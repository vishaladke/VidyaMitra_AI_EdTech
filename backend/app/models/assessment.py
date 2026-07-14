"""Assignment, question, and test attempt models."""
import enum
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Numeric, SmallInteger, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class AssignmentType(str, enum.Enum):
    HOMEWORK = "homework"
    TEST = "test"
    PRACTICE = "practice"


class QuestionType(str, enum.Enum):
    MCQ = "mcq"
    SHORT_ANSWER = "short_answer"
    LONG_ANSWER = "long_answer"
    TRUE_FALSE = "true_false"


class DifficultyLevel(str, enum.Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class Assignment(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "assignments"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    assignment_type: Mapped[AssignmentType] = mapped_column(
        Enum(AssignmentType, name="assignment_type"), default=AssignmentType.HOMEWORK, nullable=False
    )
    subject_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False
    )
    syllabus_unit_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("syllabus_units.id", ondelete="SET NULL"), nullable=True
    )
    class_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("classes.id", ondelete="SET NULL"), nullable=True
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    due_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    max_score: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class Question(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "questions"

    assignment_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("assignments.id", ondelete="CASCADE"), nullable=True
    )
    syllabus_unit_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("syllabus_units.id", ondelete="SET NULL"), nullable=True
    )
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    question_type: Mapped[QuestionType] = mapped_column(
        Enum(QuestionType, name="question_type"), default=QuestionType.MCQ, nullable=False
    )
    options: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)  # MCQ: {"a": "...", "b": "..."}
    correct_answer: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    marks: Mapped[float] = mapped_column(Numeric(4, 2), default=1.0, nullable=False)
    difficulty: Mapped[Optional[DifficultyLevel]] = mapped_column(
        Enum(DifficultyLevel, name="difficulty_level"), default=DifficultyLevel.MEDIUM
    )
    display_order: Mapped[int] = mapped_column(SmallInteger, default=0)


class TestAttempt(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "test_attempts"

    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    assignment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("assignments.id", ondelete="CASCADE"), nullable=False
    )
    answers: Mapped[dict] = mapped_column(JSONB, default={}, nullable=False)
    score: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    max_score: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    percentage: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    is_graded: Mapped[bool] = mapped_column(Boolean, default=False)
    graded_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
