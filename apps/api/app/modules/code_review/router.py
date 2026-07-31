"""Code Review Engine — router.

Three linked artifacts per review (ARCHITECTURE.md Section 3): inline
comments, a holistic summary + score, and review history. The
interactive discussion thread per comment is deferred — see
models.py's docstring for why.

Two routers, same split as mentoring's own router.py: `router`
(`/v1/code-review`) stays a pre-existing stub with no routes of its
own. `review_router` (`/v1/projects/{project_id}/reviews`) is the real
surface, nested under its owning project.
"""

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.code_review import service
from app.modules.code_review.schemas import (
    ReviewDetailRead,
    ReviewListResponse,
    ReviewSummaryRead,
    SubmitReviewRequest,
)
from app.modules.cost_control.limits import llm_rate_limit
from app.modules.llm_gateway.gateway import LLMGateway, get_llm_gateway
from app.modules.projects.dependencies import get_owned_project
from app.modules.projects.models import Project

router = APIRouter(prefix="/v1/code-review", tags=["Code Review Engine"])

review_router = APIRouter(
    prefix="/v1/projects/{project_id}/reviews", tags=["Code Review Engine — Reviews"]
)


@review_router.post(
    "",
    response_model=ReviewDetailRead,
    dependencies=[llm_rate_limit("code_review", times=20, seconds=3600)],
)
async def submit_review(
    payload: SubmitReviewRequest,
    project: Project = Depends(get_owned_project),
    db: AsyncSession = Depends(get_db),
    gateway: LLMGateway = Depends(get_llm_gateway),
) -> ReviewDetailRead:
    review = await service.submit_review(
        db,
        gateway,
        project_id=project.id,
        milestone_id=payload.milestone_id,
        code=payload.code,
        language=payload.language,
        file_path=payload.file_path,
    )
    return ReviewDetailRead.from_model(review)


@review_router.get("", response_model=ReviewListResponse)
async def list_reviews(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    project: Project = Depends(get_owned_project),
    db: AsyncSession = Depends(get_db),
) -> ReviewListResponse:
    rows, total = await service.list_reviews(db, project.id, limit, offset)
    return ReviewListResponse(
        items=[ReviewSummaryRead.from_model(review, count) for review, count in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


@review_router.get("/{review_id}", response_model=ReviewDetailRead)
async def get_review(
    review_id: uuid.UUID,
    project: Project = Depends(get_owned_project),
    db: AsyncSession = Depends(get_db),
) -> ReviewDetailRead:
    review = await service.get_review(db, project_id=project.id, review_id=review_id)
    return ReviewDetailRead.from_model(review)
