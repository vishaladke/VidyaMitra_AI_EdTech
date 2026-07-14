"""School, class, and section models — stubbed per ARCHITECTURE.md §5."""
import uuid
from typing import Optional

from sqlalchemy import Boolean, ForeignKey, SmallInteger, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class School(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Stubbed — no UI until a school signs a data-sharing agreement."""
    __tablename__ = "schools"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    city: Mapped[str] = mapped_column(String(100), default="Solapur")
    board: Mapped[str] = mapped_column(String(50), default="maharashtra_state")
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    contact_phone: Mapped[Optional[str]] = mapped_column(String(15), nullable=True)
    contact_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class Class(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "classes"

    school_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id", ondelete="SET NULL"), nullable=True
    )
    grade: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    name: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    academic_year: Mapped[str] = mapped_column(String(10), default="2026-27", nullable=False)


class Section(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "sections"

    class_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("classes.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(10), default="A", nullable=False)
    teacher_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )


class TeacherClassAssignment(Base, UUIDPrimaryKeyMixin):
    """Teacher-to-class assignment (many-to-many)."""
    __tablename__ = "teacher_class_assignments"

    teacher_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    class_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("classes.id", ondelete="CASCADE"), nullable=False
    )
    subject_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("subjects.id", ondelete="SET NULL"), nullable=True
    )
