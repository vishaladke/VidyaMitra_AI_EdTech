"""Syllabus and assessment schemas (stubs for Phase 1)."""
from pydantic import BaseModel
from typing import Optional
import uuid


class SubjectOut(BaseModel):
    id: uuid.UUID
    name: str
    name_en: Optional[str] = None
    grade: int
    board: str

    model_config = {"from_attributes": True}


class SyllabusUnitOut(BaseModel):
    id: uuid.UUID
    subject_id: uuid.UUID
    parent_id: Optional[uuid.UUID] = None
    title: str
    title_en: Optional[str] = None
    unit_type: str

    model_config = {"from_attributes": True}
