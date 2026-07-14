"""AI-related schemas — chat requests, responses, conversation history, and cost breakdown."""
from pydantic import BaseModel, Field
from typing import Optional
import uuid
from datetime import datetime


class AIChatRequest(BaseModel):
    """Student sends a message to AI Guru."""
    message: str = Field(..., min_length=1, max_length=2000, description="Student's question in Marathi or English")
    conversation_id: Optional[uuid.UUID] = Field(None, description="Continue existing conversation, or None for new")
    subject_id: Optional[uuid.UUID] = Field(None, description="Subject context for scoping AI responses")


class AIChatResponse(BaseModel):
    """AI Guru's response to a student message."""
    answer: str
    conversation_id: str
    message_id: str
    cache_source: Optional[str] = None  # exact_redis | semantic_pgvector | faq_bank | live_llm
    cost_usd: float = 0.0
    cost_inr: float = 0.0
    is_flagged: bool = False
    response_time_ms: int = 0


class AIMessageOut(BaseModel):
    """A single message in a conversation."""
    id: uuid.UUID
    role: str  # 'student' or 'assistant'
    content: str
    topic_tag: Optional[str] = None
    is_voice: bool = False
    cache_source: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class AIConversationOut(BaseModel):
    """Conversation summary for list view."""
    id: uuid.UUID
    student_id: uuid.UUID
    subject_id: Optional[uuid.UUID] = None
    title: Optional[str] = None
    is_flagged: bool = False
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AIConversationDetail(BaseModel):
    """Conversation with messages."""
    conversation: AIConversationOut
    messages: list[AIMessageOut]


class AICostSummary(BaseModel):
    """Cost summary for Super Admin dashboard."""
    total_queries: int = 0
    cache_hits: int = 0
    cache_hit_rate: float = 0.0
    total_cost_usd: float = 0.0
    total_cost_inr: float = 0.0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
