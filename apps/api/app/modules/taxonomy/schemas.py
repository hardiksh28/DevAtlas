"""Taxonomy & Concept Graph Service — request/response schemas."""

from datetime import datetime

from pydantic import BaseModel


class ConceptRead(BaseModel):
    id: str
    stack: str
    stack_version: str
    severity: str
    prerequisites: list[str]
    mastery_criteria: list[str]
    common_misconceptions: list[str]
    docs: list[str]
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_model(cls, concept: "object", prerequisites: list[str]) -> "ConceptRead":
        return cls(
            id=concept.id,  # type: ignore[attr-defined]
            stack=concept.stack,  # type: ignore[attr-defined]
            stack_version=concept.stack_version,  # type: ignore[attr-defined]
            severity=concept.severity,  # type: ignore[attr-defined]
            prerequisites=prerequisites,
            mastery_criteria=concept.mastery_criteria,  # type: ignore[attr-defined]
            common_misconceptions=concept.common_misconceptions,  # type: ignore[attr-defined]
            docs=concept.docs,  # type: ignore[attr-defined]
            created_at=concept.created_at,  # type: ignore[attr-defined]
            updated_at=concept.updated_at,  # type: ignore[attr-defined]
        )


class ConceptListResponse(BaseModel):
    items: list[ConceptRead]


class StackSummary(BaseModel):
    stack: str
    stack_version: str
    concept_count: int


class StackListResponse(BaseModel):
    items: list[StackSummary]
