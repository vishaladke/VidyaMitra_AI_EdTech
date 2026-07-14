"""Assessment schemas (stubs for Phase 1)."""
from pydantic import BaseModel
from typing import Optional
import uuid


class AssignmentOut(BaseModel):
    id: uuid.UUID
    title: str
    assignment_type: str
    subject_id: uuid.UUID

    model_config = {"from_attributes": True}
