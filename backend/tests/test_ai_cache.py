"""AI cache decision logic tests — cache-first flow unit tests.

Tests the cache-first flow components:
1. Question normalization for cache key generation
2. Safety/distress signal detection
3. Cache source enum values

These are unit tests that don't require a running database.
"""
import hashlib
import uuid

import pytest

from app.models.ai import AICacheSource
from app.services.embedding_service import normalize_question
from app.utils.safety import check_distress, check_distress_signals, get_safety_response


# ── Normalization Tests ───────────────────────────────────────

class TestQuestionNormalization:
    """Test that question normalization works correctly for cache key generation."""

    def test_normalize_strips_whitespace(self):
        """Extra whitespace should be collapsed."""
        q1 = normalize_question("What  is  photosynthesis?", grade=7, subject_id="none")
        q2 = normalize_question("What is photosynthesis?", grade=7, subject_id="none")
        assert q1 == q2

    def test_normalize_lowercases(self):
        """Questions should be case-insensitive for caching."""
        q1 = normalize_question("What Is Photosynthesis?", grade=7, subject_id="none")
        q2 = normalize_question("what is photosynthesis?", grade=7, subject_id="none")
        assert q1 == q2

    def test_normalize_strips_punctuation(self):
        """Terminal punctuation should not change cache key."""
        q1 = normalize_question("what is photosynthesis", grade=7, subject_id="none")
        q2 = normalize_question("what is photosynthesis??", grade=7, subject_id="none")
        assert q1 == q2

    def test_normalize_includes_grade_prefix(self):
        """Same question for different grades should produce different cache keys."""
        q7 = normalize_question("what is force", grade=7, subject_id="none")
        q8 = normalize_question("what is force", grade=8, subject_id="none")
        assert q7 != q8
        assert q7.startswith("g7:")
        assert q8.startswith("g8:")

    def test_normalize_includes_subject_prefix(self):
        """Same question for different subjects should produce different cache keys."""
        sid1 = str(uuid.uuid4())
        sid2 = str(uuid.uuid4())
        q1 = normalize_question("explain this", grade=7, subject_id=sid1)
        q2 = normalize_question("explain this", grade=7, subject_id=sid2)
        assert q1 != q2

    def test_normalize_handles_devanagari(self):
        """Marathi/Devanagari text should normalize correctly."""
        q = normalize_question("  प्रकाश   संश्लेषण   म्हणजे  काय?  ", grade=7, subject_id="none")
        assert "  " not in q  # no double spaces
        assert q.startswith("g7:")

    def test_normalize_deterministic(self):
        """Same input should always produce the same output."""
        q1 = normalize_question("what is gravity", grade=8, subject_id="abc")
        q2 = normalize_question("what is gravity", grade=8, subject_id="abc")
        assert q1 == q2


# ── Safety Detection Tests ────────────────────────────────────

class TestSafetyDetection:
    """Test that distress signals are properly detected."""

    def test_detects_english_distress(self):
        """English distress signals should be detected."""
        result = check_distress("I want to kill myself")
        assert result is not None  # returns a reason string

    def test_detects_marathi_distress(self):
        """Marathi distress signals should be detected."""
        result = check_distress("मला आत्महत्या करायची आहे")
        assert result is not None

    def test_normal_question_not_flagged(self):
        """Normal academic questions should NOT be flagged."""
        result = check_distress("What is photosynthesis?")
        assert result is None

    def test_math_question_not_flagged(self):
        """Math questions should not trigger false positives."""
        result = check_distress("How to solve quadratic equations?")
        assert result is None

    def test_check_distress_signals_wrapper(self):
        """check_distress_signals should return a dict with is_distress."""
        result = check_distress_signals("I want to kill myself")
        assert result["is_distress"] is True
        assert result["reason"] is not None

    def test_check_distress_signals_safe(self):
        """check_distress_signals should return False for safe messages."""
        result = check_distress_signals("What is photosynthesis?")
        assert result["is_distress"] is False

    def test_safety_response_has_childline(self):
        """Safety response should include Childline 1098."""
        response = get_safety_response("mr")
        assert "1098" in response

    def test_safety_response_english(self):
        """English safety response should also include Childline 1098."""
        response = get_safety_response("en")
        assert "1098" in response


# ── Cache Source Enum Tests ───────────────────────────────────

class TestCacheSourceEnum:
    """Test that cache source enum values are correct."""

    def test_cache_sources_exist(self):
        assert AICacheSource.EXACT_REDIS == "exact_redis"
        assert AICacheSource.SEMANTIC_PGVECTOR == "semantic_pgvector"
        assert AICacheSource.FAQ_BANK == "faq_bank"
        assert AICacheSource.LIVE_LLM == "live_llm"

    def test_cache_sources_are_strings(self):
        """Cache sources should be usable as strings."""
        for source in AICacheSource:
            assert isinstance(source.value, str)
