"""Visual Learning Engine — request/response schemas.

`DiagramOutput` is the LLM's structured-output contract (validated by
content_builder.parse_diagram_output), same two-schema split as
code_review's ReviewOutput vs ReviewDetailRead: what the model must
produce, and what the API actually returns (built from the persisted row).
"""

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

DiagramType = Literal["erd", "flowchart", "architecture", "state", "sequence", "component"]


class GenerateDiagramRequest(BaseModel):
    diagram_type: DiagramType
    # At least one of subject/milestone_id/code must be given — a diagram
    # needs *something* to visualize. `subject` alone covers "explain how
    # JWT auth works"; `code` alone covers "diagram this snippet";
    # `milestone_id` alone pulls the concept's own description. Any
    # combination is allowed and all given context is used.
    subject: str | None = Field(None, min_length=1, max_length=2000)
    milestone_id: uuid.UUID | None = None
    code: str | None = Field(None, min_length=1, max_length=20000)

    @model_validator(mode="after")
    def _has_a_subject(self) -> "GenerateDiagramRequest":
        if not self.subject and not self.milestone_id and not self.code:
            raise ValueError("one of subject, milestone_id, or code is required")
        return self


class DiagramOutput(BaseModel):
    """The LLM's full structured response shape."""

    title: str = Field(..., min_length=1, max_length=200)
    mermaid_source: str = Field(..., min_length=1)


class DiagramRead(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    milestone_id: uuid.UUID | None
    diagram_type: DiagramType
    title: str
    subject: str
    mermaid_source: str
    created_at: datetime

    @classmethod
    def from_model(cls, diagram: "object") -> "DiagramRead":
        return cls(
            id=diagram.id,  # type: ignore[attr-defined]
            project_id=diagram.project_id,  # type: ignore[attr-defined]
            milestone_id=diagram.milestone_id,  # type: ignore[attr-defined]
            diagram_type=diagram.diagram_type,  # type: ignore[attr-defined]
            title=diagram.title,  # type: ignore[attr-defined]
            subject=diagram.subject,  # type: ignore[attr-defined]
            mermaid_source=diagram.mermaid_source,  # type: ignore[attr-defined]
            created_at=diagram.created_at,  # type: ignore[attr-defined]
        )


class DiagramListResponse(BaseModel):
    items: list[DiagramRead]
    total: int
    limit: int
    offset: int
