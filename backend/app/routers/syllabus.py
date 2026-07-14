"""Syllabus router — subject listing and chapter/topic tree.

Students can browse syllabus scoped to their grade.
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, require_role
from app.models.user import UserRole, StudentProfile
from app.services.syllabus_service import (
    get_subjects,
    get_syllabus_tree,
    get_unit_detail,
    get_student_progress,
)
from sqlalchemy import select

router = APIRouter(prefix="/api/syllabus", tags=["Syllabus"])


@router.get("/subjects")
async def list_subjects(
    user=Depends(require_role(UserRole.STUDENT)),
    db: AsyncSession = Depends(get_db),
):
    """List subjects for the student's grade."""
    # Get student's grade from profile
    result = await db.execute(
        select(StudentProfile).where(StudentProfile.user_id == user.id)
    )
    profile = result.scalar_one_or_none()
    grade = profile.grade if profile else 7

    subjects = await get_subjects(db, grade)
    return [
        {
            "id": str(s.id),
            "name": s.name,
            "name_en": s.name_en,
            "grade": s.grade,
            "icon_url": s.icon_url,
            "display_order": s.display_order,
        }
        for s in subjects
    ]


@router.get("/subjects/{subject_id}/tree")
async def subject_tree(
    subject_id: uuid.UUID,
    user=Depends(require_role(UserRole.STUDENT)),
    db: AsyncSession = Depends(get_db),
):
    """Get the chapter/topic tree for a subject."""
    tree = await get_syllabus_tree(db, subject_id)
    return tree


@router.get("/units/{unit_id}")
async def unit_detail(
    unit_id: uuid.UUID,
    user=Depends(require_role(UserRole.STUDENT)),
    db: AsyncSession = Depends(get_db),
):
    """Get a single syllabus unit with its children."""
    detail = await get_unit_detail(db, unit_id)
    if not detail:
        raise HTTPException(404, "Syllabus unit not found")
    return detail


@router.get("/subjects/{subject_id}/progress")
async def subject_progress(
    subject_id: uuid.UUID,
    user=Depends(require_role(UserRole.STUDENT)),
    db: AsyncSession = Depends(get_db),
):
    """Get student's progress for a subject."""
    progress = await get_student_progress(db, user.id, subject_id)
    return progress
