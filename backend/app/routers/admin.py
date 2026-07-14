"""Admin router — RBAC: Admin and Super Admin.

Endpoints:
- GET   /api/admin/dashboard         — dashboard stats
- GET   /api/admin/users             — list users (filterable)
- PUT   /api/admin/users/{id}        — update user
- POST  /api/admin/users/{id}/toggle — toggle active status
- GET   /api/admin/subjects          — list subjects
- POST  /api/admin/subjects          — create subject
- PUT   /api/admin/subjects/{id}     — update subject
- POST  /api/admin/syllabus-units    — create syllabus unit
- GET   /api/admin/classes           — list classes
- POST  /api/admin/classes           — create class
- POST  /api/admin/teacher-assign    — assign teacher to class
- GET   /api/admin/teacher-assign    — list teacher assignments
"""
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, require_role
from app.models.user import User, UserRole
from app.services.admin_service import (
    get_admin_dashboard_stats,
    list_users,
    update_user,
    toggle_user_active,
    list_subjects_admin,
    create_subject,
    update_subject,
    create_syllabus_unit,
    list_classes,
    create_class,
    assign_teacher,
    get_teacher_assignments,
)

router = APIRouter(prefix="/api/admin", tags=["admin"])


# ── Schemas ───────────────────────────────────────────────────

class UpdateUserRequest(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    is_active: Optional[bool] = None


class CreateSubjectRequest(BaseModel):
    name: str
    name_en: str
    grade: int
    board: str = "maharashtra_state"
    display_order: int = 0


class UpdateSubjectRequest(BaseModel):
    name: Optional[str] = None
    name_en: Optional[str] = None
    display_order: Optional[int] = None
    is_active: Optional[bool] = None


class CreateSyllabusUnitRequest(BaseModel):
    subject_id: str
    title: str
    unit_type: str = "chapter"
    title_en: Optional[str] = None
    parent_id: Optional[str] = None
    display_order: int = 0
    description: Optional[str] = None


class CreateClassRequest(BaseModel):
    grade: int
    name: Optional[str] = None
    academic_year: str = "2026-27"
    school_id: Optional[str] = None


class TeacherAssignRequest(BaseModel):
    teacher_id: str
    class_id: str
    subject_id: Optional[str] = None


# ── Dashboard ─────────────────────────────────────────────────

@router.get("/dashboard")
async def admin_dashboard(
    user: User = Depends(require_role(UserRole.ADMIN, UserRole.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Admin dashboard with live stats."""
    stats = await get_admin_dashboard_stats(db)
    return {
        "user": {"id": str(user.id), "full_name": user.full_name, "role": user.role.value},
        "stats": stats,
    }


# ── Users ─────────────────────────────────────────────────────

@router.get("/users")
async def users_list(
    role: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    user: User = Depends(require_role(UserRole.ADMIN, UserRole.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """List users with optional role filter and search."""
    return await list_users(db, role=role, search=search, limit=limit, offset=offset)


@router.put("/users/{user_id}")
async def user_update(
    user_id: uuid.UUID,
    body: UpdateUserRequest,
    user: User = Depends(require_role(UserRole.ADMIN, UserRole.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Update a user's profile."""
    updates = body.model_dump(exclude_none=True)
    result = await update_user(db, user.id, user_id, updates)
    if not result:
        raise HTTPException(404, "User not found")
    return result


@router.post("/users/{user_id}/toggle")
async def user_toggle(
    user_id: uuid.UUID,
    user: User = Depends(require_role(UserRole.ADMIN, UserRole.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Toggle a user's active/inactive status."""
    result = await toggle_user_active(db, user.id, user_id)
    if not result:
        raise HTTPException(404, "User not found")
    return result


# ── Syllabus ──────────────────────────────────────────────────

@router.get("/subjects")
async def subjects_list(
    grade: Optional[int] = Query(None),
    board: Optional[str] = Query(None),
    user: User = Depends(require_role(UserRole.ADMIN, UserRole.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """List all subjects (admin view, includes inactive)."""
    subjects = await list_subjects_admin(db, grade=grade, board=board)
    return {"subjects": subjects}


@router.post("/subjects")
async def subject_create(
    body: CreateSubjectRequest,
    user: User = Depends(require_role(UserRole.ADMIN, UserRole.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Create a new subject."""
    return await create_subject(db, user.id, body.name, body.name_en, body.grade, body.board, body.display_order)


@router.put("/subjects/{subject_id}")
async def subject_update(
    subject_id: uuid.UUID,
    body: UpdateSubjectRequest,
    user: User = Depends(require_role(UserRole.ADMIN, UserRole.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Update a subject."""
    updates = body.model_dump(exclude_none=True)
    result = await update_subject(db, user.id, subject_id, updates)
    if not result:
        raise HTTPException(404, "Subject not found")
    return result


@router.post("/syllabus-units")
async def syllabus_unit_create(
    body: CreateSyllabusUnitRequest,
    user: User = Depends(require_role(UserRole.ADMIN, UserRole.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Create a syllabus unit (chapter/topic/subtopic)."""
    return await create_syllabus_unit(
        db, user.id, uuid.UUID(body.subject_id), body.title, body.unit_type,
        body.title_en, uuid.UUID(body.parent_id) if body.parent_id else None,
        body.display_order, body.description,
    )


# ── Classes ───────────────────────────────────────────────────

@router.get("/classes")
async def classes_list(
    user: User = Depends(require_role(UserRole.ADMIN, UserRole.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """List all classes."""
    classes = await list_classes(db)
    return {"classes": classes}


@router.post("/classes")
async def class_create(
    body: CreateClassRequest,
    user: User = Depends(require_role(UserRole.ADMIN, UserRole.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Create a new class."""
    return await create_class(
        db, user.id, body.grade, body.name, body.academic_year,
        uuid.UUID(body.school_id) if body.school_id else None,
    )


@router.post("/teacher-assign")
async def teacher_assign(
    body: TeacherAssignRequest,
    user: User = Depends(require_role(UserRole.ADMIN, UserRole.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Assign a teacher to a class."""
    return await assign_teacher(
        db, user.id, uuid.UUID(body.teacher_id), uuid.UUID(body.class_id),
        uuid.UUID(body.subject_id) if body.subject_id else None,
    )


@router.get("/teacher-assign")
async def teacher_assign_list(
    user: User = Depends(require_role(UserRole.ADMIN, UserRole.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """List all teacher-class assignments."""
    assignments = await get_teacher_assignments(db)
    return {"assignments": assignments}
