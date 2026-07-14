"""Teacher service — class roster, attendance, student progress, AI usage oversight.

All functions scope data to the teacher's assigned classes via TeacherClassAssignment.
For the pilot (no formal school onboarding yet), teachers can see all students
if they have no class assignments.
"""
import uuid
from datetime import date, timedelta
from typing import Optional

from sqlalchemy import select, func, and_, distinct
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole, StudentProfile, TeacherProfile
from app.models.school import Class, Section, TeacherClassAssignment
from app.models.attendance import AttendanceRecord, AttendanceStatus
from app.models.assessment import Assignment, TestAttempt, AssignmentType
from app.models.ai import AIConversation, AIMessage
from app.models.syllabus import Subject


# ── Roster ────────────────────────────────────────────────────

async def get_teacher_students(
    db: AsyncSession,
    teacher_id: uuid.UUID,
) -> list[dict]:
    """Get all students visible to this teacher.
    
    If the teacher has class assignments, returns students in those classes.
    Otherwise (pilot mode), returns all active students.
    """
    # Check if teacher has class assignments
    assignment_result = await db.execute(
        select(TeacherClassAssignment).where(
            TeacherClassAssignment.teacher_id == teacher_id
        ).limit(1)
    )
    has_assignments = assignment_result.scalar_one_or_none() is not None

    if has_assignments:
        # Get students in teacher's assigned classes
        result = await db.execute(
            select(User, StudentProfile)
            .join(StudentProfile, StudentProfile.user_id == User.id)
            .where(
                User.role == UserRole.STUDENT,
                User.is_active == True,
                StudentProfile.section_id.in_(
                    select(Section.id).where(
                        Section.class_id.in_(
                            select(TeacherClassAssignment.class_id).where(
                                TeacherClassAssignment.teacher_id == teacher_id
                            )
                        )
                    )
                ),
            )
            .order_by(User.full_name)
        )
    else:
        # Pilot mode — show all students
        result = await db.execute(
            select(User, StudentProfile)
            .join(StudentProfile, StudentProfile.user_id == User.id)
            .where(
                User.role == UserRole.STUDENT,
                User.is_active == True,
            )
            .order_by(User.full_name)
        )

    students = []
    for user, profile in result.all():
        students.append({
            "id": str(user.id),
            "full_name": user.full_name,
            "phone": user.phone,
            "grade": profile.grade if profile else None,
            "board": profile.board if profile else None,
            "streak_days": profile.streak_days if profile else 0,
            "city": profile.city if profile else None,
        })

    return students


async def get_teacher_dashboard_stats(
    db: AsyncSession,
    teacher_id: uuid.UUID,
) -> dict:
    """Get dashboard overview stats for a teacher."""
    students = await get_teacher_students(db, teacher_id)
    student_ids = [uuid.UUID(s["id"]) for s in students]

    if not student_ids:
        return {
            "total_students": 0,
            "active_today": 0,
            "total_assignments": 0,
            "avg_attendance_pct": 0,
            "ai_conversations_today": 0,
        }

    today = date.today()

    # Active today (students with AI conversations today)
    active_today = await db.scalar(
        select(func.count(distinct(AIConversation.student_id))).where(
            and_(
                AIConversation.student_id.in_(student_ids),
                func.date(AIConversation.created_at) == today,
            )
        )
    )

    # Total assignments created by this teacher
    total_assignments = await db.scalar(
        select(func.count()).select_from(Assignment).where(
            Assignment.created_by == teacher_id
        )
    )

    # Today's attendance rate
    today_attendance = await db.scalar(
        select(func.count()).select_from(AttendanceRecord).where(
            and_(
                AttendanceRecord.student_id.in_(student_ids),
                AttendanceRecord.date == today,
                AttendanceRecord.status == AttendanceStatus.PRESENT,
            )
        )
    )
    today_total = await db.scalar(
        select(func.count()).select_from(AttendanceRecord).where(
            and_(
                AttendanceRecord.student_id.in_(student_ids),
                AttendanceRecord.date == today,
            )
        )
    )
    avg_attendance = round((today_attendance / today_total * 100), 1) if today_total else 0

    # AI conversations today
    ai_conversations = await db.scalar(
        select(func.count()).select_from(AIConversation).where(
            and_(
                AIConversation.student_id.in_(student_ids),
                func.date(AIConversation.created_at) == today,
            )
        )
    )

    return {
        "total_students": len(students),
        "active_today": active_today or 0,
        "total_assignments": total_assignments or 0,
        "avg_attendance_pct": avg_attendance,
        "ai_conversations_today": ai_conversations or 0,
    }


# ── Attendance ────────────────────────────────────────────────

async def mark_attendance(
    db: AsyncSession,
    teacher_id: uuid.UUID,
    student_id: uuid.UUID,
    attendance_date: date,
    status: AttendanceStatus,
    class_id: uuid.UUID,
    notes: Optional[str] = None,
) -> dict:
    """Mark or update attendance for a student on a date.
    
    Uses upsert logic — if record exists for this student+class+date,
    update it. Otherwise create new.
    """
    result = await db.execute(
        select(AttendanceRecord).where(
            and_(
                AttendanceRecord.student_id == student_id,
                AttendanceRecord.class_id == class_id,
                AttendanceRecord.date == attendance_date,
            )
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        existing.status = status
        existing.marked_by = teacher_id
        existing.notes = notes
        record = existing
    else:
        record = AttendanceRecord(
            student_id=student_id,
            class_id=class_id,
            date=attendance_date,
            status=status,
            marked_by=teacher_id,
            notes=notes,
        )
        db.add(record)

    await db.commit()
    await db.refresh(record)

    return {
        "id": str(record.id),
        "student_id": str(record.student_id),
        "date": str(record.date),
        "status": record.status.value,
    }


async def bulk_mark_attendance(
    db: AsyncSession,
    teacher_id: uuid.UUID,
    class_id: uuid.UUID,
    attendance_date: date,
    records: list[dict],  # [{"student_id": "...", "status": "present|absent|late"}]
) -> int:
    """Mark attendance for multiple students at once."""
    count = 0
    for rec in records:
        status = AttendanceStatus(rec["status"])
        await mark_attendance(
            db, teacher_id,
            uuid.UUID(rec["student_id"]),
            attendance_date, status, class_id,
            notes=rec.get("notes"),
        )
        count += 1
    return count


async def get_attendance_summary(
    db: AsyncSession,
    teacher_id: uuid.UUID,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
) -> list[dict]:
    """Get attendance summary per student for a date range."""
    students = await get_teacher_students(db, teacher_id)
    student_ids = [uuid.UUID(s["id"]) for s in students]

    if not student_ids:
        return []

    if not start_date:
        start_date = date.today() - timedelta(days=30)
    if not end_date:
        end_date = date.today()

    summary = []
    for student in students:
        sid = uuid.UUID(student["id"])

        total = await db.scalar(
            select(func.count()).select_from(AttendanceRecord).where(
                and_(
                    AttendanceRecord.student_id == sid,
                    AttendanceRecord.date >= start_date,
                    AttendanceRecord.date <= end_date,
                )
            )
        )
        present = await db.scalar(
            select(func.count()).select_from(AttendanceRecord).where(
                and_(
                    AttendanceRecord.student_id == sid,
                    AttendanceRecord.date >= start_date,
                    AttendanceRecord.date <= end_date,
                    AttendanceRecord.status == AttendanceStatus.PRESENT,
                )
            )
        )

        pct = round((present / total * 100), 1) if total else 0
        summary.append({
            "student_id": student["id"],
            "student_name": student["full_name"],
            "total_days": total or 0,
            "present_days": present or 0,
            "attendance_pct": pct,
        })

    return summary


# ── Student Progress (Teacher View) ──────────────────────────

async def get_student_detail(
    db: AsyncSession,
    student_id: uuid.UUID,
) -> dict:
    """Get detailed progress for a specific student (teacher view).
    
    Includes: profile info, AI usage stats, subject-wise progress, recent activity.
    """
    # Get user + profile
    result = await db.execute(
        select(User, StudentProfile)
        .outerjoin(StudentProfile, StudentProfile.user_id == User.id)
        .where(User.id == student_id)
    )
    row = result.one_or_none()
    if not row:
        return {}

    user, profile = row

    # AI conversation count
    conv_count = await db.scalar(
        select(func.count()).select_from(AIConversation).where(
            AIConversation.student_id == student_id
        )
    )

    # AI messages count
    msg_count = await db.scalar(
        select(func.count()).select_from(AIMessage).where(
            AIMessage.conversation_id.in_(
                select(AIConversation.id).where(
                    AIConversation.student_id == student_id
                )
            )
        )
    )

    # Subject-wise conversation distribution
    subject_dist = await db.execute(
        select(
            Subject.name, Subject.name_en,
            func.count(AIConversation.id).label("conv_count"),
        )
        .outerjoin(Subject, Subject.id == AIConversation.subject_id)
        .where(AIConversation.student_id == student_id)
        .group_by(Subject.name, Subject.name_en)
    )
    subjects_data = [
        {"name": row[0] or "General", "name_en": row[1], "conversation_count": row[2]}
        for row in subject_dist.all()
    ]

    # Recent conversations (last 5)
    recent = await db.execute(
        select(AIConversation)
        .where(AIConversation.student_id == student_id)
        .order_by(AIConversation.created_at.desc())
        .limit(5)
    )
    recent_convos = [
        {
            "id": str(c.id),
            "title": c.title or "New conversation",
            "is_flagged": c.is_flagged,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        }
        for c in recent.scalars().all()
    ]

    # Test performance
    test_results = await db.execute(
        select(TestAttempt)
        .where(TestAttempt.student_id == student_id)
        .order_by(TestAttempt.created_at.desc())
        .limit(5)
    )
    recent_tests = [
        {
            "assignment_id": str(t.assignment_id),
            "score": float(t.score) if t.score else None,
            "max_score": float(t.max_score) if t.max_score else None,
            "percentage": float(t.percentage) if t.percentage else None,
            "is_graded": t.is_graded,
            "submitted_at": t.submitted_at.isoformat() if t.submitted_at else None,
        }
        for t in test_results.scalars().all()
    ]

    return {
        "student": {
            "id": str(user.id),
            "full_name": user.full_name,
            "phone": user.phone,
            "grade": profile.grade if profile else None,
            "streak_days": profile.streak_days if profile else 0,
            "city": profile.city if profile else None,
        },
        "ai_stats": {
            "total_conversations": conv_count or 0,
            "total_messages": msg_count or 0,
            "subjects": subjects_data,
        },
        "recent_conversations": recent_convos,
        "recent_tests": recent_tests,
    }


# ── AI Usage Oversight ───────────────────────────────────────

async def get_ai_usage_overview(
    db: AsyncSession,
    teacher_id: uuid.UUID,
    days: int = 7,
) -> dict:
    """Get AI usage overview for the teacher's students.
    
    Shows: total conversations, flagged conversations, topic distribution,
    most active students, and per-day activity.
    """
    students = await get_teacher_students(db, teacher_id)
    student_ids = [uuid.UUID(s["id"]) for s in students]

    if not student_ids:
        return {"total_conversations": 0, "flagged": 0, "students": [], "topics": []}

    since = date.today() - timedelta(days=days)

    # Total conversations in period
    total = await db.scalar(
        select(func.count()).select_from(AIConversation).where(
            and_(
                AIConversation.student_id.in_(student_ids),
                func.date(AIConversation.created_at) >= since,
            )
        )
    )

    # Flagged conversations (safety)
    flagged = await db.scalar(
        select(func.count()).select_from(AIConversation).where(
            and_(
                AIConversation.student_id.in_(student_ids),
                AIConversation.is_flagged == True,
                func.date(AIConversation.created_at) >= since,
            )
        )
    )

    # Top topic tags
    topic_result = await db.execute(
        select(AIMessage.topic_tag, func.count().label("cnt"))
        .where(
            and_(
                AIMessage.conversation_id.in_(
                    select(AIConversation.id).where(
                        and_(
                            AIConversation.student_id.in_(student_ids),
                            func.date(AIConversation.created_at) >= since,
                        )
                    )
                ),
                AIMessage.topic_tag.isnot(None),
            )
        )
        .group_by(AIMessage.topic_tag)
        .order_by(func.count().desc())
        .limit(10)
    )
    topics = [{"topic": row[0], "count": row[1]} for row in topic_result.all()]

    # Most active students
    active_result = await db.execute(
        select(
            AIConversation.student_id,
            func.count().label("cnt"),
        )
        .where(
            and_(
                AIConversation.student_id.in_(student_ids),
                func.date(AIConversation.created_at) >= since,
            )
        )
        .group_by(AIConversation.student_id)
        .order_by(func.count().desc())
        .limit(10)
    )

    # Map student IDs to names
    student_map = {uuid.UUID(s["id"]): s["full_name"] for s in students}
    most_active = [
        {"student_id": str(row[0]), "student_name": student_map.get(row[0], ""), "conversations": row[1]}
        for row in active_result.all()
    ]

    return {
        "total_conversations": total or 0,
        "flagged_conversations": flagged or 0,
        "topics": topics,
        "most_active_students": most_active,
        "period_days": days,
    }


# ── Assignments ──────────────────────────────────────────────

async def create_assignment(
    db: AsyncSession,
    teacher_id: uuid.UUID,
    title: str,
    subject_id: uuid.UUID,
    assignment_type: AssignmentType = AssignmentType.HOMEWORK,
    description: Optional[str] = None,
    due_date: Optional[str] = None,
    max_score: Optional[float] = None,
    class_id: Optional[uuid.UUID] = None,
    syllabus_unit_id: Optional[uuid.UUID] = None,
) -> dict:
    """Create a new assignment (homework or test)."""
    from datetime import datetime as dt

    assignment = Assignment(
        title=title,
        description=description,
        assignment_type=assignment_type,
        subject_id=subject_id,
        syllabus_unit_id=syllabus_unit_id,
        class_id=class_id,
        created_by=teacher_id,
        due_date=dt.fromisoformat(due_date) if due_date else None,
        max_score=max_score,
        is_active=True,
    )
    db.add(assignment)
    await db.commit()
    await db.refresh(assignment)

    return {
        "id": str(assignment.id),
        "title": assignment.title,
        "type": assignment.assignment_type.value,
        "subject_id": str(assignment.subject_id),
        "due_date": assignment.due_date.isoformat() if assignment.due_date else None,
    }


async def get_teacher_assignments(
    db: AsyncSession,
    teacher_id: uuid.UUID,
    limit: int = 20,
) -> list[dict]:
    """Get assignments created by this teacher."""
    result = await db.execute(
        select(Assignment)
        .where(Assignment.created_by == teacher_id)
        .order_by(Assignment.created_at.desc())
        .limit(limit)
    )
    assignments = result.scalars().all()

    return [
        {
            "id": str(a.id),
            "title": a.title,
            "type": a.assignment_type.value,
            "subject_id": str(a.subject_id),
            "due_date": a.due_date.isoformat() if a.due_date else None,
            "max_score": float(a.max_score) if a.max_score else None,
            "is_active": a.is_active,
            "created_at": a.created_at.isoformat() if a.created_at else None,
        }
        for a in assignments
    ]
