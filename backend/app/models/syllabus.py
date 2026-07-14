"""Subject and syllabus unit (chapter/topic tree) models."""
import uuid
from typing import Optional

from sqlalchemy import Boolean, ForeignKey, SmallInteger, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Subject(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "subjects"

    name: Mapped[str] = mapped_column(String(100), nullable=False)  # Marathi name e.g. "गणित"
    name_en: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # English for admin
    grade: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    board: Mapped[str] = mapped_column(String(50), default="maharashtra_state", nullable=False)
    icon_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    display_order: Mapped[int] = mapped_column(SmallInteger, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    __table_args__ = (
        UniqueConstraint("name", "grade", "board", name="uq_subject_name_grade_board"),
    )


class SyllabusUnit(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Self-referential tree: subject → chapter → topic → subtopic.
    Versioned, with is_active flag for content management."""
    __tablename__ = "syllabus_units"

    subject_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    parent_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("syllabus_units.id", ondelete="CASCADE"), nullable=True, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)  # Marathi
    title_en: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # English for admin
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    unit_type: Mapped[str] = mapped_column(String(20), default="chapter", nullable=False)  # chapter|topic|subtopic
    display_order: Mapped[int] = mapped_column(SmallInteger, default=0)
    version: Mapped[int] = mapped_column(SmallInteger, default=1, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    pdf_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # R2 URL
