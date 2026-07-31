"""Taxonomy & Concept Graph Service — models.

Owns the canonical concept taxonomy referenced by ARCHITECTURE.md
Section 7: `concepts` (canonical id, stack, severity, mastery criteria,
prerequisites) plus `concept_prerequisites` as the self-referencing edge
table the section calls for. Content is curated, versioned YAML under
`packages/taxonomy-data/concepts/` (see service.py's loader) — the LLM
never writes to these tables (ARCHITECTURE.md Section 3: "it is the only
thing allowed to evolve the taxonomy; the LLM never modifies it
directly").

Concept ids are natural keys (e.g. "python.async_await"), not surrogate
UUIDs, because the taxonomy-data YAML files themselves declare ids as
globally unique and append-only — a surrogate id would just be a second
identity for the same append-only string, not a real abstraction over it.
"""

from datetime import datetime

from sqlalchemy import CheckConstraint, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from sqlalchemy.types import JSON

from app.core.database import Base

# Same JSONB-on-Postgres/plain-JSON-elsewhere convention as every other
# module's models.py (see knowledge/models.py's docstring) — lets the
# SQLite test fallback engine create these tables too.
_JSONB_OR_JSON = JSON().with_variant(JSONB(), "postgresql")

SEVERITIES = ("foundational", "intermediate", "advanced")


class Concept(Base):
    """One canonical concept. No soft delete: taxonomy-data's own
    convention is "append-only, never rename-in-place" (see
    example-python-basics.yaml's header comment) — concepts are never
    deleted, only superseded by product decision, which is out of scope
    for this pass.
    """

    __tablename__ = "concepts"
    __table_args__ = (
        CheckConstraint(f"severity IN {SEVERITIES!r}", name="ck_concepts_severity"),
        Index("ix_concepts_stack_version", "stack", "stack_version"),
    )

    id: Mapped[str] = mapped_column(String(200), primary_key=True)
    stack: Mapped[str] = mapped_column(String(50))
    stack_version: Mapped[str] = mapped_column(String(20))
    severity: Mapped[str] = mapped_column(String(20))

    mastery_criteria: Mapped[list] = mapped_column(_JSONB_OR_JSON, server_default="[]")
    common_misconceptions: Mapped[list] = mapped_column(_JSONB_OR_JSON, server_default="[]")
    docs: Mapped[list] = mapped_column(_JSONB_OR_JSON, server_default="[]")

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now())

    prerequisite_edges: Mapped[list["ConceptPrerequisite"]] = relationship(
        back_populates="concept",
        foreign_keys="ConceptPrerequisite.concept_id",
        cascade="all, delete-orphan",
    )


class ConceptPrerequisite(Base):
    """Self-referencing edge: `concept_id` requires `prerequisite_id`.
    Composite PK — a given (concept, prerequisite) pair can only exist
    once, and the pair itself is the whole identity of the row (no
    surrogate id needed, matching RecentProject's composite-PK
    reasoning in projects/models.py).
    """

    __tablename__ = "concept_prerequisites"
    __table_args__ = (Index("ix_concept_prerequisites_prerequisite", "prerequisite_id"),)

    concept_id: Mapped[str] = mapped_column(
        ForeignKey("concepts.id", ondelete="CASCADE"), primary_key=True
    )
    prerequisite_id: Mapped[str] = mapped_column(
        ForeignKey("concepts.id", ondelete="CASCADE"), primary_key=True
    )

    concept: Mapped["Concept"] = relationship(
        back_populates="prerequisite_edges", foreign_keys=[concept_id]
    )
