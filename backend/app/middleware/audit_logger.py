"""Audit logger middleware — logs every Admin/Super Admin action.

Per ARCHITECTURE.md §8: Audit log for every Admin/Super Admin action.
"""
import uuid
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content import AuditLog
from app.models.user import User, UserRole


async def log_admin_action(
    db: AsyncSession,
    user: User,
    action: str,
    resource_type: Optional[str] = None,
    resource_id: Optional[uuid.UUID] = None,
    details: Optional[dict] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
):
    """Log an admin/super admin action to the audit_logs table.
    Only logs for Admin and Super Admin roles."""
    if user.role not in (UserRole.ADMIN, UserRole.SUPER_ADMIN):
        return

    log = AuditLog(
        user_id=user.id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details or {},
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.add(log)
    await db.commit()
