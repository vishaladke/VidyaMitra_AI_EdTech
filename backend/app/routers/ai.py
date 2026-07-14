"""AI router — chat endpoint, conversation history, and cost queries.

All endpoints require student role (except cost summary which is super_admin only).
"""
import uuid
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, require_role
from app.models.user import UserRole
from app.schemas.ai import (
    AIChatRequest,
    AIChatResponse,
    AIConversationOut,
    AIConversationDetail,
    AIMessageOut,
)
from app.services.ai_service import (
    process_student_message,
    get_student_conversations,
    get_conversation_messages,
)

router = APIRouter(prefix="/api/ai", tags=["AI Guru"])


@router.post("/chat", response_model=AIChatResponse)
async def send_chat_message(
    body: AIChatRequest,
    user=Depends(require_role(UserRole.STUDENT)),
    db: AsyncSession = Depends(get_db),
):
    """Send a message to AI Guru and get a response.
    
    The response goes through the cache-first flow:
    1. Redis exact-match cache
    2. pgvector semantic cache (similarity > 0.92)
    3. FAQ bank
    4. Live Claude API call
    
    Every response path logs cost to the Super Admin AI dashboard.
    """
    result = await process_student_message(
        db=db,
        student_id=user.id,
        message=body.message,
        conversation_id=body.conversation_id,
        subject_id=body.subject_id,
    )
    return AIChatResponse(**result)


@router.get("/conversations", response_model=list[AIConversationOut])
async def list_conversations(
    limit: int = 20,
    offset: int = 0,
    user=Depends(require_role(UserRole.STUDENT)),
    db: AsyncSession = Depends(get_db),
):
    """List the student's AI Guru conversations."""
    conversations = await get_student_conversations(db, user.id, limit, offset)
    return conversations


@router.get("/conversations/{conversation_id}", response_model=AIConversationDetail)
async def get_conversation(
    conversation_id: uuid.UUID,
    user=Depends(require_role(UserRole.STUDENT)),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific conversation with all messages."""
    messages = await get_conversation_messages(db, conversation_id, user.id)
    from app.models.ai import AIConversation
    conv = await db.get(AIConversation, conversation_id)
    
    return AIConversationDetail(
        conversation=AIConversationOut.model_validate(conv),
        messages=[AIMessageOut.model_validate(m) for m in messages],
    )
