"""Parent router — RBAC: Parent only.

Endpoints:
- GET  /api/parents/dashboard          — dashboard stats
- GET  /api/parents/children           — linked children list
- GET  /api/parents/children/{id}      — child progress detail
- GET  /api/parents/reports            — weekly reports
- GET  /api/parents/notifications      — notification preferences
- PUT  /api/parents/notifications      — update notification preferences
"""
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, require_role
from app.models.user import User, UserRole
from app.services.parent_service import (
    get_linked_children,
    get_parent_dashboard_stats,
    get_child_progress,
    get_notification_preferences,
    update_notification_preferences,
)
from app.services.report_service import generate_student_report

router = APIRouter(prefix="/api/parents", tags=["parents"])


# ── Schemas ───────────────────────────────────────────────────

class NotificationPrefsRequest(BaseModel):
    whatsapp: bool = True
    email: bool = False


# ── Dashboard ─────────────────────────────────────────────────

@router.get("/dashboard")
async def parent_dashboard(
    user: User = Depends(require_role(UserRole.PARENT)),
    db: AsyncSession = Depends(get_db),
):
    """Parent dashboard with aggregated stats across all children."""
    stats = await get_parent_dashboard_stats(db, user.id)
    children = await get_linked_children(db, user.id)

    return {
        "user": {
            "id": str(user.id),
            "full_name": user.full_name,
            "role": user.role.value,
        },
        "stats": stats,
        "children": children,
    }


# ── Children ──────────────────────────────────────────────────

@router.get("/children")
async def list_children(
    user: User = Depends(require_role(UserRole.PARENT)),
    db: AsyncSession = Depends(get_db),
):
    """Get all linked children."""
    children = await get_linked_children(db, user.id)
    return {"children": children, "total": len(children)}


@router.get("/children/{child_id}")
async def child_detail(
    child_id: uuid.UUID,
    user: User = Depends(require_role(UserRole.PARENT)),
    db: AsyncSession = Depends(get_db),
):
    """Get progress detail for a specific child.
    
    Authorization: only returns data if child is linked to this parent.
    """
    progress = await get_child_progress(db, child_id, user.id)
    if not progress:
        raise HTTPException(404, "Child not found or not linked to your account")
    return progress


# ── Reports ───────────────────────────────────────────────────

@router.get("/reports")
async def weekly_reports(
    user: User = Depends(require_role(UserRole.PARENT)),
    db: AsyncSession = Depends(get_db),
):
    """Get weekly reports for all linked children."""
    children = await get_linked_children(db, user.id)
    reports = []

    for child in children:
        report = await generate_student_report(db, uuid.UUID(child["id"]))
        reports.append(report)

    return {"reports": reports}


@router.get("/reports/{child_id}")
async def child_weekly_report(
    child_id: uuid.UUID,
    user: User = Depends(require_role(UserRole.PARENT)),
    db: AsyncSession = Depends(get_db),
):
    """Get weekly report for a specific child."""
    progress = await get_child_progress(db, child_id, user.id)
    if not progress:
        raise HTTPException(404, "Child not found or not linked to your account")

    report = await generate_student_report(db, child_id)
    return report


# ── Notifications ─────────────────────────────────────────────

@router.get("/notifications")
async def get_notif_prefs(
    user: User = Depends(require_role(UserRole.PARENT)),
    db: AsyncSession = Depends(get_db),
):
    """Get notification preferences."""
    prefs = await get_notification_preferences(db, user.id)
    return {"preferences": prefs}


@router.put("/notifications")
async def update_notif_prefs(
    body: NotificationPrefsRequest,
    user: User = Depends(require_role(UserRole.PARENT)),
    db: AsyncSession = Depends(get_db),
):
    """Update notification preferences."""
    result = await update_notification_preferences(
        db, user.id,
        {"whatsapp": body.whatsapp, "email": body.email},
    )
    return result
