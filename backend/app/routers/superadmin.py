"""Super Admin router — mounted at /{SUPERADMIN_URL_PATH}/api/...

Per ARCHITECTURE.md §8:
- Unlisted path, not linked from any public navigation
- Mandatory TOTP beyond the standard OTP flow
- Own rate-limited lockout
- RBAC: Super Admin only

Endpoints:
- GET  /dashboard          — overview stats
- GET  /ai-costs           — AI cost dashboard
- GET  /chat-audit         — chat audit log
- GET  /chat-audit/{id}    — conversation messages
- GET  /master-data        — master data summary
- GET  /cms                — list homepage content
- POST /cms                — create/update homepage content
- GET  /audit-logs         — admin action audit logs
"""
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, require_role
from app.models.user import User, UserRole
from app.services.superadmin_service import (
    get_superadmin_dashboard_stats,
    get_ai_cost_dashboard,
    get_chat_audit,
    get_conversation_messages,
    get_master_data_summary,
    list_homepage_content,
    upsert_homepage_content,
    get_audit_logs,
)

router = APIRouter(tags=["superadmin"])


# ── Schemas ───────────────────────────────────────────────────

class CMSContentRequest(BaseModel):
    section: str
    title: Optional[str] = None
    content: Optional[str] = None
    media_url: Optional[str] = None
    display_order: int = 0
    status: str = "draft"
    language: str = "mr"
    content_id: Optional[str] = None


# ── Dashboard ─────────────────────────────────────────────────

@router.get("/dashboard")
async def superadmin_dashboard(
    user: User = Depends(require_role(UserRole.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Super Admin dashboard with full platform stats."""
    stats = await get_superadmin_dashboard_stats(db)
    return {
        "user": {"id": str(user.id), "full_name": user.full_name, "role": user.role.value},
        "stats": stats,
    }


# ── AI Costs ──────────────────────────────────────────────────

@router.get("/ai-costs")
async def ai_costs(
    days: int = Query(30, ge=1, le=365),
    user: User = Depends(require_role(UserRole.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """AI cost dashboard: tokens, ₹, cache-hit rate, per-user breakdown."""
    return await get_ai_cost_dashboard(db, days)


# ── Chat Audit ────────────────────────────────────────────────

@router.get("/chat-audit")
async def chat_audit(
    search: Optional[str] = Query(None),
    flagged_only: bool = Query(False),
    student_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    user: User = Depends(require_role(UserRole.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Full AI conversation audit log with search and filters."""
    sid = uuid.UUID(student_id) if student_id else None
    return await get_chat_audit(db, search=search, flagged_only=flagged_only, student_id=sid, limit=limit, offset=offset)


@router.get("/chat-audit/{conversation_id}")
async def chat_messages(
    conversation_id: uuid.UUID,
    user: User = Depends(require_role(UserRole.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Get all messages in a conversation (full audit access)."""
    messages = await get_conversation_messages(db, conversation_id)
    return {"messages": messages}


# ── Master Data ───────────────────────────────────────────────

@router.get("/master-data")
async def master_data(
    user: User = Depends(require_role(UserRole.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Master data summary: grades, boards, subjects, units."""
    return await get_master_data_summary(db)


# ── Homepage CMS ─────────────────────────────────────────────

@router.get("/cms")
async def cms_list(
    section: Optional[str] = Query(None),
    user: User = Depends(require_role(UserRole.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """List homepage content sections."""
    content = await list_homepage_content(db, section=section)
    return {"content": content}


@router.post("/cms")
async def cms_upsert(
    body: CMSContentRequest,
    user: User = Depends(require_role(UserRole.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Create or update homepage content."""
    return await upsert_homepage_content(
        db, user.id, body.section, body.title, body.content,
        body.media_url, body.display_order, body.status, body.language,
        uuid.UUID(body.content_id) if body.content_id else None,
    )


# ── Audit Logs ────────────────────────────────────────────────

@router.get("/audit-logs")
async def audit_logs(
    action: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    user: User = Depends(require_role(UserRole.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Get admin action audit logs."""
    return await get_audit_logs(db, action_filter=action, limit=limit, offset=offset)
