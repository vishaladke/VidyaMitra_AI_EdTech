"""Notification service — full notification orchestrator.

Handles the complete notification flow:
1. Provider factory (mock or whatsapp based on NOTIFICATION_PROVIDER)
2. Send + log to NotificationLog table
3. WhatsApp report formatting + delivery
4. Batch weekly report delivery
5. Delivery status updates (from webhook callbacks)
6. Notification history per user

Per ARCHITECTURE.md §11: WhatsApp is primary, abstracted behind
NotificationChannelProvider so email/SMS/push can be added later.
"""
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, and_, desc, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.notification import NotificationChannel, NotificationLog
from app.models.user import User, UserRole, ParentProfile, ParentStudentLink
from app.providers.notification.base import NotificationChannelProvider
from app.providers.notification.mock import MockNotificationProvider
from app.providers.notification.whatsapp import WhatsAppProvider

logger = logging.getLogger(__name__)


# ── Provider Factory ──────────────────────────────────────────────

def get_notification_provider(channel: str = "whatsapp") -> NotificationChannelProvider:
    """Factory: select notification provider based on config.

    In local/pilot with NOTIFICATION_PROVIDER=mock, all channels use MockProvider.
    In production with NOTIFICATION_PROVIDER=whatsapp, WhatsApp uses the real BSP.
    """
    notification_provider = getattr(settings, "NOTIFICATION_PROVIDER", "mock")

    if notification_provider == "mock":
        return MockNotificationProvider()

    if channel == "whatsapp":
        return WhatsAppProvider()

    # Default fallback to mock for unimplemented channels
    return MockNotificationProvider()


# ── Send Notification ─────────────────────────────────────────────

async def send_notification(
    db: AsyncSession,
    user_id: uuid.UUID,
    channel: NotificationChannel,
    template_name: str,
    params: Optional[dict] = None,
    recipient_phone: Optional[str] = None,
) -> dict:
    """Send a notification and log it.

    Args:
        db: Database session
        user_id: Target user ID
        channel: Notification channel (whatsapp, email, sms, push)
        template_name: Template identifier
        params: Template parameter values
        recipient_phone: Override phone number (default: user's phone)

    Returns:
        dict with message_id, status
    """
    # Get recipient phone if not provided
    if not recipient_phone:
        result = await db.execute(select(User.phone).where(User.id == user_id))
        phone = result.scalar_one_or_none()
        if not phone:
            logger.warning(f"⚠️ Cannot send notification: user {user_id} not found")
            return {"status": "failed", "error": "user_not_found"}
        recipient_phone = phone

    # Get provider and send
    provider = get_notification_provider(channel.value)
    provider_msg_id = await provider.send(
        to=recipient_phone,
        template_name=template_name,
        params=params,
    )

    # Build content preview
    content_preview = None
    if params:
        content_preview = str(params)[:200]

    # Log to database
    log_entry = NotificationLog(
        user_id=user_id,
        channel=channel,
        template_name=template_name,
        content_preview=content_preview,
        status="sent",
        provider_message_id=provider_msg_id,
        metadata_json={"params": params} if params else {},
    )
    db.add(log_entry)
    await db.commit()
    await db.refresh(log_entry)

    logger.info(f"📤 Notification sent: {channel.value} to user {user_id}, msg_id={provider_msg_id}")

    return {
        "status": "sent",
        "message_id": provider_msg_id,
        "log_id": str(log_entry.id),
    }


# ── WhatsApp Weekly Report ────────────────────────────────────────

async def send_whatsapp_report(
    db: AsyncSession,
    parent_id: uuid.UUID,
    report: dict,
) -> dict:
    """Send a weekly student report to a parent via WhatsApp.

    Uses the Marathi summary text from the report as the template body.
    """
    # Extract template params from the report
    params = format_whatsapp_template_params(report)

    return await send_notification(
        db=db,
        user_id=parent_id,
        channel=NotificationChannel.WHATSAPP,
        template_name="weekly_student_report",
        params=params,
    )


def format_whatsapp_template_params(report: dict) -> dict:
    """Extract WhatsApp template variable values from a student report.

    Maps report data to the BSP-registered template variables.
    The template should have variables like:
    {{1}} = student name, {{2}} = grade, {{3}} = summary text
    """
    student = report.get("student", {})
    ai = report.get("ai_activity", {})
    attendance = report.get("attendance", {})
    tests = report.get("tests", {})

    return {
        "student_name": student.get("full_name", "विद्यार्थी"),
        "grade": str(student.get("grade", "")),
        "conversations": str(ai.get("conversations", 0)),
        "active_days": str(ai.get("active_days", 0)),
        "attendance_pct": str(attendance.get("percentage", "N/A")),
        "avg_score": str(tests.get("average_score", "N/A")),
        "summary_mr": report.get("summary_mr", ""),
    }


# ── Batch Weekly Reports ─────────────────────────────────────────

async def send_weekly_reports_batch(
    db: AsyncSession,
    reports: list[dict],
) -> dict:
    """Send weekly reports to all parents with WhatsApp enabled.

    For each report, find the parent(s) linked to the student,
    check their notification preferences, and send if WhatsApp is enabled.

    Returns summary of sent/skipped/failed counts.
    """
    sent = 0
    skipped = 0
    failed = 0

    for report in reports:
        student_id = report.get("student", {}).get("id")
        if not student_id:
            skipped += 1
            continue

        # Find parent(s) linked to this student
        parent_links = await db.execute(
            select(ParentStudentLink.parent_id).where(
                ParentStudentLink.student_id == uuid.UUID(student_id)
            )
        )
        parent_ids = [row[0] for row in parent_links.all()]

        if not parent_ids:
            skipped += 1
            continue

        for parent_id in parent_ids:
            # Check notification preferences
            pref_result = await db.execute(
                select(ParentProfile.notification_preferences).where(
                    ParentProfile.user_id == parent_id
                )
            )
            prefs = pref_result.scalar_one_or_none()

            if not prefs or not prefs.get("whatsapp", True):
                skipped += 1
                continue

            try:
                await send_whatsapp_report(db, parent_id, report)
                sent += 1
            except Exception as e:
                logger.error(f"❌ Failed to send report to parent {parent_id}: {e}")
                failed += 1

    summary = {"sent": sent, "skipped": skipped, "failed": failed, "total": len(reports)}
    logger.info(f"📊 Batch report delivery: {summary}")
    return summary


# ── Delivery Status Updates ───────────────────────────────────────

async def update_delivery_status(
    db: AsyncSession,
    provider_message_id: str,
    status: str,
    timestamp: Optional[str] = None,
) -> bool:
    """Update notification log when we receive a delivery/read receipt.

    Called by the webhook router when WhatsApp sends status updates.
    """
    result = await db.execute(
        select(NotificationLog).where(
            NotificationLog.provider_message_id == provider_message_id
        )
    )
    log_entry = result.scalar_one_or_none()

    if not log_entry:
        logger.warning(f"⚠️ Delivery status update: no log for message {provider_message_id}")
        return False

    log_entry.status = status
    if timestamp:
        log_entry.metadata_json = {
            **(log_entry.metadata_json or {}),
            f"{status}_at": timestamp,
        }

    await db.commit()
    logger.info(f"📬 Delivery status updated: {provider_message_id} → {status}")
    return True


# ── Notification History ──────────────────────────────────────────

async def get_notification_history(
    db: AsyncSession,
    user_id: uuid.UUID,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    """Get notification delivery log for a user."""
    total = await db.scalar(
        select(func.count())
        .select_from(NotificationLog)
        .where(NotificationLog.user_id == user_id)
    )

    offset = (page - 1) * page_size
    result = await db.execute(
        select(NotificationLog)
        .where(NotificationLog.user_id == user_id)
        .order_by(NotificationLog.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    logs = result.scalars().all()

    return {
        "notifications": [
            {
                "id": str(log.id),
                "channel": log.channel.value,
                "template_name": log.template_name,
                "content_preview": log.content_preview,
                "status": log.status,
                "created_at": log.created_at.isoformat(),
                "metadata": log.metadata_json,
            }
            for log in logs
        ],
        "total": total or 0,
    }
