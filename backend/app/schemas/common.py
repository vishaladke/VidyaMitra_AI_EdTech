"""Common schema types: pagination, error responses."""
from pydantic import BaseModel
from typing import Optional, Any


class ErrorResponse(BaseModel):
    detail: str
    code: Optional[str] = None


class PaginatedResponse(BaseModel):
    items: list[Any]
    total: int
    page: int
    page_size: int
    pages: int


class MessageResponse(BaseModel):
    message: str
    data: Optional[dict] = None
