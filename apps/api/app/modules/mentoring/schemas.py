"""Mentoring Engine — request/response schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class SendMessageRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=8000)
    milestone_id: uuid.UUID | None = None

    @field_validator("content")
    @classmethod
    def _not_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("content cannot be blank")
        return stripped


class MentorReply(BaseModel):
    """The LLM's structured response shape — validated by
    content_builder.parse_mentor_reply before it's ever persisted or
    returned to a client."""

    reply: str
    misconceptions_detected: list[str] = Field(default_factory=list)


class MessageRead(BaseModel):
    id: uuid.UUID
    role: str
    content: str
    milestone_id: uuid.UUID | None
    misconceptions_detected: list[str]
    created_at: datetime

    @classmethod
    def from_model(cls, message: "object") -> "MessageRead":
        return cls(
            id=message.id,  # type: ignore[attr-defined]
            role=message.role,  # type: ignore[attr-defined]
            content=message.content,  # type: ignore[attr-defined]
            milestone_id=message.milestone_id,  # type: ignore[attr-defined]
            misconceptions_detected=message.detected_misconceptions,  # type: ignore[attr-defined]
            created_at=message.created_at,  # type: ignore[attr-defined]
        )


class SendMessageResponse(BaseModel):
    user_message: MessageRead
    reply: MessageRead


class MessageListResponse(BaseModel):
    items: list[MessageRead]
    total: int
    limit: int
    offset: int
