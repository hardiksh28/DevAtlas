"""Visual Learning Engine — models.

`Diagram` is one generated visual explanation: a Mermaid source string plus
the request that produced it. Same "immutable history row" shape as
`CodeReview` (see code_review/models.py's docstring) rather than an
in-place-editable/versioned row like `Milestone.lesson_content` — a diagram
is cheap to regenerate and a learner comparing "what changed" benefits from
browsing prior attempts, same reasoning as review history.

Rendering never happens on the backend: `mermaid_source` is plain text,
rendered to SVG client-side by the `mermaid` package (see
apps/web/src/components/workspace/MermaidDiagram.tsx). Storing rendered SVG
or a rasterized image was considered and rejected — it would require a
server-side rendering pipeline (headless browser or a service like Kroki)
for a text format the browser already renders natively, and would need
re-rendering on every theme change anyway.
"""

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.core.database import Base

DIAGRAM_TYPES = ("erd", "flowchart", "architecture", "state", "sequence", "component")


class Diagram(Base):
    """One generated diagram. `subject` is the free-text or milestone-derived
    description the diagram was generated from — kept alongside the output
    so a learner (or a future "regenerate with tweaks" flow) can see what
    prompted it without re-deriving it from `milestone_id` alone (which may
    itself later be null if the milestone is removed — SET NULL, matching
    CodeReview.milestone_id).
    """

    __tablename__ = "diagrams"
    __table_args__ = (
        CheckConstraint(f"diagram_type IN {DIAGRAM_TYPES!r}", name="ck_diagrams_diagram_type"),
        Index("ix_diagrams_project_created", "project_id", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    milestone_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("milestones.id", ondelete="SET NULL"), default=None
    )

    diagram_type: Mapped[str] = mapped_column(String(20))
    title: Mapped[str] = mapped_column(String(200))
    subject: Mapped[str] = mapped_column(String)
    mermaid_source: Mapped[str] = mapped_column(String)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
