"""Curriculum Engine — models.

`Roadmap` (one per project — regeneration mutates it in place, see
service.py) and `Milestone` (one per selected concept, ordered by
`sequence_index`). No soft delete on either: a roadmap/milestone is
never "deleted" in the `ProjectDocument` sense — it's either archived
(roadmap-level, a rare full-stack-change path) or diffed away by
regeneration (milestone-level, see sequencing.diff_milestones), and
diffed-away rows that were never started are hard-deleted outright
(they were never shown to the learner as real progress, so there's
nothing to recover).
"""

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from sqlalchemy.types import JSON

from app.core.database import Base

_JSONB_OR_JSON = JSON().with_variant(JSONB(), "postgresql")

EXPERIENCE_LEVELS = ("beginner", "intermediate", "advanced")
ROADMAP_STATUSES = ("active", "archived")
MILESTONE_STATUSES = ("locked", "available", "in_progress", "completed")


class Roadmap(Base):
    """One roadmap per project. `version` increments on every
    regeneration so the client can show "this roadmap changed" without
    diffing the milestone list itself.
    """

    __tablename__ = "roadmaps"
    __table_args__ = (
        CheckConstraint(f"experience_level IN {EXPERIENCE_LEVELS!r}", name="ck_roadmaps_experience_level"),
        CheckConstraint(f"status IN {ROADMAP_STATUSES!r}", name="ck_roadmaps_status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), unique=True
    )

    stack: Mapped[str] = mapped_column(String(50))
    stack_version: Mapped[str] = mapped_column(String(20))
    experience_level: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(20), server_default="active")

    # Bumped every generate_or_regenerate_roadmap call — surfaced to the
    # client, never read by any query, purely a change-detection signal.
    version: Mapped[int] = mapped_column(Integer, server_default="1")
    estimated_total_minutes: Mapped[int] = mapped_column(Integer, server_default="0")

    # Which project_documents (if any) fed the RAG context used for
    # narration — provenance only, not read at generation time.
    source_document_ids: Mapped[list] = mapped_column(_JSONB_OR_JSON, server_default="[]")

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now())

    milestones: Mapped[list["Milestone"]] = relationship(
        back_populates="roadmap",
        cascade="all, delete-orphan",
        order_by="Milestone.sequence_index",
    )


class Milestone(Base):
    """One concept's slot in a roadmap. `UniqueConstraint(roadmap_id,
    concept_id)` is the structural duplicate-lesson guard: a concept can
    appear at most once per roadmap, by construction, not by convention.
    """

    __tablename__ = "milestones"
    __table_args__ = (
        CheckConstraint(f"status IN {MILESTONE_STATUSES!r}", name="ck_milestones_status"),
        UniqueConstraint("roadmap_id", "concept_id", name="uq_milestones_roadmap_concept"),
        Index("ix_milestones_roadmap_sequence", "roadmap_id", "sequence_index"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    roadmap_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("roadmaps.id", ondelete="CASCADE"))
    # RESTRICT, not CASCADE: a concept is append-only (see taxonomy's
    # Concept docstring) and should never be deletable out from under a
    # milestone that references it — if that ever needs to change, it's
    # a deliberate migration, not an accidental cascade.
    concept_id: Mapped[str] = mapped_column(ForeignKey("concepts.id", ondelete="RESTRICT"))

    sequence_index: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20), server_default="locked")
    title: Mapped[str] = mapped_column(String(200))
    estimated_minutes: Mapped[int] = mapped_column(Integer)

    # {explanation, key_points[], exercises[], quiz[]} — null until
    # generate_milestone_content's first successful call. See
    # curriculum/schemas.py's LessonContent for the validated shape.
    lesson_content: Mapped[dict | None] = mapped_column(_JSONB_OR_JSON, default=None)
    content_version: Mapped[int] = mapped_column(Integer, server_default="0")
    content_generated_at: Mapped[datetime | None] = mapped_column(default=None)

    started_at: Mapped[datetime | None] = mapped_column(default=None)
    completed_at: Mapped[datetime | None] = mapped_column(default=None)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now())

    roadmap: Mapped["Roadmap"] = relationship(back_populates="milestones")
