"""Embedding service — wraps OpenAI text-embedding-3-small for pgvector semantic cache.

This is the only place in the codebase that calls the embedding API.
Dimension: 1536 (matches ai_semantic_cache.question_embedding and faq_bank.question_embedding columns).
"""
import hashlib
import logging
from typing import Optional

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

# Cache embeddings in-process to avoid redundant API calls within the same request
_embedding_cache: dict[str, list[float]] = {}
_MAX_CACHE_SIZE = 500


def _cache_key(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


async def get_embedding(text: str) -> Optional[list[float]]:
    """Generate a 1536-dim embedding vector for the given text.
    
    Returns None if the API call fails (allows graceful degradation — 
    the cache-first flow will skip the semantic cache step).
    """
    key = _cache_key(text)
    if key in _embedding_cache:
        return _embedding_cache[key]

    api_key = getattr(settings, "OPENAI_API_KEY", None)
    if not api_key:
        logger.warning("OPENAI_API_KEY not set — skipping embedding generation")
        return None

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                "https://api.openai.com/v1/embeddings",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": getattr(settings, "EMBEDDING_MODEL", "text-embedding-3-small"),
                    "input": text,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            embedding = data["data"][0]["embedding"]

            # Cache it (evict oldest if full)
            if len(_embedding_cache) >= _MAX_CACHE_SIZE:
                oldest_key = next(iter(_embedding_cache))
                del _embedding_cache[oldest_key]
            _embedding_cache[key] = embedding

            return embedding

    except Exception as e:
        logger.error(f"Embedding API error: {e}")
        return None


def normalize_question(question: str, grade: int, subject_id: str) -> str:
    """Normalize a student question for cache lookup.
    
    Produces a deterministic string key:
    - Lowercase
    - Strip extra whitespace
    - Prefix with grade and subject for scoping
    """
    import re
    # Collapse whitespace (handles Devanagari + Latin)
    cleaned = re.sub(r"\s+", " ", question.strip().lower())
    # Remove trailing punctuation for matching
    cleaned = re.sub(r"[?!।\.\s]+$", "", cleaned)
    return f"g{grade}:s{subject_id}:{cleaned}"
