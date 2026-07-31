"""Progress & Weakness Tracking Service — models.

`MasteryProfile` is ARCHITECTURE.md Section 3's "one evolving record per
(user, concept) pair" — cross-project by design (`user_id`, not
`project_id`): a learner's mastery of `python.async_await` follows them
into their next project, it isn't reset per workspace. `MasteryEvidence`
is its append-only supporting history (never edited — same "historical
record" reasoning as mentoring's `messages`), one row per signal that
moved the confidence score.

`QuizAttempt` and `ActivityEvent` are the two inputs the mastery engine
and the analytics dashboard both read: quiz scoring needed *some* table
(nothing previously persisted a quiz submission — `Milestone.lesson_content`
only ever stored the generated questions) and `ActivityEvent` is one
generic append-only log rather than five bespoke tables — every tracked
signal in the Step-12 brief (lessons, quizzes, reviews, streaks, time
spent) is one `event_type` + a JSONB payload, so streak/time-spent
queries scan one indexed table instead of a UNION across five.
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

# Reversible state machine per ARCHITECTURE.md Section 3: "Detected →
# Practicing → Improving → Mastered → Monitor". `monitor` is reachable
# only by regressing from `mastered` (service._next_resolution_state) —
# it means "previously mastered, now flagged for review", not a fifth
# rung on the way up.
RESOLUTION_STATES = ("detected", "practicing", "improving", "mastered", "monitor")
EVIDENCE_SOURCES = ("milestone", "quiz", "code_review")
EVIDENCE_SIGNALS = ("positive", "negative")
ACTIVITY_TYPES = ("milestone_completed", "quiz_submitted", "code_review_submitted")


class MasteryProfile(Base):
    __tablename__ = "mastery_profiles"
    __table_args__ = (
        CheckConstraint(f"resolution_state IN {RESOLUTION_STATES!r}", name="ck_mastery_profiles_state"),
        CheckConstraint(
            "confidence_score >= 0 AND confidence_score <= 1", name="ck_mastery_profiles_confidence_range"
        ),
        UniqueConstraint("user_id", "concept_id", name="uq_mastery_profiles_user_concept"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    # RESTRICT, matching curriculum.Milestone.concept_id — a concept is
    # append-only and must never be deletable out from under a profile.
    concept_id: Mapped[str] = mapped_column(ForeignKey("concepts.id", ondelete="RESTRICT"))

    confidence_score: Mapped[float] = mapped_column(server_default="0")
    resolution_state: Mapped[str] = mapped_column(String(20), server_default="detected")

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now())

    evidence: Mapped[list["MasteryEvidence"]] = relationship(
        back_populates="profile", cascade="all, delete-orphan", order_by="MasteryEvidence.created_at"
    )


class MasteryEvidence(Base):
    """One signal that moved a profile's confidence score. Append-only —
    a mastery profile's history is meant to be reconstructable, not just
    its current snapshot."""

    __tablename__ = "mastery_evidence"
    __table_args__ = (
        CheckConstraint(f"source IN {EVIDENCE_SOURCES!r}", name="ck_mastery_evidence_source"),
        CheckConstraint(f"signal IN {EVIDENCE_SIGNALS!r}", name="ck_mastery_evidence_signal"),
        Index("ix_mastery_evidence_profile_created", "profile_id", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    profile_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("mastery_profiles.id", ondelete="CASCADE"))

    source: Mapped[str] = mapped_column(String(20))
    signal: Mapped[str] = mapped_column(String(20))
    # Magnitude applied to confidence_score at the time (service._apply_confidence)
    # — kept so the history can be audited/replayed without re-deriving it.
    weight: Mapped[float] = mapped_column()
    note: Mapped[str | None] = mapped_column(String, default=None)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    profile: Mapped["MasteryProfile"] = relationship(back_populates="evidence")


class QuizAttempt(Base):
    """One scored submission of a milestone's generated quiz. Retakes are
    allowed (no unique constraint) — each attempt is its own evidence
    signal, and the dashboard reads the most recent one per milestone."""

    __tablename__ = "quiz_attempts"
    __table_args__ = (Index("ix_quiz_attempts_user_milestone", "user_id", "milestone_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    milestone_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("milestones.id", ondelete="CASCADE"))

    score: Mapped[int] = mapped_column(Integer)
    total: Mapped[int] = mapped_column(Integer)
    # Selected option index per question, same order as
    # Milestone.lesson_content["quiz"] — free-form JSON, not a child
    # table, since it's write-once and only ever read back whole.
    answers: Mapped[list] = mapped_column(_JSONB_OR_JSON, server_default="[]")

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class ActivityEvent(Base):
    """One append-only fact: this user did this kind of thing at this
    time. Powers streaks, time-spent, and coding-activity analytics from
    a single indexed table instead of a bespoke counter per metric."""

    __tablename__ = "activity_events"
    __table_args__ = (
        CheckConstraint(f"event_type IN {ACTIVITY_TYPES!r}", name="ck_activity_events_type"),
        Index("ix_activity_events_user_occurred", "user_id", "occurred_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    # SET NULL, not CASCADE: an activity event is a historical fact about
    # the user first, the project second — deleting a project shouldn't
    # erase that the learner was active on that day.
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("projects.id", ondelete="SET NULL"), default=None
    )

    event_type: Mapped[str] = mapped_column(String(30))
    occurred_at: Mapped[datetime] = mapped_column(server_default=func.now())
    duration_seconds: Mapped[int | None] = mapped_column(Integer, default=None)
    event_metadata: Mapped[dict] = mapped_column(_JSONB_OR_JSON, server_default="{}")
