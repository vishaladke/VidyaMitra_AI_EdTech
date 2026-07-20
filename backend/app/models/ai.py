"""AI conversation, message, cost tracking, semantic cache, and FAQ bank models."""
import enum
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, Numeric, SmallInteger, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from pgvector.sqlalchemy import Vector

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class AICacheSource(str, enum.Enum):
    EXACT_REDIS = "exact_redis"
    SEMANTIC_PGVECTOR = "semantic_pgvector"
    FAQ_BANK = "faq_bank"
    LIVE_LLM = "live_llm"


class AIConversation(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "ai_conversations"

    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    subject_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("subjects.id", ondelete="SET NULL"), nullable=True
    )
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Safety: distress signal flagging
    is_flagged: Mapped[bool] = mapped_column(Boolean, default=False)
    flag_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reviewed_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class AIMessage(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "ai_messages"

    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ai_conversations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role: Mapped[str] = mapped_column(String(10), nullable=False)  # 'student' or 'assistant'
    content: Mapped[str] = mapped_column(Text, nullable=False)
    topic_tag: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # cheap classifier
    is_voice: Mapped[bool] = mapped_column(Boolean, default=False)
    audio_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # R2 URL
    cache_source: Mapped[Optional[AICacheSource]] = mapped_column(
        Enum(AICacheSource, name="ai_cache_source", values_callable=lambda x: [e.value for e in x]), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class AICostLog(Base, UUIDPrimaryKeyMixin):
    """Every AI response path logs here — cache hit or live LLM call.
    Powers the Super Admin AI-cost dashboard."""
    __tablename__ = "ai_cost_logs"

    conversation_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ai_conversations.id", ondelete="SET NULL"), nullable=True
    )
    message_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ai_messages.id", ondelete="SET NULL"), nullable=True
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    cache_source: Mapped[AICacheSource] = mapped_column(
        Enum(AICacheSource, name="ai_cache_source", values_callable=lambda x: [e.value for e in x], create_type=False), nullable=False
    )
    model_used: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    prompt_cache_hit: Mapped[bool] = mapped_column(Boolean, default=False)
    cost_usd: Mapped[float] = mapped_column(Numeric(10, 6), default=0)
    cost_inr: Mapped[float] = mapped_column(Numeric(10, 4), default=0)
    response_time_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )


class AISemanticCache(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """pgvector semantic cache — catches paraphrased repeats (similarity > 0.92)."""
    __tablename__ = "ai_semantic_cache"

    normalized_question: Mapped[str] = mapped_column(Text, nullable=False)
    question_embedding = mapped_column(Vector(1536))  # OpenAI text-embedding-3-small
    grade: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    subject_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("subjects.id", ondelete="CASCADE"), nullable=True
    )
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    hit_count: Mapped[int] = mapped_column(Integer, default=0)


class FAQBank(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Pre-generated FAQ bank — batch-processed from syllabus before launch.
    Checked in cache-first flow after semantic cache miss."""
    __tablename__ = "faq_bank"

    question: Mapped[str] = mapped_column(Text, nullable=False)
    question_embedding = mapped_column(Vector(1536))
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    grade: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    subject_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False
    )
    syllabus_unit_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("syllabus_units.id", ondelete="SET NULL"), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
