"""CMS content, ad slots (DPDP-compliant), and audit log models."""
import enum
import uuid
from datetime import date, datetime
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Integer, SmallInteger, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class ContentStatus(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class HomepageContent(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "homepage_content"

    section: Mapped[str] = mapped_column(String(50), nullable=False)  # hero, features, pricing, about
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    media_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    display_order: Mapped[int] = mapped_column(SmallInteger, default=0)
    status: Mapped[ContentStatus] = mapped_column(
        Enum(ContentStatus, name="content_status"), default=ContentStatus.DRAFT
    )
    language: Mapped[str] = mapped_column(String(10), default="mr")  # mr = Marathi, en = English
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )


class AdSlot(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Ad slots — DPDP Act compliance: NO ads on student-facing screens.
    Placement must be parent/teacher/admin-facing only.
    No behavioral targeting using student activity data."""
    __tablename__ = "ad_slots"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    placement: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g. 'parent_dashboard_sidebar'
    content_html: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    target_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    impressions: Mapped[int] = mapped_column(Integer, default=0)
    clicks: Mapped[int] = mapped_column(Integer, default=0)
    start_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )


class AuditLog(Base, UUIDPrimaryKeyMixin):
    """Every Admin/Super Admin action is logged here."""
    __tablename__ = "audit_logs"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)  # e.g. 'user.create'
    resource_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    resource_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    details: Mapped[Optional[dict]] = mapped_column(JSONB, default={})
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
