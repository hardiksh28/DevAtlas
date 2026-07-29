"""Code Review Engine — router.

Three-layer PR-style review: inline comments, summary, gated discussion.

This module is a stub: the route surface will grow as the module's
responsibilities (see docs/architecture/ARCHITECTURE.md, Section 3) are
implemented. Keeping an explicit, empty-but-real router per module from
day one means every module has an identical shape — new contributors
never have to guess where a given feature's routes should live.
"""
from fastapi import APIRouter
from schemas import ReviewComment

router = APIRouter(prefix="/v1/code-review", tags=["Code Review Engine"])


@router.get("/_example-comment-shape", response_model=ReviewComment)
async def example_comment_shape() -> ReviewComment:
    """Not a real endpoint — exists only to prove `schemas` (packages/schemas)
    is actually installed and importable via the uv workspace, not just
    present on disk. Remove once a real review endpoint uses ReviewComment.
    """
    return ReviewComment(
        file_path="src/app.py",
        line_start=12,
        line_end=14,
        body="What happens here if `items` is empty?",
    )
