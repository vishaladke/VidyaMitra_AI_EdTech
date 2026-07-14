"""Student progress service — tracks completion, streaks, and study stats.

Derives progress from AI conversations and syllabus browsing activity.
Powers the student dashboard and parent/teacher progress views.
"""
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select, func, distinct, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai import AIConversation, AIMessage
from app.models.syllabus import Subject, SyllabusUnit
from app.models.user import StudentProfile


async def get_student_dashboard_stats(
    db: AsyncSession,
    student_id: uuid.UUID,
) -> dict:
    """Get dashboard-level stats for a student.
    
    Returns:
        - total_subjects: number of subjects available for this grade
        - subjects_started: subjects with at least one AI conversation
        - total_conversations: total AI chat conversations
        - total_messages: total messages sent
        - streak_days: current streak from student profile
        - last_active: timestamp of last AI conversation
    """
    # Get student profile for grade and streak
    profile_result = await db.execute(
        select(StudentProfile).where(StudentProfile.user_id == student_id)
    )
    profile = profile_result.scalar_one_or_none()
    grade = profile.grade if profile else 7
    streak = profile.streak_days if profile else 0

    # Count available subjects for this grade
    total_subjects = await db.scalar(
        select(func.count()).select_from(Subject).where(
            and_(Subject.grade == grade, Subject.is_active == True)
        )
    )

    # Count subjects with at least one conversation
    subjects_started = await db.scalar(
        select(func.count(distinct(AIConversation.subject_id))).where(
            and_(
                AIConversation.student_id == student_id,
                AIConversation.subject_id.isnot(None),
            )
        )
    )

    # Total conversations
    total_conversations = await db.scalar(
        select(func.count()).select_from(AIConversation).where(
            AIConversation.student_id == student_id
        )
    )

    # Total messages sent by the student
    total_messages = await db.scalar(
        select(func.count()).select_from(AIMessage).where(
            and_(
                AIMessage.conversation_id.in_(
                    select(AIConversation.id).where(
                        AIConversation.student_id == student_id
                    )
                ),
                AIMessage.role == "student",
            )
        )
    )

    # Last activity
    last_active = await db.scalar(
        select(func.max(AIConversation.created_at)).where(
            AIConversation.student_id == student_id
        )
    )

    return {
        "total_subjects": total_subjects or 0,
        "subjects_started": subjects_started or 0,
        "total_conversations": total_conversations or 0,
        "total_messages": total_messages or 0,
        "streak_days": streak,
        "last_active": last_active.isoformat() if last_active else None,
    }


async def get_subject_progress(
    db: AsyncSession,
    student_id: uuid.UUID,
    subject_id: uuid.UUID,
) -> dict:
    """Get progress for a specific subject.
    
    Calculates:
        - total_units: all active syllabus units (chapters + topics)
        - units_studied: units with at least one related AI conversation
        - completion_pct: units_studied / total_units * 100
        - conversation_count: total conversations for this subject
        - last_studied: when the student last studied this subject
    """
    # Total active units for this subject
    total_units = await db.scalar(
        select(func.count()).select_from(SyllabusUnit).where(
            and_(
                SyllabusUnit.subject_id == subject_id,
                SyllabusUnit.is_active == True,
            )
        )
    )

    # Conversations for this subject
    conversation_count = await db.scalar(
        select(func.count()).select_from(AIConversation).where(
            and_(
                AIConversation.student_id == student_id,
                AIConversation.subject_id == subject_id,
            )
        )
    )

    # Last studied
    last_studied = await db.scalar(
        select(func.max(AIConversation.created_at)).where(
            and_(
                AIConversation.student_id == student_id,
                AIConversation.subject_id == subject_id,
            )
        )
    )

    # Derive units studied from topic tags in AI messages
    units_studied = await db.scalar(
        select(func.count(distinct(AIMessage.topic_tag))).where(
            and_(
                AIMessage.conversation_id.in_(
                    select(AIConversation.id).where(
                        and_(
                            AIConversation.student_id == student_id,
                            AIConversation.subject_id == subject_id,
                        )
                    )
                ),
                AIMessage.topic_tag.isnot(None),
            )
        )
    )

    total = total_units or 1  # avoid division by zero
    studied = min(units_studied or 0, total)
    completion_pct = round((studied / total) * 100, 1)

    return {
        "subject_id": str(subject_id),
        "total_units": total_units or 0,
        "units_studied": studied,
        "completion_pct": completion_pct,
        "conversation_count": conversation_count or 0,
        "last_studied": last_studied.isoformat() if last_studied else None,
    }


async def get_recent_conversations(
    db: AsyncSession,
    student_id: uuid.UUID,
    limit: int = 5,
) -> list[dict]:
    """Get the student's most recent AI conversations for the dashboard."""
    result = await db.execute(
        select(AIConversation)
        .where(AIConversation.student_id == student_id)
        .order_by(AIConversation.created_at.desc())
        .limit(limit)
    )
    conversations = result.scalars().all()

    return [
        {
            "id": str(c.id),
            "title": c.title or "New conversation",
            "subject_id": str(c.subject_id) if c.subject_id else None,
            "is_flagged": c.is_flagged,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        }
        for c in conversations
    ]


async def update_streak(
    db: AsyncSession,
    student_id: uuid.UUID,
) -> int:
    """Update the student's streak based on daily activity.
    
    Called after each AI chat interaction. Increments streak if
    the student hasn't been active today, resets if they missed a day.
    """
    profile_result = await db.execute(
        select(StudentProfile).where(StudentProfile.user_id == student_id)
    )
    profile = profile_result.scalar_one_or_none()
    if not profile:
        return 0

    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday_start = today_start - timedelta(days=1)

    # Check if student was active today already
    today_count = await db.scalar(
        select(func.count()).select_from(AIConversation).where(
            and_(
                AIConversation.student_id == student_id,
                AIConversation.created_at >= today_start,
            )
        )
    )

    if today_count and today_count > 1:
        # Already counted today (>1 because current conversation is already saved)
        return profile.streak_days

    # Check if active yesterday
    yesterday_count = await db.scalar(
        select(func.count()).select_from(AIConversation).where(
            and_(
                AIConversation.student_id == student_id,
                AIConversation.created_at >= yesterday_start,
                AIConversation.created_at < today_start,
            )
        )
    )

    if yesterday_count and yesterday_count > 0:
        profile.streak_days += 1
    else:
        # Streak broken — reset to 1 (today counts)
        profile.streak_days = 1

    await db.commit()
    return profile.streak_days
