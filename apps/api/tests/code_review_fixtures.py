"""Shared test helpers for seeding code review data directly via the
ORM. Not a test file itself (no `test_` prefix), mirroring
tests/mentoring_fixtures.py."""

import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.code_review.models import CodeReview, CodeReviewComment


async def create_review(
    db: AsyncSession,
    project_id: uuid.UUID,
    *,
    language: str = "python",
    file_path: str | None = "app.py",
    code: str = "x = 1",
    overall_score: int = 80,
    summary: str = "Looks good.",
    strengths: list[str] | None = None,
    refactoring_ideas: list[str] | None = None,
    created_at: datetime | None = None,
) -> CodeReview:
    review = CodeReview(
        project_id=project_id,
        language=language,
        file_path=file_path,
        code=code,
        overall_score=overall_score,
        summary=summary,
        strengths=strengths or [],
        refactoring_ideas=refactoring_ideas or [],
    )
    if created_at is not None:
        review.created_at = created_at
    db.add(review)
    await db.flush()
    return review


async def create_comment(
    db: AsyncSession,
    review: CodeReview,
    *,
    file_path: str = "app.py",
    line_start: int = 1,
    line_end: int = 1,
    category: str = "bug",
    severity: str = "major",
    body: str = "What if this is empty?",
    suggestion: str | None = None,
    concept_tags: list[str] | None = None,
) -> CodeReviewComment:
    comment = CodeReviewComment(
        review=review,
        file_path=file_path,
        line_start=line_start,
        line_end=line_end,
        category=category,
        severity=severity,
        body=body,
        suggestion=suggestion,
        concept_tags=concept_tags or [],
    )
    db.add(comment)
    await db.flush()
    return comment
