"""Weekly report generation service — generates student progress summaries.

Produces a structured report for each student that can be:
1. Displayed in-app to parents
2. Formatted for WhatsApp Utility template (Phase 5)
3. Stored in DB for historical access

Run as a management command: python -m app.scripts.generate_weekly_reports
Or scheduled via cron/task scheduler.
"""
import uuid
import logging
from datetime import date, timedelta
from typing import Optional

from sqlalchemy import select, func, and_, distinct
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole, StudentProfile, ParentStudentLink
from app.models.ai import AIConversation, AIMessage, AICacheSource
from app.models.attendance import AttendanceRecord, AttendanceStatus
from app.models.assessment import TestAttempt
from app.models.syllabus import Subject

logger = logging.getLogger(__name__)


async def generate_student_report(
    db: AsyncSession,
    student_id: uuid.UUID,
    week_start: Optional[date] = None,
    week_end: Optional[date] = None,
) -> dict:
    """Generate a weekly progress report for a student.
    
    Returns a structured dict suitable for:
    - In-app parent dashboard display
    - WhatsApp template formatting (Phase 5)
    """
    if not week_end:
        week_end = date.today()
    if not week_start:
        week_start = week_end - timedelta(days=7)

    # Student info
    result = await db.execute(
        select(User, StudentProfile)
        .outerjoin(StudentProfile, StudentProfile.user_id == User.id)
        .where(User.id == student_id)
    )
    row = result.one_or_none()
    if not row:
        return {"error": "Student not found"}

    user, profile = row

    # ── AI Activity ───────────────────────────────────────
    conversations_this_week = await db.scalar(
        select(func.count()).select_from(AIConversation).where(
            and_(
                AIConversation.student_id == student_id,
                func.date(AIConversation.created_at) >= week_start,
                func.date(AIConversation.created_at) <= week_end,
            )
        )
    )

    messages_this_week = await db.scalar(
        select(func.count()).select_from(AIMessage).where(
            and_(
                AIMessage.conversation_id.in_(
                    select(AIConversation.id).where(
                        and_(
                            AIConversation.student_id == student_id,
                            func.date(AIConversation.created_at) >= week_start,
                            func.date(AIConversation.created_at) <= week_end,
                        )
                    )
                ),
                AIMessage.role == "student",
            )
        )
    )

    # Active days (unique dates with activity)
    active_days_result = await db.execute(
        select(func.date(AIConversation.created_at).distinct()).where(
            and_(
                AIConversation.student_id == student_id,
                func.date(AIConversation.created_at) >= week_start,
                func.date(AIConversation.created_at) <= week_end,
            )
        )
    )
    active_days = len(active_days_result.all())

    # Top subjects studied
    subject_result = await db.execute(
        select(Subject.name, func.count().label("cnt"))
        .outerjoin(AIConversation, AIConversation.subject_id == Subject.id)
        .where(
            and_(
                AIConversation.student_id == student_id,
                func.date(AIConversation.created_at) >= week_start,
                func.date(AIConversation.created_at) <= week_end,
            )
        )
        .group_by(Subject.name)
        .order_by(func.count().desc())
        .limit(3)
    )
    top_subjects = [row[0] for row in subject_result.all()]

    # ── Attendance ────────────────────────────────────────
    att_total = await db.scalar(
        select(func.count()).select_from(AttendanceRecord).where(
            and_(
                AttendanceRecord.student_id == student_id,
                AttendanceRecord.date >= week_start,
                AttendanceRecord.date <= week_end,
            )
        )
    )
    att_present = await db.scalar(
        select(func.count()).select_from(AttendanceRecord).where(
            and_(
                AttendanceRecord.student_id == student_id,
                AttendanceRecord.date >= week_start,
                AttendanceRecord.date <= week_end,
                AttendanceRecord.status == AttendanceStatus.PRESENT,
            )
        )
    )
    attendance_pct = round((att_present / att_total * 100), 1) if att_total else None

    # ── Tests ─────────────────────────────────────────────
    test_result = await db.execute(
        select(TestAttempt).where(
            and_(
                TestAttempt.student_id == student_id,
                func.date(TestAttempt.created_at) >= week_start,
                func.date(TestAttempt.created_at) <= week_end,
                TestAttempt.is_graded == True,
            )
        )
    )
    tests = test_result.scalars().all()
    avg_score = None
    if tests:
        scores = [float(t.percentage) for t in tests if t.percentage]
        avg_score = round(sum(scores) / len(scores), 1) if scores else None

    # ── Build Report ──────────────────────────────────────
    report = {
        "student": {
            "id": str(user.id),
            "full_name": user.full_name,
            "grade": profile.grade if profile else None,
            "streak_days": profile.streak_days if profile else 0,
        },
        "period": {
            "start": str(week_start),
            "end": str(week_end),
        },
        "ai_activity": {
            "conversations": conversations_this_week or 0,
            "questions_asked": messages_this_week or 0,
            "active_days": active_days,
            "top_subjects": top_subjects,
        },
        "attendance": {
            "total_days": att_total or 0,
            "present_days": att_present or 0,
            "percentage": attendance_pct,
        },
        "tests": {
            "completed": len(tests),
            "average_score": avg_score,
        },
        "summary_mr": _build_marathi_summary(
            user.full_name,
            profile.grade if profile else 7,
            conversations_this_week or 0,
            active_days,
            top_subjects,
            attendance_pct,
            avg_score,
            profile.streak_days if profile else 0,
        ),
    }

    return report


def _build_marathi_summary(
    name: str, grade: int,
    conversations: int, active_days: int,
    top_subjects: list[str],
    attendance_pct: Optional[float],
    avg_score: Optional[float],
    streak: int,
) -> str:
    """Build a Marathi text summary for WhatsApp report.
    
    This is the template that gets sent via WhatsApp Utility category message.
    """
    lines = [
        f"📚 विद्यामित्र साप्ताहिक अहवाल",
        f"विद्यार्थी: {name} (इयत्ता {grade})",
        "",
    ]

    # Activity
    if conversations > 0:
        lines.append(f"🤖 AI गुरू: {conversations} संवाद, {active_days}/7 दिवस सक्रिय")
        if top_subjects:
            lines.append(f"📖 मुख्य विषय: {', '.join(top_subjects)}")
    else:
        lines.append("🤖 AI गुरू: या आठवड्यात वापरले नाही")

    # Streak
    if streak > 0:
        lines.append(f"🔥 स्ट्रीक: {streak} दिवस सलग")

    # Attendance
    if attendance_pct is not None:
        emoji = "✅" if attendance_pct >= 80 else "⚠️"
        lines.append(f"{emoji} उपस्थिती: {attendance_pct}%")

    # Tests
    if avg_score is not None:
        emoji = "🌟" if avg_score >= 75 else "📝"
        lines.append(f"{emoji} चाचणी सरासरी: {avg_score}%")

    lines.append("")
    lines.append("— विद्यामित्र EdTech 💙")

    return "\n".join(lines)


async def generate_all_reports(
    db: AsyncSession,
    week_start: Optional[date] = None,
    week_end: Optional[date] = None,
) -> list[dict]:
    """Generate weekly reports for all active students.
    
    Called by the weekly cron job.
    """
    if not week_end:
        week_end = date.today()
    if not week_start:
        week_start = week_end - timedelta(days=7)

    # Get all active students
    result = await db.execute(
        select(User.id).where(
            User.role == UserRole.STUDENT,
            User.is_active == True,
        )
    )
    student_ids = [row[0] for row in result.all()]

    reports = []
    for student_id in student_ids:
        try:
            report = await generate_student_report(db, student_id, week_start, week_end)
            reports.append(report)
            logger.info(f"✅ Report generated for student {student_id}")
        except Exception as e:
            logger.error(f"❌ Failed to generate report for {student_id}: {e}")

    logger.info(f"📊 Generated {len(reports)} weekly reports")
    return reports
