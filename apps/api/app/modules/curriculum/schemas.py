"""Curriculum Engine — request/response schemas.

`LessonContent` (and its `Exercise`/`QuizQuestion` children) is the one
schema in this module validated *twice*: once here as the API response
shape, and once by content_builder.parse_milestone_content against the
LLM's raw JSON output before it's ever persisted — so a malformed
narration response is caught at generation time, not surfaced to a
client as a broken response body.
"""

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

ExperienceLevel = Literal["beginner", "intermediate", "advanced"]
MilestoneStatus = Literal["locked", "available", "in_progress", "completed"]


class GenerateRoadmapRequest(BaseModel):
    stack: str = Field(..., min_length=1, max_length=50)
    stack_version: str = Field(..., min_length=1, max_length=20)
    experience_level: ExperienceLevel

    @field_validator("stack")
    @classmethod
    def _not_blank(cls, value: str) -> str:
        stripped = value.strip().lower()
        if not stripped:
            raise ValueError("stack cannot be blank")
        return stripped


class UpdateMilestoneStatusRequest(BaseModel):
    # Only forward, learner-driven transitions are client-settable;
    # `locked`/`available` are server-computed (see service.py's
    # update_milestone_status) — never accepted here.
    status: Literal["in_progress", "completed"]


class Exercise(BaseModel):
    prompt: str = Field(..., min_length=1)
    hint: str | None = None


class QuizQuestion(BaseModel):
    question: str = Field(..., min_length=1)
    options: list[str] = Field(..., min_length=2, max_length=6)
    correct_index: int = Field(..., ge=0)
    explanation: str = ""

    @model_validator(mode="after")
    def _correct_index_in_range(self) -> "QuizQuestion":
        if self.correct_index >= len(self.options):
            raise ValueError("correct_index must index into options")
        return self


class LessonContent(BaseModel):
    explanation: str
    key_points: list[str] = Field(default_factory=list)
    exercises: list[Exercise] = Field(default_factory=list)
    quiz: list[QuizQuestion] = Field(default_factory=list)


class MilestoneRead(BaseModel):
    id: uuid.UUID
    roadmap_id: uuid.UUID
    concept_id: str
    sequence_index: int
    status: MilestoneStatus
    title: str
    estimated_minutes: int
    has_content: bool
    content_version: int
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_model(cls, milestone: "object") -> "MilestoneRead":
        return cls(
            id=milestone.id,  # type: ignore[attr-defined]
            roadmap_id=milestone.roadmap_id,  # type: ignore[attr-defined]
            concept_id=milestone.concept_id,  # type: ignore[attr-defined]
            sequence_index=milestone.sequence_index,  # type: ignore[attr-defined]
            status=milestone.status,  # type: ignore[attr-defined]
            title=milestone.title,  # type: ignore[attr-defined]
            estimated_minutes=milestone.estimated_minutes,  # type: ignore[attr-defined]
            has_content=milestone.lesson_content is not None,  # type: ignore[attr-defined]
            content_version=milestone.content_version,  # type: ignore[attr-defined]
            started_at=milestone.started_at,  # type: ignore[attr-defined]
            completed_at=milestone.completed_at,  # type: ignore[attr-defined]
            created_at=milestone.created_at,  # type: ignore[attr-defined]
            updated_at=milestone.updated_at,  # type: ignore[attr-defined]
        )


class MilestoneDetailRead(MilestoneRead):
    lesson_content: LessonContent | None

    @classmethod
    def from_model(cls, milestone: "object") -> "MilestoneDetailRead":
        base = MilestoneRead.from_model(milestone)
        raw_content = milestone.lesson_content  # type: ignore[attr-defined]
        return cls(
            **base.model_dump(),
            lesson_content=LessonContent.model_validate(raw_content) if raw_content else None,
        )


class RoadmapRead(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    stack: str
    stack_version: str
    experience_level: ExperienceLevel
    status: Literal["active", "archived"]
    version: int
    estimated_total_minutes: int
    milestones: list[MilestoneRead]
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_model(cls, roadmap: "object") -> "RoadmapRead":
        return cls(
            id=roadmap.id,  # type: ignore[attr-defined]
            project_id=roadmap.project_id,  # type: ignore[attr-defined]
            stack=roadmap.stack,  # type: ignore[attr-defined]
            stack_version=roadmap.stack_version,  # type: ignore[attr-defined]
            experience_level=roadmap.experience_level,  # type: ignore[attr-defined]
            status=roadmap.status,  # type: ignore[attr-defined]
            version=roadmap.version,  # type: ignore[attr-defined]
            estimated_total_minutes=roadmap.estimated_total_minutes,  # type: ignore[attr-defined]
            milestones=[MilestoneRead.from_model(m) for m in roadmap.milestones],  # type: ignore[attr-defined]
            created_at=roadmap.created_at,  # type: ignore[attr-defined]
            updated_at=roadmap.updated_at,  # type: ignore[attr-defined]
        )
