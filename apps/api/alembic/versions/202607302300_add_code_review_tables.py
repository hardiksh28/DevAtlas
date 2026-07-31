"""add code review engine tables: code_reviews + code_review_comments

Revision ID: 202607302300
Revises: 202607302200
Create Date: 2026-07-30

Implements the persisted half of ARCHITECTURE.md's "Code Review Engine"
(Section 3) — one CodeReview per submission (score, summary, strengths,
refactoring ideas) plus its line-anchored CodeReviewComment children.
The gated discussion thread per comment is explicitly deferred (see
app/modules/code_review/models.py's docstring).
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "202607302300"
down_revision: str | None = "202607302200"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "code_reviews",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "milestone_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("milestones.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("language", sa.String(length=50), nullable=False),
        sa.Column("file_path", sa.String(length=500), nullable=True),
        sa.Column("code", sa.String(), nullable=False),
        sa.Column("overall_score", sa.Integer(), nullable=False),
        sa.Column("summary", sa.String(), nullable=False),
        sa.Column("strengths", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("refactoring_ideas", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column(
            "created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    op.create_index("ix_code_reviews_project_created", "code_reviews", ["project_id", "created_at"])

    op.create_table(
        "code_review_comments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "review_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("code_reviews.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("file_path", sa.String(length=500), nullable=False),
        sa.Column("line_start", sa.Integer(), nullable=False),
        sa.Column("line_end", sa.Integer(), nullable=False),
        sa.Column("category", sa.String(length=20), nullable=False),
        sa.Column("severity", sa.String(length=20), nullable=False),
        sa.Column("body", sa.String(), nullable=False),
        sa.Column("suggestion", sa.String(), nullable=True),
        sa.Column("concept_tags", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column(
            "created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.CheckConstraint(
            "category IN ('correctness', 'bug', 'readability', 'maintainability', "
            "'security', 'performance', 'scalability', 'best_practice')",
            name="ck_code_review_comments_category",
        ),
        sa.CheckConstraint(
            "severity IN ('info', 'minor', 'major', 'critical')",
            name="ck_code_review_comments_severity",
        ),
    )
    op.create_index(
        "ix_code_review_comments_review_line", "code_review_comments", ["review_id", "line_start"]
    )


def downgrade() -> None:
    op.drop_table("code_review_comments")
    op.drop_table("code_reviews")
