"""User-related schemas."""
from pydantic import BaseModel
from typing import Optional
import uuid
from datetime import datetime


class StudentProfileCreate(BaseModel):
    grade: int
    board: str = "maharashtra_state"
    medium: str = "marathi"
    city: str = "Solapur"


class UserOut(BaseModel):
    id: uuid.UUID
    phone: str
    email: Optional[str] = None
    role: str
    full_name: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
