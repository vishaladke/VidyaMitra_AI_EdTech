"""Student router — RBAC: Student only.

Endpoints:
- GET  /api/students/dashboard                 — dashboard stats + recent conversations
- GET  /api/students/assignments               — list assignments (homework/practice)
- GET  /api/students/assignments/{id}          — assignment detail with questions
- POST /api/students/assignments/{id}/submit   — submit answers (auto-grades MCQ)
- GET  /api/students/tests                     — list tests
- GET  /api/students/tests/{id}                — get test for taking (no answers)
- POST /api/students/tests/{id}/submit         — submit test attempt
- GET  /api/students/tests/{id}/result         — get test result with answers
- GET  /api/students/progress                  — full progress overview
- GET  /api/students/progress/{subject_id}     — subject-specific progress
"""
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, require_role
from app.models.user import User, UserRole
from app.schemas.student import SubmitAnswersRequest
from app.services.student_service import (
    get_student_assignments,
    get_assignment_detail,
    submit_assignment,
    get_student_tests,
    get_test_for_taking,
    get_test_result,
    get_full_progress,
)
from app.services.progress_service import (
    get_student_dashboard_stats,
    get_recent_conversations,
    get_subject_progress,
)

router = APIRouter(prefix="/api/students", tags=["students"])


# ── Dashboard ─────────────────────────────────────────────────

@router.get("/dashboard")
async def student_dashboard(
    user: User = Depends(require_role(UserRole.STUDENT)),
    db: AsyncSession = Depends(get_db),
):
    """Student dashboard with live stats and recent conversations."""
    stats = await get_student_dashboard_stats(db, user.id)
    recent = await get_recent_conversations(db, user.id, limit=5)

    return {
        "message": "Student dashboard",
        "user": {
            "id": str(user.id),
            "full_name": user.full_name,
            "role": user.role.value,
        },
        "stats": stats,
        "recent_conversations": recent,
        "modules": [
            {"name": "syllabus", "label": "अभ्यासक्रम", "status": "active"},
            {"name": "assignments", "label": "असाइनमेंट", "status": "active"},
            {"name": "tests", "label": "चाचण्या", "status": "active"},
            {"name": "ai_guru", "label": "AI गुरू", "status": "active"},
            {"name": "progress", "label": "प्रगती", "status": "active"},
        ],
    }


# ── Assignments ───────────────────────────────────────────────

@router.get("/assignments")
async def list_assignments(
    status: Optional[str] = Query(None, description="pending | completed"),
    user: User = Depends(require_role(UserRole.STUDENT)),
    db: AsyncSession = Depends(get_db),
):
    """List assignments for the student."""
    assignments = await get_student_assignments(db, user.id, filter_type=status)
    return {"assignments": assignments, "total": len(assignments)}


@router.get("/assignments/{assignment_id}")
async def assignment_detail(
    assignment_id: uuid.UUID,
    user: User = Depends(require_role(UserRole.STUDENT)),
    db: AsyncSession = Depends(get_db),
):
    """Get assignment detail with questions."""
    detail = await get_assignment_detail(db, assignment_id, user.id)
    if not detail:
        raise HTTPException(404, "Assignment not found")
    return detail


@router.post("/assignments/{assignment_id}/submit")
async def submit_assignment_answers(
    assignment_id: uuid.UUID,
    body: SubmitAnswersRequest,
    user: User = Depends(require_role(UserRole.STUDENT)),
    db: AsyncSession = Depends(get_db),
):
    """Submit answers for an assignment. Auto-grades MCQ and true/false."""
    try:
        result = await submit_assignment(db, assignment_id, user.id, body.answers)
        return result
    except ValueError as e:
        raise HTTPException(404, str(e))


# ── Tests ─────────────────────────────────────────────────────

@router.get("/tests")
async def list_tests(
    status: Optional[str] = Query(None, description="available | completed"),
    user: User = Depends(require_role(UserRole.STUDENT)),
    db: AsyncSession = Depends(get_db),
):
    """List tests for the student."""
    tests = await get_student_tests(db, user.id, filter_type=status)
    return {"tests": tests, "total": len(tests)}


@router.get("/tests/{test_id}")
async def test_for_taking(
    test_id: uuid.UUID,
    user: User = Depends(require_role(UserRole.STUDENT)),
    db: AsyncSession = Depends(get_db),
):
    """Get test questions for taking (no correct answers)."""
    test = await get_test_for_taking(db, test_id, user.id)
    if not test:
        raise HTTPException(404, "Test not found")
    return test


@router.post("/tests/{test_id}/submit")
async def submit_test(
    test_id: uuid.UUID,
    body: SubmitAnswersRequest,
    user: User = Depends(require_role(UserRole.STUDENT)),
    db: AsyncSession = Depends(get_db),
):
    """Submit test answers. Auto-grades MCQ and true/false."""
    try:
        result = await submit_assignment(db, test_id, user.id, body.answers)
        return result
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.get("/tests/{test_id}/result")
async def test_result(
    test_id: uuid.UUID,
    user: User = Depends(require_role(UserRole.STUDENT)),
    db: AsyncSession = Depends(get_db),
):
    """Get test result with correct answers and explanations."""
    result = await get_test_result(db, test_id, user.id)
    if not result:
        raise HTTPException(404, "Test result not found — have you submitted this test?")
    return result


# ── Progress ──────────────────────────────────────────────────

@router.get("/progress")
async def progress_overview(
    user: User = Depends(require_role(UserRole.STUDENT)),
    db: AsyncSession = Depends(get_db),
):
    """Full progress overview across all subjects."""
    progress = await get_full_progress(db, user.id)
    return progress


@router.get("/progress/{subject_id}")
async def subject_progress_detail(
    subject_id: uuid.UUID,
    user: User = Depends(require_role(UserRole.STUDENT)),
    db: AsyncSession = Depends(get_db),
):
    """Detailed progress for a specific subject."""
    progress = await get_subject_progress(db, user.id, subject_id)
    return progress
