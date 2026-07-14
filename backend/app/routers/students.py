"""Student router — RBAC: Student only."""
from fastapi import APIRouter, Depends

from app.dependencies import require_role
from app.models.user import User, UserRole

router = APIRouter(prefix="/api/students", tags=["students"])


@router.get("/dashboard")
async def student_dashboard(user: User = Depends(require_role(UserRole.STUDENT))):
    """Student dashboard — shell for Phase 1."""
    return {
        "message": "Student dashboard",
        "user": {
            "id": str(user.id),
            "full_name": user.full_name,
            "role": user.role.value,
        },
        "modules": [
            {"name": "syllabus", "label": "अभ्यासक्रम", "status": "coming_phase_2"},
            {"name": "assignments", "label": "असाइनमेंट", "status": "coming_phase_2"},
            {"name": "tests", "label": "चाचण्या", "status": "coming_phase_2"},
            {"name": "ai_guru", "label": "AI गुरू", "status": "coming_phase_2"},
            {"name": "progress", "label": "प्रगती", "status": "coming_phase_2"},
        ],
    }
