"""Super Admin service — AI cost dashboard, chat audit, master data, CMS.

Highest privilege level: full platform oversight. All data accessible.
"""
import uuid
import logging
from datetime import date, timedelta
from typing import Optional

from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole
from app.models.ai import AIConversation, AIMessage, AICostLog, AICacheSource
from app.models.syllabus import Subject
from app.models.content import HomepageContent, ContentStatus, AuditLog

logger = logging.getLogger(__name__)


# ── Dashboard Stats ──────────────────────────────────────────

async def get_superadmin_dashboard_stats(db: AsyncSession) -> dict:
    """Get super admin overview: users, AI costs, cache performance."""
    total_users = await db.scalar(select(func.count()).select_from(User))
    active_users = await db.scalar(
        select(func.count()).select_from(User).where(User.is_active == True)
    )

    # AI cost totals
    total_cost_inr = await db.scalar(
        select(func.sum(AICostLog.cost_inr))
    )
    total_cost_usd = await db.scalar(
        select(func.sum(AICostLog.cost_usd))
    )

    # Cache hit rate
    total_requests = await db.scalar(
        select(func.count()).select_from(AICostLog)
    )
    cache_hits = await db.scalar(
        select(func.count()).select_from(AICostLog).where(
            AICostLog.cache_source != AICacheSource.LIVE_LLM
        )
    )
    cache_hit_rate = round((cache_hits / total_requests * 100), 1) if total_requests else 0

    # Total conversations
    total_conversations = await db.scalar(
        select(func.count()).select_from(AIConversation)
    )

    # Flagged conversations
    flagged = await db.scalar(
        select(func.count()).select_from(AIConversation).where(
            AIConversation.is_flagged == True
        )
    )

    return {
        "total_users": total_users or 0,
        "active_users": active_users or 0,
        "total_cost_inr": float(total_cost_inr or 0),
        "total_cost_usd": float(total_cost_usd or 0),
        "cache_hit_rate": cache_hit_rate,
        "total_conversations": total_conversations or 0,
        "flagged_conversations": flagged or 0,
        "total_ai_requests": total_requests or 0,
    }


# ── AI Cost Dashboard ────────────────────────────────────────

async def get_ai_cost_dashboard(
    db: AsyncSession,
    days: int = 30,
) -> dict:
    """AI cost dashboard with breakdown by source, per-user costs, daily trends."""
    since = date.today() - timedelta(days=days)

    # Cost by cache source
    source_result = await db.execute(
        select(
            AICostLog.cache_source,
            func.count().label("count"),
            func.sum(AICostLog.cost_inr).label("total_inr"),
            func.sum(AICostLog.input_tokens).label("total_input"),
            func.sum(AICostLog.output_tokens).label("total_output"),
        )
        .where(func.date(AICostLog.created_at) >= since)
        .group_by(AICostLog.cache_source)
    )
    by_source = [
        {
            "source": row[0].value if row[0] else "unknown",
            "count": row[1],
            "cost_inr": float(row[2] or 0),
            "input_tokens": row[3] or 0,
            "output_tokens": row[4] or 0,
        }
        for row in source_result.all()
    ]

    # Per-user costs (top 10)
    user_result = await db.execute(
        select(
            AICostLog.student_id,
            User.full_name,
            func.count().label("requests"),
            func.sum(AICostLog.cost_inr).label("total_inr"),
        )
        .join(User, User.id == AICostLog.student_id)
        .where(func.date(AICostLog.created_at) >= since)
        .group_by(AICostLog.student_id, User.full_name)
        .order_by(func.sum(AICostLog.cost_inr).desc())
        .limit(10)
    )
    per_user = [
        {
            "student_id": str(row[0]),
            "student_name": row[1],
            "requests": row[2],
            "cost_inr": float(row[3] or 0),
        }
        for row in user_result.all()
    ]

    # Daily cost trend
    daily_result = await db.execute(
        select(
            func.date(AICostLog.created_at).label("day"),
            func.count().label("requests"),
            func.sum(AICostLog.cost_inr).label("cost_inr"),
        )
        .where(func.date(AICostLog.created_at) >= since)
        .group_by(func.date(AICostLog.created_at))
        .order_by(func.date(AICostLog.created_at))
    )
    daily = [
        {"date": str(row[0]), "requests": row[1], "cost_inr": float(row[2] or 0)}
        for row in daily_result.all()
    ]

    # Totals
    total_inr = sum(s["cost_inr"] for s in by_source)
    total_requests = sum(s["count"] for s in by_source)
    cache_hits = sum(s["count"] for s in by_source if s["source"] != "live_llm")
    cache_rate = round((cache_hits / total_requests * 100), 1) if total_requests else 0

    return {
        "period_days": days,
        "total_cost_inr": total_inr,
        "total_requests": total_requests,
        "cache_hit_rate": cache_rate,
        "by_source": by_source,
        "per_user": per_user,
        "daily_trend": daily,
    }


# ── Chat Audit ────────────────────────────────────────────────

async def get_chat_audit(
    db: AsyncSession,
    search: Optional[str] = None,
    flagged_only: bool = False,
    student_id: Optional[uuid.UUID] = None,
    limit: int = 50,
    offset: int = 0,
) -> dict:
    """Full AI conversation audit log with search and filters."""
    query = (
        select(AIConversation, User.full_name)
        .join(User, User.id == AIConversation.student_id)
        .order_by(AIConversation.created_at.desc())
    )

    if flagged_only:
        query = query.where(AIConversation.is_flagged == True)
    if student_id:
        query = query.where(AIConversation.student_id == student_id)
    if search:
        query = query.where(
            or_(
                AIConversation.title.ilike(f"%{search}%"),
                User.full_name.ilike(f"%{search}%"),
            )
        )

    # Count
    count_query = select(func.count()).select_from(AIConversation)
    if flagged_only:
        count_query = count_query.where(AIConversation.is_flagged == True)
    if student_id:
        count_query = count_query.where(AIConversation.student_id == student_id)
    total = await db.scalar(count_query)

    result = await db.execute(query.limit(limit).offset(offset))
    conversations = [
        {
            "id": str(conv.id),
            "student_id": str(conv.student_id),
            "student_name": name,
            "title": conv.title or "New conversation",
            "is_flagged": conv.is_flagged,
            "flag_reason": conv.flag_reason,
            "created_at": conv.created_at.isoformat() if conv.created_at else None,
        }
        for conv, name in result.all()
    ]

    return {"conversations": conversations, "total": total or 0, "limit": limit, "offset": offset}


async def get_conversation_messages(
    db: AsyncSession,
    conversation_id: uuid.UUID,
) -> list[dict]:
    """Get all messages in a conversation (full audit access)."""
    result = await db.execute(
        select(AIMessage)
        .where(AIMessage.conversation_id == conversation_id)
        .order_by(AIMessage.created_at)
    )
    return [
        {
            "id": str(m.id),
            "role": m.role,
            "content": m.content,
            "topic_tag": m.topic_tag,
            "cache_source": m.cache_source.value if m.cache_source else None,
            "created_at": m.created_at.isoformat() if m.created_at else None,
        }
        for m in result.scalars().all()
    ]


# ── Master Data ───────────────────────────────────────────────

async def get_master_data_summary(db: AsyncSession) -> dict:
    """Get summary of all master data (subjects, boards, grades)."""
    # Subjects by grade
    grade_result = await db.execute(
        select(Subject.grade, func.count().label("cnt"))
        .group_by(Subject.grade)
        .order_by(Subject.grade)
    )
    grades = [{"grade": row[0], "subject_count": row[1]} for row in grade_result.all()]

    # Boards
    board_result = await db.execute(
        select(Subject.board, func.count().label("cnt"))
        .group_by(Subject.board)
    )
    boards = [{"board": row[0], "subject_count": row[1]} for row in board_result.all()]

    # Total units
    from app.models.syllabus import SyllabusUnit
    total_units = await db.scalar(select(func.count()).select_from(SyllabusUnit))

    return {
        "grades": grades,
        "boards": boards,
        "total_subjects": sum(g["subject_count"] for g in grades),
        "total_units": total_units or 0,
    }


# ── Homepage CMS ─────────────────────────────────────────────

async def list_homepage_content(
    db: AsyncSession,
    section: Optional[str] = None,
) -> list[dict]:
    """List all homepage content sections."""
    query = select(HomepageContent).order_by(HomepageContent.display_order)
    if section:
        query = query.where(HomepageContent.section == section)

    result = await db.execute(query)
    return [
        {
            "id": str(c.id),
            "section": c.section,
            "title": c.title,
            "content": c.content,
            "media_url": c.media_url,
            "display_order": c.display_order,
            "status": c.status.value,
            "language": c.language,
        }
        for c in result.scalars().all()
    ]


async def upsert_homepage_content(
    db: AsyncSession,
    admin_id: uuid.UUID,
    section: str,
    title: Optional[str] = None,
    content: Optional[str] = None,
    media_url: Optional[str] = None,
    display_order: int = 0,
    status: str = "draft",
    language: str = "mr",
    content_id: Optional[uuid.UUID] = None,
) -> dict:
    """Create or update homepage content."""
    if content_id:
        existing = await db.get(HomepageContent, content_id)
        if existing:
            existing.title = title
            existing.content = content
            existing.media_url = media_url
            existing.display_order = display_order
            existing.status = ContentStatus(status)
            existing.language = language
            await db.commit()
            return {"id": str(existing.id), "updated": True}

    new_content = HomepageContent(
        section=section,
        title=title,
        content=content,
        media_url=media_url,
        display_order=display_order,
        status=ContentStatus(status),
        language=language,
        created_by=admin_id,
    )
    db.add(new_content)
    await db.commit()
    await db.refresh(new_content)
    return {"id": str(new_content.id), "created": True}


# ── Audit Log Access ─────────────────────────────────────────

async def get_audit_logs(
    db: AsyncSession,
    action_filter: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> dict:
    """Get audit logs with optional action filter."""
    query = (
        select(AuditLog, User.full_name)
        .join(User, User.id == AuditLog.user_id)
        .order_by(AuditLog.created_at.desc())
    )

    if action_filter:
        query = query.where(AuditLog.action.ilike(f"%{action_filter}%"))

    total = await db.scalar(select(func.count()).select_from(AuditLog))
    result = await db.execute(query.limit(limit).offset(offset))

    logs = [
        {
            "id": str(log.id),
            "user_name": name,
            "action": log.action,
            "resource_type": log.resource_type,
            "resource_id": str(log.resource_id) if log.resource_id else None,
            "details": log.details,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        }
        for log, name in result.all()
    ]

    return {"logs": logs, "total": total or 0}
