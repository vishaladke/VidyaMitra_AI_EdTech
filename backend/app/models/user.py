"""User, profile, and parent-student link models."""
import enum
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, SmallInteger, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class UserRole(str, enum.Enum):
    STUDENT = "student"
    TEACHER = "teacher"
    PARENT = "parent"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"


class GenderEnum(str, enum.Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class User(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "users"

    phone: Mapped[str] = mapped_column(String(15), unique=True, nullable=False, index=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=True)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole, name="user_role", values_callable=lambda x: [e.value for e in x]), nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Super Admin TOTP fields
    totp_secret: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    totp_verified: Mapped[bool] = mapped_column(Boolean, default=False)

    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    student_profile: Mapped[Optional["StudentProfile"]] = relationship(back_populates="user", uselist=False)
    teacher_profile: Mapped[Optional["TeacherProfile"]] = relationship(back_populates="user", uselist=False)
    parent_profile: Mapped[Optional["ParentProfile"]] = relationship(back_populates="user", uselist=False)


class StudentProfile(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "student_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    grade: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    board: Mapped[str] = mapped_column(String(50), default="maharashtra_state", nullable=False)
    medium: Mapped[str] = mapped_column(String(20), default="marathi", nullable=False)
    school_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id", ondelete="SET NULL"), nullable=True
    )
    section_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sections.id", ondelete="SET NULL"), nullable=True
    )
    date_of_birth: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    gender: Mapped[Optional[GenderEnum]] = mapped_column(Enum(GenderEnum, name="gender_enum", values_callable=lambda x: [e.value for e in x]), nullable=True)
    city: Mapped[str] = mapped_column(String(100), default="Solapur")
    streak_days: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)

    user: Mapped["User"] = relationship(back_populates="student_profile")


class TeacherProfile(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "teacher_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    school_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id", ondelete="SET NULL"), nullable=True
    )
    qualification: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    subjects: Mapped[Optional[list[str]]] = mapped_column(ARRAY(Text), nullable=True)

    user: Mapped["User"] = relationship(back_populates="teacher_profile")


class ParentProfile(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "parent_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    city: Mapped[str] = mapped_column(String(100), default="Solapur")
    notification_preferences: Mapped[Optional[dict]] = mapped_column(
        JSONB, default={"whatsapp": True, "email": False}
    )

    user: Mapped["User"] = relationship(back_populates="parent_profile")


class ParentStudentLink(Base, UUIDPrimaryKeyMixin):
    """Many-to-many: one parent can have multiple children,
    and (less commonly) a student could have multiple guardians."""
    __tablename__ = "parent_student_links"

    parent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    relationship_type: Mapped[str] = mapped_column(String(50), default="parent")
    is_primary: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        # One link per parent-student pair
        {"comment": "Many-to-many parent-student relationships"},
    )
