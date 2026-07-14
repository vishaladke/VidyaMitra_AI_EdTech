"""Parent service — linked children, progress view, notification preferences.

Parents can see the same progress data as teachers, but only for their
linked children (via parent_student_links table).
"""
import uuid
from typing import Optional

from sqlalchemy import select, func, and_, distinct
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole, StudentProfile, ParentProfile, ParentStudentLink
from app.models.ai import AIConversation, AIMessage
from app.models.attendance import AttendanceRecord, AttendanceStatus
from app.models.assessment import TestAttempt
from app.models.syllabus import Subject


async def get_linked_children(
    db: AsyncSession,
    parent_id: uuid.UUID,
) -> list[dict]:
    """Get all children linked to this parent."""
    result = await db.execute(
        select(User, StudentProfile, ParentStudentLink)
        .join(ParentStudentLink, ParentStudentLink.student_id == User.id)
        .outerjoin(StudentProfile, StudentProfile.user_id == User.id)
        .where(
            ParentStudentLink.parent_id == parent_id,
            User.is_active == True,
        )
        .order_by(User.full_name)
    )

    children = []
    for user, profile, link in result.all():
        children.append({
            "id": str(user.id),
            "full_name": user.full_name,
            "grade": profile.grade if profile else None,
            "board": profile.board if profile else None,
            "streak_days": profile.streak_days if profile else 0,
            "city": profile.city if profile else None,
            "relationship": link.relationship_type,
            "is_primary": link.is_primary,
        })

    return children


async def get_parent_dashboard_stats(
    db: AsyncSession,
    parent_id: uuid.UUID,
) -> dict:
    """Get dashboard overview stats for a parent."""
    children = await get_linked_children(db, parent_id)
    child_ids = [uuid.UUID(c["id"]) for c in children]

    if not child_ids:
        return {
            "total_children": 0,
            "active_today": 0,
            "total_ai_conversations": 0,
            "avg_streak": 0,
        }

    from datetime import date
    today = date.today()

    # Active today
    active_today = await db.scalar(
        select(func.count(distinct(AIConversation.student_id))).where(
            and_(
                AIConversation.student_id.in_(child_ids),
                func.date(AIConversation.created_at) == today,
            )
        )
    )

    # Total AI conversations across all children
    total_convos = await db.scalar(
        select(func.count()).select_from(AIConversation).where(
            AIConversation.student_id.in_(child_ids)
        )
    )

    # Average streak
    avg_streak = sum(c.get("streak_days", 0) for c in children) / len(children) if children else 0

    return {
        "total_children": len(children),
        "active_today": active_today or 0,
        "total_ai_conversations": total_convos or 0,
        "avg_streak": round(avg_streak, 1),
    }


async def get_child_progress(
    db: AsyncSession,
    child_id: uuid.UUID,
    parent_id: uuid.UUID,
) -> Optional[dict]:
    """Get progress for a specific child (with parent authorization check).
    
    Returns None if the child is not linked to this parent.
    """
    # Verify parent-child link
    link_result = await db.execute(
        select(ParentStudentLink).where(
            and_(
                ParentStudentLink.parent_id == parent_id,
                ParentStudentLink.student_id == child_id,
            )
        )
    )
    if not link_result.scalar_one_or_none():
        return None

    # Get user + profile
    result = await db.execute(
        select(User, StudentProfile)
        .outerjoin(StudentProfile, StudentProfile.user_id == User.id)
        .where(User.id == child_id)
    )
    row = result.one_or_none()
    if not row:
        return None

    user, profile = row

    # AI stats
    conv_count = await db.scalar(
        select(func.count()).select_from(AIConversation).where(
            AIConversation.student_id == child_id
        )
    )

    msg_count = await db.scalar(
        select(func.count()).select_from(AIMessage).where(
            AIMessage.conversation_id.in_(
                select(AIConversation.id).where(
                    AIConversation.student_id == child_id
                )
            )
        )
    )

    # Subject distribution
    subject_dist = await db.execute(
        select(
            Subject.name, Subject.name_en,
            func.count(AIConversation.id).label("cnt"),
        )
        .outerjoin(Subject, Subject.id == AIConversation.subject_id)
        .where(AIConversation.student_id == child_id)
        .group_by(Subject.name, Subject.name_en)
    )
    subjects = [
        {"name": row[0] or "General", "name_en": row[1], "conversations": row[2]}
        for row in subject_dist.all()
    ]

    # Recent test scores
    test_result = await db.execute(
        select(TestAttempt)
        .where(TestAttempt.student_id == child_id)
        .order_by(TestAttempt.created_at.desc())
        .limit(5)
    )
    recent_tests = [
        {
            "score": float(t.score) if t.score else None,
            "max_score": float(t.max_score) if t.max_score else None,
            "percentage": float(t.percentage) if t.percentage else None,
            "submitted_at": t.submitted_at.isoformat() if t.submitted_at else None,
        }
        for t in test_result.scalars().all()
    ]

    # Attendance (last 30 days)
    from datetime import date, timedelta
    thirty_days_ago = date.today() - timedelta(days=30)

    attendance_total = await db.scalar(
        select(func.count()).select_from(AttendanceRecord).where(
            and_(
                AttendanceRecord.student_id == child_id,
                AttendanceRecord.date >= thirty_days_ago,
            )
        )
    )
    attendance_present = await db.scalar(
        select(func.count()).select_from(AttendanceRecord).where(
            and_(
                AttendanceRecord.student_id == child_id,
                AttendanceRecord.date >= thirty_days_ago,
                AttendanceRecord.status == AttendanceStatus.PRESENT,
            )
        )
    )
    attendance_pct = round((attendance_present / attendance_total * 100), 1) if attendance_total else 0

    return {
        "child": {
            "id": str(user.id),
            "full_name": user.full_name,
            "grade": profile.grade if profile else None,
            "streak_days": profile.streak_days if profile else 0,
        },
        "ai_stats": {
            "total_conversations": conv_count or 0,
            "total_messages": msg_count or 0,
            "subjects": subjects,
        },
        "recent_tests": recent_tests,
        "attendance": {
            "total_days": attendance_total or 0,
            "present_days": attendance_present or 0,
            "attendance_pct": attendance_pct,
        },
    }


async def update_notification_preferences(
    db: AsyncSession,
    parent_id: uuid.UUID,
    preferences: dict,
) -> dict:
    """Update parent's notification preferences."""
    result = await db.execute(
        select(ParentProfile).where(ParentProfile.user_id == parent_id)
    )
    profile = result.scalar_one_or_none()

    if not profile:
        return {"error": "Profile not found"}

    profile.notification_preferences = preferences
    await db.commit()

    return {
        "updated": True,
        "preferences": preferences,
    }


async def get_notification_preferences(
    db: AsyncSession,
    parent_id: uuid.UUID,
) -> dict:
    """Get parent's current notification preferences."""
    result = await db.execute(
        select(ParentProfile).where(ParentProfile.user_id == parent_id)
    )
    profile = result.scalar_one_or_none()

    return profile.notification_preferences if profile and profile.notification_preferences else {
        "whatsapp": True,
        "email": False,
    }
