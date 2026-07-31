"""Progress & Weakness Tracking Service — request/response schemas."""

import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field

ResolutionState = Literal["detected", "practicing", "improving", "mastered", "monitor"]


class QuizSubmitRequest(BaseModel):
    # Selected option index per question, same order as the milestone's
    # generated quiz — service.submit_quiz validates the length matches.
    answers: list[int] = Field(..., min_length=1)


class QuizAttemptRead(BaseModel):
    id: uuid.UUID
    milestone_id: uuid.UUID
    score: int
    total: int
    answers: list[int]
    created_at: datetime

    @classmethod
    def from_model(cls, attempt: "object") -> "QuizAttemptRead":
        return cls(
            id=attempt.id,  # type: ignore[attr-defined]
            milestone_id=attempt.milestone_id,  # type: ignore[attr-defined]
            score=attempt.score,  # type: ignore[attr-defined]
            total=attempt.total,  # type: ignore[attr-defined]
            answers=attempt.answers,  # type: ignore[attr-defined]
            created_at=attempt.created_at,  # type: ignore[attr-defined]
        )


class MasteryProfileRead(BaseModel):
    concept_id: str
    confidence_score: float
    resolution_state: ResolutionState
    updated_at: datetime

    @classmethod
    def from_model(cls, profile: "object") -> "MasteryProfileRead":
        return cls(
            concept_id=profile.concept_id,  # type: ignore[attr-defined]
            confidence_score=round(profile.confidence_score, 4),  # type: ignore[attr-defined]
            resolution_state=profile.resolution_state,  # type: ignore[attr-defined]
            updated_at=profile.updated_at,  # type: ignore[attr-defined]
        )


class MasteryProfileListResponse(BaseModel):
    items: list[MasteryProfileRead]


class ActivityDayRead(BaseModel):
    """One point on the activity chart — a day and how much happened on it."""

    activity_date: date
    event_count: int
    duration_seconds: int


class StreakRead(BaseModel):
    current_streak_days: int
    longest_streak_days: int
    last_active_date: date | None


class DashboardResponse(BaseModel):
    """The one aggregate read backing the analytics dashboard — composes
    mastery, quiz, review, and activity data into a single page-load
    response, same "one endpoint for one page" reasoning as
    projects.schemas.DashboardResponse."""

    streak: StreakRead
    milestones_completed: int
    total_time_spent_seconds: int
    quizzes_taken: int
    average_quiz_score_pct: float | None
    code_reviews_submitted: int
    average_review_score: float | None
    weak_concepts: list[MasteryProfileRead]
    strengths: list[MasteryProfileRead]
    activity_by_day: list[ActivityDayRead]
