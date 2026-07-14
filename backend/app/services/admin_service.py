"""Admin service — syllabus CRUD, user management, class management.

All admin actions are audit-logged via the AuditLog model.
"""
import uuid
import logging
from typing import Optional

from sqlalchemy import select, func, and_, or_, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole, StudentProfile, TeacherProfile, ParentProfile
from app.models.school import School, Class, Section, TeacherClassAssignment
from app.models.syllabus import Subject, SyllabusUnit
from app.models.content import AuditLog

logger = logging.getLogger(__name__)


# ── Audit Helper ──────────────────────────────────────────────

async def _audit_log(
    db: AsyncSession,
    user_id: uuid.UUID,
    action: str,
    resource_type: Optional[str] = None,
    resource_id: Optional[uuid.UUID] = None,
    details: Optional[dict] = None,
) -> None:
    """Log an admin action for audit trail."""
    log = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details or {},
    )
    db.add(log)


# ── Dashboard Stats ──────────────────────────────────────────

async def get_admin_dashboard_stats(db: AsyncSession) -> dict:
    """Get admin dashboard overview stats."""
    total_users = await db.scalar(select(func.count()).select_from(User))
    total_students = await db.scalar(
        select(func.count()).select_from(User).where(User.role == UserRole.STUDENT)
    )
    total_teachers = await db.scalar(
        select(func.count()).select_from(User).where(User.role == UserRole.TEACHER)
    )
    total_parents = await db.scalar(
        select(func.count()).select_from(User).where(User.role == UserRole.PARENT)
    )
    total_subjects = await db.scalar(select(func.count()).select_from(Subject))
    total_classes = await db.scalar(select(func.count()).select_from(Class))

    return {
        "total_users": total_users or 0,
        "total_students": total_students or 0,
        "total_teachers": total_teachers or 0,
        "total_parents": total_parents or 0,
        "total_subjects": total_subjects or 0,
        "total_classes": total_classes or 0,
    }


# ── User Management ──────────────────────────────────────────

async def list_users(
    db: AsyncSession,
    role: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> dict:
    """List users with optional filtering."""
    query = select(User).order_by(User.created_at.desc())

    if role:
        query = query.where(User.role == UserRole(role))
    if search:
        query = query.where(
            or_(
                User.full_name.ilike(f"%{search}%"),
                User.phone.ilike(f"%{search}%"),
            )
        )

    # Get total count
    count_query = select(func.count()).select_from(User)
    if role:
        count_query = count_query.where(User.role == UserRole(role))
    if search:
        count_query = count_query.where(
            or_(
                User.full_name.ilike(f"%{search}%"),
                User.phone.ilike(f"%{search}%"),
            )
        )
    total = await db.scalar(count_query)

    result = await db.execute(query.limit(limit).offset(offset))
    users = [
        {
            "id": str(u.id),
            "phone": u.phone,
            "email": u.email,
            "full_name": u.full_name,
            "role": u.role.value,
            "is_active": u.is_active,
            "created_at": u.created_at.isoformat() if u.created_at else None,
            "last_login_at": u.last_login_at.isoformat() if u.last_login_at else None,
        }
        for u in result.scalars().all()
    ]

    return {"users": users, "total": total or 0, "limit": limit, "offset": offset}


async def update_user(
    db: AsyncSession,
    admin_id: uuid.UUID,
    user_id: uuid.UUID,
    updates: dict,
) -> Optional[dict]:
    """Update a user's profile fields."""
    user = await db.get(User, user_id)
    if not user:
        return None

    allowed_fields = {"full_name", "phone", "email", "is_active"}
    for field, value in updates.items():
        if field in allowed_fields:
            setattr(user, field, value)

    await _audit_log(db, admin_id, "user.update", "user", user_id, updates)
    await db.commit()

    return {
        "id": str(user.id),
        "full_name": user.full_name,
        "phone": user.phone,
        "email": user.email,
        "is_active": user.is_active,
    }


async def toggle_user_active(
    db: AsyncSession,
    admin_id: uuid.UUID,
    user_id: uuid.UUID,
) -> Optional[dict]:
    """Toggle a user's active status."""
    user = await db.get(User, user_id)
    if not user:
        return None

    user.is_active = not user.is_active
    await _audit_log(
        db, admin_id, "user.toggle_active", "user", user_id,
        {"is_active": user.is_active},
    )
    await db.commit()

    return {"id": str(user.id), "is_active": user.is_active}


# ── Syllabus CRUD ─────────────────────────────────────────────

async def list_subjects_admin(
    db: AsyncSession,
    grade: Optional[int] = None,
    board: Optional[str] = None,
) -> list[dict]:
    """List all subjects (admin view — includes inactive)."""
    query = select(Subject).order_by(Subject.grade, Subject.display_order)
    if grade:
        query = query.where(Subject.grade == grade)
    if board:
        query = query.where(Subject.board == board)

    result = await db.execute(query)
    return [
        {
            "id": str(s.id),
            "name": s.name,
            "name_en": s.name_en,
            "grade": s.grade,
            "board": s.board,
            "display_order": s.display_order,
            "is_active": s.is_active,
        }
        for s in result.scalars().all()
    ]


async def create_subject(
    db: AsyncSession,
    admin_id: uuid.UUID,
    name: str,
    name_en: str,
    grade: int,
    board: str = "maharashtra_state",
    display_order: int = 0,
) -> dict:
    """Create a new subject."""
    subject = Subject(
        id=uuid.uuid4(),
        name=name,
        name_en=name_en,
        grade=grade,
        board=board,
        display_order=display_order,
        is_active=True,
    )
    db.add(subject)
    await _audit_log(db, admin_id, "subject.create", "subject", subject.id, {"name": name, "grade": grade})
    await db.commit()

    return {"id": str(subject.id), "name": name, "grade": grade}


async def update_subject(
    db: AsyncSession,
    admin_id: uuid.UUID,
    subject_id: uuid.UUID,
    updates: dict,
) -> Optional[dict]:
    """Update a subject's fields."""
    subject = await db.get(Subject, subject_id)
    if not subject:
        return None

    allowed = {"name", "name_en", "display_order", "is_active"}
    for field, value in updates.items():
        if field in allowed:
            setattr(subject, field, value)

    await _audit_log(db, admin_id, "subject.update", "subject", subject_id, updates)
    await db.commit()

    return {"id": str(subject.id), "name": subject.name, "updated": True}


async def create_syllabus_unit(
    db: AsyncSession,
    admin_id: uuid.UUID,
    subject_id: uuid.UUID,
    title: str,
    unit_type: str = "chapter",
    title_en: Optional[str] = None,
    parent_id: Optional[uuid.UUID] = None,
    display_order: int = 0,
    description: Optional[str] = None,
) -> dict:
    """Create a new syllabus unit (chapter/topic/subtopic)."""
    unit = SyllabusUnit(
        id=uuid.uuid4(),
        subject_id=subject_id,
        parent_id=parent_id,
        title=title,
        title_en=title_en,
        unit_type=unit_type,
        display_order=display_order,
        description=description,
        version=1,
        is_active=True,
    )
    db.add(unit)
    await _audit_log(db, admin_id, "syllabus_unit.create", "syllabus_unit", unit.id, {"title": title})
    await db.commit()

    return {"id": str(unit.id), "title": title, "unit_type": unit_type}


# ── Class Management ──────────────────────────────────────────

async def list_classes(db: AsyncSession) -> list[dict]:
    """List all classes."""
    result = await db.execute(
        select(Class).order_by(Class.grade, Class.name)
    )
    return [
        {
            "id": str(c.id),
            "grade": c.grade,
            "name": c.name,
            "academic_year": c.academic_year,
            "school_id": str(c.school_id) if c.school_id else None,
        }
        for c in result.scalars().all()
    ]


async def create_class(
    db: AsyncSession,
    admin_id: uuid.UUID,
    grade: int,
    name: Optional[str] = None,
    academic_year: str = "2026-27",
    school_id: Optional[uuid.UUID] = None,
) -> dict:
    """Create a new class."""
    cls = Class(
        grade=grade,
        name=name or f"Grade {grade}",
        academic_year=academic_year,
        school_id=school_id,
    )
    db.add(cls)
    await db.flush()
    await _audit_log(db, admin_id, "class.create", "class", cls.id, {"grade": grade})
    await db.commit()

    return {"id": str(cls.id), "grade": grade, "name": cls.name}


async def assign_teacher(
    db: AsyncSession,
    admin_id: uuid.UUID,
    teacher_id: uuid.UUID,
    class_id: uuid.UUID,
    subject_id: Optional[uuid.UUID] = None,
) -> dict:
    """Assign a teacher to a class (optionally for a specific subject)."""
    assignment = TeacherClassAssignment(
        teacher_id=teacher_id,
        class_id=class_id,
        subject_id=subject_id,
    )
    db.add(assignment)
    await db.flush()
    await _audit_log(
        db, admin_id, "teacher.assign", "teacher_class_assignment", assignment.id,
        {"teacher_id": str(teacher_id), "class_id": str(class_id)},
    )
    await db.commit()

    return {"id": str(assignment.id), "teacher_id": str(teacher_id), "class_id": str(class_id)}


async def get_teacher_assignments(db: AsyncSession) -> list[dict]:
    """List all teacher-class assignments."""
    result = await db.execute(
        select(TeacherClassAssignment, User, Class)
        .join(User, User.id == TeacherClassAssignment.teacher_id)
        .join(Class, Class.id == TeacherClassAssignment.class_id)
        .order_by(Class.grade)
    )
    return [
        {
            "id": str(a.id),
            "teacher_id": str(a.teacher_id),
            "teacher_name": u.full_name,
            "class_id": str(a.class_id),
            "class_name": f"Grade {c.grade}" + (f" - {c.name}" if c.name else ""),
            "subject_id": str(a.subject_id) if a.subject_id else None,
        }
        for a, u, c in result.all()
    ]
