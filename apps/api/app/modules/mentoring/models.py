"""Mentoring / Hint Ladder Engine — models.

One `Conversation` per project (like `Roadmap`, curriculum/models.py) —
a persistent mentor thread for the project workspace, not fragmented
per concept. `Message.milestone_id` optionally anchors a single turn to
the concept being discussed, without requiring one.

No soft delete: an append-only transcript, same reasoning as
`evidence_log` (ARCHITECTURE.md Section 7) — a mentor conversation is a
historical record, never edited or removed.
"""

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from sqlalchemy.types import JSON

from app.core.database import Base

_JSONB_OR_JSON = JSON().with_variant(JSONB(), "postgresql")


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), unique=True
    )

    # Rolling compacted memory of every message before `summarized_up_to`
    # — see mentoring/service.py's `_maybe_compact_history` and
    # docs/architecture/mentor-engine-v1.md's memory-strategy section.
    summary: Mapped[str | None] = mapped_column(default=None)
    summarized_up_to: Mapped[datetime | None] = mapped_column(default=None)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now())

    messages: Mapped[list["Message"]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.created_at",
    )


class Message(Base):
    __tablename__ = "messages"
    __table_args__ = (
        CheckConstraint("role IN ('user', 'assistant')", name="ck_messages_role"),
        Index("ix_messages_conversation_created", "conversation_id", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE")
    )
    # Optional concept anchor — lets a turn ground itself in a specific
    # milestone's curated mastery criteria/misconceptions (taxonomy.Concept)
    # without requiring every mentor message to be milestone-scoped.
    milestone_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("milestones.id", ondelete="SET NULL"), default=None
    )

    role: Mapped[str] = mapped_column(String(20))
    content: Mapped[str] = mapped_column(String)
    # Assistant messages only — always [] for role="user". Concept ids
    # (if milestone-anchored) or free-text descriptions (if not) the
    # model flagged as a misconception in this reply.
    detected_misconceptions: Mapped[list] = mapped_column(_JSONB_OR_JSON, server_default="[]")

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    conversation: Mapped["Conversation"] = relationship(back_populates="messages")
