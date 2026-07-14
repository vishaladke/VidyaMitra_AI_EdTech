"""AI service — full cache-first flow orchestration.

Implements the cost-optimization flow from ARCHITECTURE.md §7:
1. Exact-match Redis cache
2. Semantic pgvector cache (similarity > 0.92)
3. Pre-generated FAQ bank
4. Live Claude API call

Every path logs to ai_cost_logs.
"""
import hashlib
import json
import logging
import time
import uuid
from typing import Optional

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai import (
    AIConversation,
    AIMessage,
    AICostLog,
    AICacheSource,
    AISemanticCache,
    FAQBank,
)
from app.models.syllabus import Subject
from app.models.user import User, StudentProfile
from app.services.embedding_service import get_embedding, normalize_question
from app.services.claude_service import chat_completion, classify_topic, calculate_cost
from app.utils.safety import detect_distress, SAFETY_MESSAGE_MARATHI

logger = logging.getLogger(__name__)

# Similarity threshold for semantic cache (per ai-cost-optimization-flow.mermaid)
SEMANTIC_SIMILARITY_THRESHOLD = 0.92


async def _get_redis():
    """Get Redis client (lazy import to avoid circular deps)."""
    try:
        import redis.asyncio as aioredis
        from app.config import settings
        return aioredis.from_url(
            getattr(settings, "REDIS_URL", "redis://localhost:6379/0"),
            decode_responses=True,
        )
    except Exception as e:
        logger.warning(f"Redis unavailable: {e}")
        return None


async def _check_redis_cache(cache_key: str) -> Optional[str]:
    """Step 1: Check exact-match Redis cache."""
    redis = await _get_redis()
    if not redis:
        return None
    try:
        cached = await redis.get(f"ai:cache:{cache_key}")
        if cached:
            logger.info(f"Redis cache HIT for key {cache_key[:16]}...")
            return cached
        return None
    except Exception as e:
        logger.warning(f"Redis cache error: {e}")
        return None
    finally:
        await redis.aclose()


async def _store_redis_cache(cache_key: str, answer: str, ttl: int = 86400) -> None:
    """Store answer in Redis exact-match cache with TTL (default 24h)."""
    redis = await _get_redis()
    if not redis:
        return
    try:
        await redis.set(f"ai:cache:{cache_key}", answer, ex=ttl)
    except Exception as e:
        logger.warning(f"Redis store error: {e}")
    finally:
        await redis.aclose()


async def _check_semantic_cache(
    db: AsyncSession,
    embedding: list[float],
    grade: int,
    subject_id: Optional[uuid.UUID],
) -> Optional[str]:
    """Step 2: Check pgvector semantic cache (cosine similarity > 0.92)."""
    try:
        embedding_str = "[" + ",".join(str(x) for x in embedding) + "]"
        
        query = text("""
            SELECT id, answer, 1 - (question_embedding <=> :embedding::vector) as similarity
            FROM ai_semantic_cache
            WHERE grade = :grade
            AND (:subject_id IS NULL OR subject_id = :subject_id)
            ORDER BY question_embedding <=> :embedding::vector
            LIMIT 1
        """)
        
        result = await db.execute(
            query,
            {
                "embedding": embedding_str,
                "grade": grade,
                "subject_id": str(subject_id) if subject_id else None,
            },
        )
        row = result.first()
        
        if row and row.similarity >= SEMANTIC_SIMILARITY_THRESHOLD:
            logger.info(f"Semantic cache HIT (similarity={row.similarity:.4f})")
            # Increment hit count
            await db.execute(
                text("UPDATE ai_semantic_cache SET hit_count = hit_count + 1 WHERE id = :id"),
                {"id": str(row.id)},
            )
            await db.commit()
            return row.answer
        
        return None
    except Exception as e:
        logger.warning(f"Semantic cache error: {e}")
        return None


async def _check_faq_bank(
    db: AsyncSession,
    embedding: list[float],
    grade: int,
    subject_id: Optional[uuid.UUID],
) -> Optional[str]:
    """Step 3: Check pre-generated FAQ bank."""
    try:
        embedding_str = "[" + ",".join(str(x) for x in embedding) + "]"
        
        query = text("""
            SELECT answer, 1 - (question_embedding <=> :embedding::vector) as similarity
            FROM faq_bank
            WHERE grade = :grade
            AND (:subject_id IS NULL OR subject_id = :subject_id)
            AND is_active = true
            ORDER BY question_embedding <=> :embedding::vector
            LIMIT 1
        """)
        
        result = await db.execute(
            query,
            {
                "embedding": embedding_str,
                "grade": grade,
                "subject_id": str(subject_id) if subject_id else None,
            },
        )
        row = result.first()
        
        if row and row.similarity >= SEMANTIC_SIMILARITY_THRESHOLD:
            logger.info(f"FAQ bank HIT (similarity={row.similarity:.4f})")
            return row.answer
        
        return None
    except Exception as e:
        logger.warning(f"FAQ bank error: {e}")
        return None


async def _store_in_semantic_cache(
    db: AsyncSession,
    normalized_q: str,
    embedding: list[float],
    answer: str,
    grade: int,
    subject_id: Optional[uuid.UUID],
) -> None:
    """Store new Q&A pair in semantic cache for future similarity matches."""
    try:
        cache_entry = AISemanticCache(
            normalized_question=normalized_q,
            question_embedding=embedding,
            grade=grade,
            subject_id=subject_id,
            answer=answer,
        )
        db.add(cache_entry)
        await db.flush()
    except Exception as e:
        logger.warning(f"Semantic cache store error: {e}")


async def _log_cost(
    db: AsyncSession,
    conversation_id: uuid.UUID,
    message_id: uuid.UUID,
    student_id: uuid.UUID,
    cache_source: AICacheSource,
    model_used: Optional[str] = None,
    input_tokens: int = 0,
    output_tokens: int = 0,
    cache_hit: bool = False,
    cost_usd: float = 0.0,
    cost_inr: float = 0.0,
    response_time_ms: int = 0,
) -> None:
    """Log cost for every AI response path (cache hit or LLM call)."""
    cost_log = AICostLog(
        conversation_id=conversation_id,
        message_id=message_id,
        student_id=student_id,
        cache_source=cache_source,
        model_used=model_used,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        prompt_cache_hit=cache_hit,
        cost_usd=cost_usd,
        cost_inr=cost_inr,
        response_time_ms=response_time_ms,
    )
    db.add(cost_log)


async def process_student_message(
    db: AsyncSession,
    student_id: uuid.UUID,
    message: str,
    conversation_id: Optional[uuid.UUID] = None,
    subject_id: Optional[uuid.UUID] = None,
) -> dict:
    """Main entry point: process a student's AI Guru message through the cache-first flow.
    
    Returns dict with:
        answer, conversation_id, message_id, cache_source, cost_usd, cost_inr,
        is_flagged, response_time_ms
    """
    start_time = time.monotonic()

    # ── Safety check first ──────────────────────────────────────
    if detect_distress(message):
        # Create/get conversation
        conv = await _get_or_create_conversation(db, student_id, conversation_id, subject_id, flagged=True)
        
        # Store the student message
        student_msg = AIMessage(
            conversation_id=conv.id,
            role="student",
            content=message,
            is_voice=False,
        )
        db.add(student_msg)
        
        # Store safety response
        safety_msg = AIMessage(
            conversation_id=conv.id,
            role="assistant",
            content=SAFETY_MESSAGE_MARATHI,
            cache_source=None,
        )
        db.add(safety_msg)
        await db.flush()
        
        elapsed = int((time.monotonic() - start_time) * 1000)
        await db.commit()
        
        return {
            "answer": SAFETY_MESSAGE_MARATHI,
            "conversation_id": str(conv.id),
            "message_id": str(safety_msg.id),
            "cache_source": None,
            "cost_usd": 0.0,
            "cost_inr": 0.0,
            "is_flagged": True,
            "response_time_ms": elapsed,
        }

    # ── Get student grade for cache scoping ─────────────────────
    grade = await _get_student_grade(db, student_id)
    
    # ── Get subject info for system prompt ──────────────────────
    subject_name = ""
    subject_name_en = ""
    if subject_id:
        subject = await db.get(Subject, subject_id)
        if subject:
            subject_name = subject.name
            subject_name_en = subject.name_en or ""

    # ── Normalize question ──────────────────────────────────────
    normalized = normalize_question(message, grade, str(subject_id or "all"))
    cache_key = hashlib.sha256(normalized.encode()).hexdigest()

    # ── Step 1: Redis exact-match cache ─────────────────────────
    cached_answer = await _check_redis_cache(cache_key)
    if cached_answer:
        conv = await _get_or_create_conversation(db, student_id, conversation_id, subject_id)
        student_msg, assistant_msg = await _store_messages(
            db, conv.id, message, cached_answer, AICacheSource.EXACT_REDIS
        )
        elapsed = int((time.monotonic() - start_time) * 1000)
        await _log_cost(
            db, conv.id, assistant_msg.id, student_id,
            AICacheSource.EXACT_REDIS, response_time_ms=elapsed,
        )
        await db.commit()
        return _build_response(cached_answer, conv.id, assistant_msg.id, AICacheSource.EXACT_REDIS, elapsed)

    # ── Generate embedding for semantic search ──────────────────
    embedding = await get_embedding(normalized)

    # ── Step 2: pgvector semantic cache ─────────────────────────
    if embedding:
        semantic_answer = await _check_semantic_cache(db, embedding, grade, subject_id)
        if semantic_answer:
            conv = await _get_or_create_conversation(db, student_id, conversation_id, subject_id)
            student_msg, assistant_msg = await _store_messages(
                db, conv.id, message, semantic_answer, AICacheSource.SEMANTIC_PGVECTOR
            )
            # Also store in Redis for future exact matches
            await _store_redis_cache(cache_key, semantic_answer)
            elapsed = int((time.monotonic() - start_time) * 1000)
            await _log_cost(
                db, conv.id, assistant_msg.id, student_id,
                AICacheSource.SEMANTIC_PGVECTOR, response_time_ms=elapsed,
            )
            await db.commit()
            return _build_response(semantic_answer, conv.id, assistant_msg.id, AICacheSource.SEMANTIC_PGVECTOR, elapsed)

    # ── Step 3: FAQ bank ────────────────────────────────────────
    if embedding:
        faq_answer = await _check_faq_bank(db, embedding, grade, subject_id)
        if faq_answer:
            conv = await _get_or_create_conversation(db, student_id, conversation_id, subject_id)
            student_msg, assistant_msg = await _store_messages(
                db, conv.id, message, faq_answer, AICacheSource.FAQ_BANK
            )
            await _store_redis_cache(cache_key, faq_answer)
            elapsed = int((time.monotonic() - start_time) * 1000)
            await _log_cost(
                db, conv.id, assistant_msg.id, student_id,
                AICacheSource.FAQ_BANK, response_time_ms=elapsed,
            )
            await db.commit()
            return _build_response(faq_answer, conv.id, assistant_msg.id, AICacheSource.FAQ_BANK, elapsed)

    # ── Step 4: Live Claude API call ────────────────────────────
    conv = await _get_or_create_conversation(db, student_id, conversation_id, subject_id)
    
    # Build conversation history for context
    history = await _get_conversation_history(db, conv.id, limit=10)
    history.append({"role": "user", "content": message})

    llm_result = await chat_completion(
        messages=history,
        grade=grade,
        subject_name=subject_name,
        subject_name_en=subject_name_en,
    )

    answer = llm_result["content"]
    
    # Store messages
    topic_tag = await classify_topic(message, answer)
    student_msg, assistant_msg = await _store_messages(
        db, conv.id, message, answer, AICacheSource.LIVE_LLM, topic_tag=topic_tag
    )

    # Store in caches for future lookups
    await _store_redis_cache(cache_key, answer)
    if embedding:
        await _store_in_semantic_cache(db, normalized, embedding, answer, grade, subject_id)

    elapsed = int((time.monotonic() - start_time) * 1000)
    await _log_cost(
        db, conv.id, assistant_msg.id, student_id,
        AICacheSource.LIVE_LLM,
        model_used=llm_result["model"],
        input_tokens=llm_result["input_tokens"],
        output_tokens=llm_result["output_tokens"],
        cache_hit=llm_result["cache_hit"],
        cost_usd=llm_result["cost_usd"],
        cost_inr=llm_result["cost_inr"],
        response_time_ms=elapsed,
    )
    await db.commit()

    return _build_response(answer, conv.id, assistant_msg.id, AICacheSource.LIVE_LLM, elapsed,
                          cost_usd=llm_result["cost_usd"], cost_inr=llm_result["cost_inr"])


# ── Helper functions ────────────────────────────────────────────

async def _get_student_grade(db: AsyncSession, student_id: uuid.UUID) -> int:
    """Get student's grade from profile, default to 7."""
    result = await db.execute(
        select(StudentProfile.grade).where(StudentProfile.user_id == student_id)
    )
    row = result.scalar_one_or_none()
    return row or 7


async def _get_or_create_conversation(
    db: AsyncSession,
    student_id: uuid.UUID,
    conversation_id: Optional[uuid.UUID],
    subject_id: Optional[uuid.UUID],
    flagged: bool = False,
) -> AIConversation:
    """Get existing conversation or create a new one."""
    if conversation_id:
        conv = await db.get(AIConversation, conversation_id)
        if conv and conv.student_id == student_id:
            if flagged:
                conv.is_flagged = True
                conv.flag_reason = "Distress signal detected"
            return conv

    conv = AIConversation(
        student_id=student_id,
        subject_id=subject_id,
        is_flagged=flagged,
        flag_reason="Distress signal detected" if flagged else None,
    )
    db.add(conv)
    await db.flush()
    return conv


async def _store_messages(
    db: AsyncSession,
    conversation_id: uuid.UUID,
    student_message: str,
    assistant_answer: str,
    cache_source: AICacheSource,
    topic_tag: Optional[str] = None,
) -> tuple[AIMessage, AIMessage]:
    """Store both student and assistant messages."""
    student_msg = AIMessage(
        conversation_id=conversation_id,
        role="student",
        content=student_message,
    )
    db.add(student_msg)

    assistant_msg = AIMessage(
        conversation_id=conversation_id,
        role="assistant",
        content=assistant_answer,
        cache_source=cache_source,
        topic_tag=topic_tag,
    )
    db.add(assistant_msg)
    await db.flush()

    return student_msg, assistant_msg


async def _get_conversation_history(
    db: AsyncSession,
    conversation_id: uuid.UUID,
    limit: int = 10,
) -> list[dict]:
    """Get recent conversation messages formatted for Claude API."""
    result = await db.execute(
        select(AIMessage)
        .where(AIMessage.conversation_id == conversation_id)
        .order_by(AIMessage.created_at.desc())
        .limit(limit)
    )
    messages = list(reversed(result.scalars().all()))
    
    history = []
    for msg in messages:
        role = "user" if msg.role == "student" else "assistant"
        history.append({"role": role, "content": msg.content})
    
    return history


def _build_response(
    answer: str,
    conversation_id: uuid.UUID,
    message_id: uuid.UUID,
    cache_source: AICacheSource,
    response_time_ms: int,
    cost_usd: float = 0.0,
    cost_inr: float = 0.0,
) -> dict:
    return {
        "answer": answer,
        "conversation_id": str(conversation_id),
        "message_id": str(message_id),
        "cache_source": cache_source.value,
        "cost_usd": cost_usd,
        "cost_inr": cost_inr,
        "is_flagged": False,
        "response_time_ms": response_time_ms,
    }


async def get_student_conversations(
    db: AsyncSession,
    student_id: uuid.UUID,
    limit: int = 20,
    offset: int = 0,
) -> list[AIConversation]:
    """List a student's AI conversations."""
    result = await db.execute(
        select(AIConversation)
        .where(AIConversation.student_id == student_id)
        .order_by(AIConversation.updated_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(result.scalars().all())


async def get_conversation_messages(
    db: AsyncSession,
    conversation_id: uuid.UUID,
    student_id: uuid.UUID,
) -> list[AIMessage]:
    """Get all messages in a conversation (with ownership check)."""
    # Verify ownership
    conv = await db.get(AIConversation, conversation_id)
    if not conv or conv.student_id != student_id:
        return []
    
    result = await db.execute(
        select(AIMessage)
        .where(AIMessage.conversation_id == conversation_id)
        .order_by(AIMessage.created_at.asc())
    )
    return list(result.scalars().all())
