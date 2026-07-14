"""Syllabus service — subject listing, syllabus unit tree, and progress tracking."""
import uuid
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.syllabus import Subject, SyllabusUnit
from app.models.ai import AIConversation


async def get_subjects(
    db: AsyncSession,
    grade: int,
    board: str = "maharashtra_state",
) -> list[Subject]:
    """Get active subjects for a grade and board."""
    result = await db.execute(
        select(Subject)
        .where(
            Subject.grade == grade,
            Subject.board == board,
            Subject.is_active == True,
        )
        .order_by(Subject.display_order)
    )
    return list(result.scalars().all())


async def get_syllabus_tree(
    db: AsyncSession,
    subject_id: uuid.UUID,
) -> list[dict]:
    """Get the full chapter/topic tree for a subject.
    
    Returns a nested list:
    [
        {
            "id": ..., "title": ..., "unit_type": "chapter", 
            "children": [
                {"id": ..., "title": ..., "unit_type": "topic", "children": []}
            ]
        }
    ]
    """
    result = await db.execute(
        select(SyllabusUnit)
        .where(
            SyllabusUnit.subject_id == subject_id,
            SyllabusUnit.is_active == True,
        )
        .order_by(SyllabusUnit.display_order)
    )
    units = list(result.scalars().all())

    # Build tree from flat list
    units_by_id = {u.id: u for u in units}
    tree: list[dict] = []
    children_map: dict[uuid.UUID, list[dict]] = {}

    for unit in units:
        node = {
            "id": str(unit.id),
            "title": unit.title,
            "title_en": unit.title_en,
            "unit_type": unit.unit_type,
            "description": unit.description,
            "pdf_url": unit.pdf_url,
            "children": [],
        }
        children_map[unit.id] = node["children"]

        if unit.parent_id and unit.parent_id in children_map:
            children_map[unit.parent_id].append(node)
        else:
            tree.append(node)

    return tree


async def get_unit_detail(
    db: AsyncSession,
    unit_id: uuid.UUID,
) -> Optional[dict]:
    """Get a single syllabus unit with its children."""
    unit = await db.get(SyllabusUnit, unit_id)
    if not unit:
        return None

    result = await db.execute(
        select(SyllabusUnit)
        .where(
            SyllabusUnit.parent_id == unit_id,
            SyllabusUnit.is_active == True,
        )
        .order_by(SyllabusUnit.display_order)
    )
    children = list(result.scalars().all())

    return {
        "id": str(unit.id),
        "title": unit.title,
        "title_en": unit.title_en,
        "unit_type": unit.unit_type,
        "description": unit.description,
        "pdf_url": unit.pdf_url,
        "children": [
            {
                "id": str(c.id),
                "title": c.title,
                "title_en": c.title_en,
                "unit_type": c.unit_type,
                "description": c.description,
            }
            for c in children
        ],
    }


async def get_student_progress(
    db: AsyncSession,
    student_id: uuid.UUID,
    subject_id: uuid.UUID,
) -> dict:
    """Calculate student's progress for a subject based on AI conversations.
    
    Returns: {total_units, studied_units, completion_pct}
    """
    # Count total active units
    total_result = await db.execute(
        select(func.count(SyllabusUnit.id))
        .where(
            SyllabusUnit.subject_id == subject_id,
            SyllabusUnit.is_active == True,
        )
    )
    total_units = total_result.scalar() or 0

    # Count unique conversations for this subject
    conv_result = await db.execute(
        select(func.count(AIConversation.id))
        .where(
            AIConversation.student_id == student_id,
            AIConversation.subject_id == subject_id,
        )
    )
    studied = conv_result.scalar() or 0

    completion = round((studied / total_units * 100), 1) if total_units > 0 else 0.0

    return {
        "total_units": total_units,
        "studied_units": min(studied, total_units),
        "completion_pct": min(completion, 100.0),
    }
