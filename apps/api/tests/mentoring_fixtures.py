"""Shared test helpers for seeding mentoring data directly via the ORM.
Not a test file itself (no `test_` prefix), mirroring
tests/knowledge_fixtures.py."""

import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.mentoring.models import Conversation, Message


async def create_conversation(db: AsyncSession, project_id: uuid.UUID) -> Conversation:
    conversation = Conversation(project_id=project_id)
    db.add(conversation)
    await db.flush()
    return conversation


async def create_message(
    db: AsyncSession,
    conversation: Conversation,
    *,
    role: str = "user",
    content: str = "hello",
    milestone_id: uuid.UUID | None = None,
    detected_misconceptions: list[str] | None = None,
    created_at: datetime | None = None,
) -> Message:
    message = Message(
        conversation_id=conversation.id,
        milestone_id=milestone_id,
        role=role,
        content=content,
        detected_misconceptions=detected_misconceptions or [],
    )
    if created_at is not None:
        message.created_at = created_at
    db.add(message)
    await db.flush()
    return message
