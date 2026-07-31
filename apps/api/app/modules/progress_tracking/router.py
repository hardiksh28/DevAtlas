"""Progress & Weakness Tracking Service — router.

Three routers: `router` (`/v1/progress-tracking`) stays the pre-existing
stub. `quiz_router` (`/v1/projects/{project_id}/progress`) is
project-scoped (quiz submission needs a project's milestone). `progress_router`
(`/v1/progress`) is user-scoped, not project-scoped — mastery follows the
learner across every project (ARCHITECTURE.md Section 3), so it reads
`current_user` directly rather than depending on `get_owned_project`,
same pattern as projects.router's own `dashboard_router`.

Thin HTTP layer only: every handler extracts what it needs, calls
service.py, and shapes the result via a schemas.py adapter.
"""

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.models import User
from app.modules.progress_tracking import service
from app.modules.progress_tracking.schemas import (
    DashboardResponse,
    MasteryProfileListResponse,
    MasteryProfileRead,
    QuizAttemptRead,
    QuizSubmitRequest,
)
from app.modules.projects.dependencies import get_owned_project
from app.modules.projects.models import Project

router = APIRouter(prefix="/v1/progress-tracking", tags=["Progress & Weakness Tracking"])

quiz_router = APIRouter(
    prefix="/v1/projects/{project_id}/progress", tags=["Progress & Weakness Tracking — Quiz"]
)

progress_router = APIRouter(prefix="/v1/progress", tags=["Progress & Weakness Tracking"])


@quiz_router.post("/milestones/{milestone_id}/quiz", response_model=QuizAttemptRead)
async def submit_quiz(
    milestone_id: uuid.UUID,
    payload: QuizSubmitRequest,
    project: Project = Depends(get_owned_project),
    db: AsyncSession = Depends(get_db),
) -> QuizAttemptRead:
    attempt = await service.submit_quiz(
        db,
        user_id=project.owner_id,
        project_id=project.id,
        milestone_id=milestone_id,
        answers=payload.answers,
    )
    return QuizAttemptRead.from_model(attempt)


@progress_router.get("/mastery", response_model=MasteryProfileListResponse)
async def list_mastery(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MasteryProfileListResponse:
    profiles = await service.list_mastery_profiles(db, current_user.id)
    return MasteryProfileListResponse(items=[MasteryProfileRead.from_model(p) for p in profiles])


@progress_router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DashboardResponse:
    data = await service.get_dashboard(db, current_user.id)
    return DashboardResponse(
        streak=data["streak"],
        milestones_completed=data["milestones_completed"],
        total_time_spent_seconds=data["total_time_spent_seconds"],
        quizzes_taken=data["quizzes_taken"],
        average_quiz_score_pct=data["average_quiz_score_pct"],
        code_reviews_submitted=data["code_reviews_submitted"],
        average_review_score=data["average_review_score"],
        weak_concepts=[MasteryProfileRead.from_model(p) for p in data["weak_concepts"]],
        strengths=[MasteryProfileRead.from_model(p) for p in data["strengths"]],
        activity_by_day=data["activity_by_day"],
    )
