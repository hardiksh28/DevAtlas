"""Build Plan — request/response schemas.

`GeneratedPlanContent` is validated twice, same reasoning as
curriculum's LessonContent: once here as part of the API response
shape, and once by content_builder.parse_build_plan against the LLM's
raw JSON before anything is persisted.
"""

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

StepStatus = Literal["pending", "in_progress", "completed"]
StepBuildMode = Literal["guided", "generated"]


class GenerateBuildPlanRequest(BaseModel):
    # Optional supplementary detail beyond the project's own description
    # (already stored on Project) — lets a learner add context without
    # editing Project Settings first. The description itself remains the
    # primary, required input; see service.py's ProjectDescriptionMissingError.
    additional_context: str | None = Field(default=None, max_length=4000)

    @field_validator("additional_context")
    @classmethod
    def _blank_to_none(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None


class UpdateStepModeRequest(BaseModel):
    build_mode: StepBuildMode


class UpdateStepStatusRequest(BaseModel):
    status: Literal["in_progress", "completed"]


class RecommendedStackItem(BaseModel):
    name: str = Field(..., min_length=1)
    reason: str = Field(..., min_length=1)


class BuildPlanStepGenerated(BaseModel):
    title: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)


class GeneratedPlanContent(BaseModel):
    """The LLM's raw output shape — content_builder.parse_build_plan
    validates against this before service.py ever touches the DB."""

    summary: str = Field(..., min_length=1)
    recommended_stack: list[RecommendedStackItem] = Field(default_factory=list)
    steps: list[BuildPlanStepGenerated] = Field(default_factory=list)


class BuildPlanStepRead(BaseModel):
    id: uuid.UUID
    build_plan_id: uuid.UUID
    sequence_index: int
    title: str
    description: str
    status: StepStatus
    build_mode: StepBuildMode | None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_model(cls, step: "object") -> "BuildPlanStepRead":
        return cls(
            id=step.id,  # type: ignore[attr-defined]
            build_plan_id=step.build_plan_id,  # type: ignore[attr-defined]
            sequence_index=step.sequence_index,  # type: ignore[attr-defined]
            title=step.title,  # type: ignore[attr-defined]
            description=step.description,  # type: ignore[attr-defined]
            status=step.status,  # type: ignore[attr-defined]
            build_mode=step.build_mode,  # type: ignore[attr-defined]
            created_at=step.created_at,  # type: ignore[attr-defined]
            updated_at=step.updated_at,  # type: ignore[attr-defined]
        )


class BuildPlanRead(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    summary: str
    recommended_stack: list[RecommendedStackItem]
    version: int
    steps: list[BuildPlanStepRead]
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_model(cls, plan: "object") -> "BuildPlanRead":
        return cls(
            id=plan.id,  # type: ignore[attr-defined]
            project_id=plan.project_id,  # type: ignore[attr-defined]
            summary=plan.summary,  # type: ignore[attr-defined]
            recommended_stack=[
                RecommendedStackItem.model_validate(item)
                for item in plan.recommended_stack  # type: ignore[attr-defined]
            ],
            version=plan.version,  # type: ignore[attr-defined]
            steps=[BuildPlanStepRead.from_model(s) for s in plan.steps],  # type: ignore[attr-defined]
            created_at=plan.created_at,  # type: ignore[attr-defined]
            updated_at=plan.updated_at,  # type: ignore[attr-defined]
        )
