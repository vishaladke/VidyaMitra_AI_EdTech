"""Teacher router — RBAC: Teacher only.

Endpoints:
- GET  /api/teachers/dashboard       — dashboard stats
- GET  /api/teachers/students        — class roster
- GET  /api/teachers/students/{id}   — student detail + progress
- POST /api/teachers/attendance      — mark attendance (single)
- POST /api/teachers/attendance/bulk — mark attendance (bulk)
- GET  /api/teachers/attendance      — attendance summary
- GET  /api/teachers/ai-usage        — AI usage oversight
- POST /api/teachers/assignments     — create assignment
- GET  /api/teachers/assignments     — list assignments
"""
import uuid
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, require_role
from app.models.user import User, UserRole
from app.models.attendance import AttendanceStatus
from app.models.assessment import AssignmentType
from app.services.teacher_service import (
    get_teacher_dashboard_stats,
    get_teacher_students,
    get_student_detail,
    mark_attendance,
    bulk_mark_attendance,
    get_attendance_summary,
    get_ai_usage_overview,
    create_assignment,
    get_teacher_assignments,
)

router = APIRouter(prefix="/api/teachers", tags=["teachers"])


# ── Schemas ───────────────────────────────────────────────────

class AttendanceMarkRequest(BaseModel):
    student_id: str
    class_id: str
    date: str  # YYYY-MM-DD
    status: str  # present | absent | late
    notes: Optional[str] = None


class BulkAttendanceRequest(BaseModel):
    class_id: str
    date: str
    records: list[dict]  # [{"student_id": "...", "status": "present"}]


class CreateAssignmentRequest(BaseModel):
    title: str
    subject_id: str
    assignment_type: str = "homework"
    description: Optional[str] = None
    due_date: Optional[str] = None
    max_score: Optional[float] = None
    class_id: Optional[str] = None
    syllabus_unit_id: Optional[str] = None


# ── Dashboard ─────────────────────────────────────────────────

@router.get("/dashboard")
async def teacher_dashboard(
    user: User = Depends(require_role(UserRole.TEACHER)),
    db: AsyncSession = Depends(get_db),
):
    """Teacher dashboard with live stats."""
    stats = await get_teacher_dashboard_stats(db, user.id)
    return {
        "user": {
            "id": str(user.id),
            "full_name": user.full_name,
            "role": user.role.value,
        },
        "stats": stats,
    }


# ── Roster ────────────────────────────────────────────────────

@router.get("/students")
async def list_students(
    user: User = Depends(require_role(UserRole.TEACHER)),
    db: AsyncSession = Depends(get_db),
):
    """Get all students in teacher's classes."""
    students = await get_teacher_students(db, user.id)
    return {"students": students, "total": len(students)}


@router.get("/students/{student_id}")
async def student_detail(
    student_id: uuid.UUID,
    user: User = Depends(require_role(UserRole.TEACHER)),
    db: AsyncSession = Depends(get_db),
):
    """Get detailed progress for a specific student."""
    detail = await get_student_detail(db, student_id)
    if not detail:
        raise HTTPException(404, "Student not found")
    return detail


# ── Attendance ────────────────────────────────────────────────

@router.post("/attendance")
async def mark_student_attendance(
    body: AttendanceMarkRequest,
    user: User = Depends(require_role(UserRole.TEACHER)),
    db: AsyncSession = Depends(get_db),
):
    """Mark attendance for a single student."""
    result = await mark_attendance(
        db, user.id,
        uuid.UUID(body.student_id),
        date.fromisoformat(body.date),
        AttendanceStatus(body.status),
        uuid.UUID(body.class_id),
        notes=body.notes,
    )
    return result


@router.post("/attendance/bulk")
async def mark_bulk_attendance(
    body: BulkAttendanceRequest,
    user: User = Depends(require_role(UserRole.TEACHER)),
    db: AsyncSession = Depends(get_db),
):
    """Mark attendance for multiple students at once."""
    count = await bulk_mark_attendance(
        db, user.id,
        uuid.UUID(body.class_id),
        date.fromisoformat(body.date),
        body.records,
    )
    return {"marked": count}


@router.get("/attendance/summary")
async def attendance_summary(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    user: User = Depends(require_role(UserRole.TEACHER)),
    db: AsyncSession = Depends(get_db),
):
    """Get attendance summary per student."""
    start = date.fromisoformat(start_date) if start_date else None
    end = date.fromisoformat(end_date) if end_date else None
    summary = await get_attendance_summary(db, user.id, start, end)
    return {"summary": summary}


# ── AI Usage ──────────────────────────────────────────────────

@router.get("/ai-usage")
async def ai_usage_overview(
    days: int = Query(7, ge=1, le=90),
    user: User = Depends(require_role(UserRole.TEACHER)),
    db: AsyncSession = Depends(get_db),
):
    """Get AI usage overview for the teacher's students."""
    overview = await get_ai_usage_overview(db, user.id, days)
    return overview


# ── Assignments ───────────────────────────────────────────────

@router.post("/assignments")
async def create_new_assignment(
    body: CreateAssignmentRequest,
    user: User = Depends(require_role(UserRole.TEACHER)),
    db: AsyncSession = Depends(get_db),
):
    """Create a new homework or test assignment."""
    result = await create_assignment(
        db, user.id,
        title=body.title,
        subject_id=uuid.UUID(body.subject_id),
        assignment_type=AssignmentType(body.assignment_type),
        description=body.description,
        due_date=body.due_date,
        max_score=body.max_score,
        class_id=uuid.UUID(body.class_id) if body.class_id else None,
        syllabus_unit_id=uuid.UUID(body.syllabus_unit_id) if body.syllabus_unit_id else None,
    )
    return result


@router.get("/assignments")
async def list_assignments(
    limit: int = Query(20, ge=1, le=100),
    user: User = Depends(require_role(UserRole.TEACHER)),
    db: AsyncSession = Depends(get_db),
):
    """List assignments created by this teacher."""
    assignments = await get_teacher_assignments(db, user.id, limit)
    return {"assignments": assignments}
