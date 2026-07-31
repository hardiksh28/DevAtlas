"""Integration tests for app.modules.code_review.service, calling
service functions directly against db_session (no HTTP layer) — same
pattern as test_mentoring_service.py."""

import json

import pytest

from app.modules.auth import service as auth_service
from app.modules.code_review import service as code_review_service
from app.modules.code_review.exceptions import ReviewGenerationError, ReviewNotFoundError
from app.modules.curriculum import service as curriculum_service
from app.modules.projects import service as projects_service
from tests.code_review_fixtures import create_comment, create_review
from tests.taxonomy_fixtures import create_concept


class FakeLLMGateway:
    def __init__(self, *, review_response: str | None = None) -> None:
        self.review_response = review_response or json.dumps(
            {
                "overall_score": 65,
                "summary": "Reasonable first attempt with one real bug.",
                "strengths": ["Clear function names"],
                "comments": [
                    {
                        "file_path": "app.py",
                        "line_start": 1,
                        "line_end": 1,
                        "category": "bug",
                        "severity": "major",
                        "body": "What happens if `items` is empty?",
                        "suggestion": "Add a guard clause.",
                        "concept_tags": ["python.iteration"],
                    }
                ],
                "refactoring_ideas": ["Extract validation into its own function."],
            }
        )
        self.generate_calls: list[tuple[str, str]] = []
        self.raise_on_generate: Exception | None = None

    async def embed(self, texts: list[str]) -> list[list[float]]:
        return [[0.1] * 768 for _ in texts]

    async def generate(self, operation: str, prompt: str) -> str:
        self.generate_calls.append((operation, prompt))
        if self.raise_on_generate:
            raise self.raise_on_generate
        return self.review_response


async def _make_user_and_project(db, email: str):
    user = await auth_service.register_user(db, email, "hunter22222", "Owner")
    project = await projects_service.create_project(db, user.id, "Review Project", None)
    return user, project


class TestSubmitReview:
    async def test_creates_review_with_score_summary_and_comments(self, db_session):
        _, project = await _make_user_and_project(db_session, "review1@example.com")
        gateway = FakeLLMGateway()

        review = await code_review_service.submit_review(
            db_session,
            gateway,
            project_id=project.id,
            milestone_id=None,
            code="def f(items):\n    return items[0]",
            language="python",
            file_path="app.py",
        )

        assert review.overall_score == 65
        assert review.summary.startswith("Reasonable")
        assert review.strengths == ["Clear function names"]
        assert review.refactoring_ideas == ["Extract validation into its own function."]
        assert len(review.comments) == 1
        assert review.comments[0].category == "bug"
        assert review.comments[0].line_start == 1

    async def test_tags_the_generate_call_with_the_code_review_operation(self, db_session):
        _, project = await _make_user_and_project(db_session, "review2@example.com")
        gateway = FakeLLMGateway()

        await code_review_service.submit_review(
            db_session,
            gateway,
            project_id=project.id,
            milestone_id=None,
            code="x = 1",
            language="python",
            file_path=None,
        )

        assert gateway.generate_calls[0][0] == "code_review"

    async def test_defaults_experience_level_without_a_roadmap(self, db_session):
        _, project = await _make_user_and_project(db_session, "review3@example.com")
        gateway = FakeLLMGateway()

        await code_review_service.submit_review(
            db_session,
            gateway,
            project_id=project.id,
            milestone_id=None,
            code="x = 1",
            language="python",
            file_path=None,
        )

        assert "intermediate" in gateway.generate_calls[0][1]

    async def test_uses_roadmap_experience_level_when_present(self, db_session):
        _, project = await _make_user_and_project(db_session, "review4@example.com")
        await create_concept(db_session, "python.variables", severity="foundational")
        await db_session.commit()
        await curriculum_service.generate_or_regenerate_roadmap(
            db_session,
            project_id=project.id,
            stack="python",
            stack_version="3.12",
            experience_level="advanced",
        )
        gateway = FakeLLMGateway()

        await code_review_service.submit_review(
            db_session,
            gateway,
            project_id=project.id,
            milestone_id=None,
            code="x = 1",
            language="python",
            file_path=None,
        )

        assert "advanced" in gateway.generate_calls[0][1]

    async def test_drops_out_of_range_line_comments(self, db_session):
        _, project = await _make_user_and_project(db_session, "review5@example.com")
        gateway = FakeLLMGateway(
            review_response=json.dumps(
                {
                    "overall_score": 90,
                    "summary": "Fine.",
                    "strengths": [],
                    "comments": [
                        {
                            "file_path": "app.py",
                            "line_start": 999,
                            "line_end": 999,
                            "category": "bug",
                            "severity": "critical",
                            "body": "Hallucinated line reference.",
                            "suggestion": None,
                            "concept_tags": [],
                        }
                    ],
                    "refactoring_ideas": [],
                }
            )
        )

        review = await code_review_service.submit_review(
            db_session,
            gateway,
            project_id=project.id,
            milestone_id=None,
            code="x = 1",
            language="python",
            file_path="app.py",
        )

        assert review.comments == []

    async def test_retries_once_on_invalid_json_then_raises(self, db_session):
        _, project = await _make_user_and_project(db_session, "review6@example.com")
        gateway = FakeLLMGateway(review_response="not valid json")

        with pytest.raises(ReviewGenerationError):
            await code_review_service.submit_review(
                db_session,
                gateway,
                project_id=project.id,
                milestone_id=None,
                code="x = 1",
                language="python",
                file_path=None,
            )

        assert len(gateway.generate_calls) == 2

    async def test_gateway_failure_raises_review_generation_error(self, db_session):
        _, project = await _make_user_and_project(db_session, "review7@example.com")
        gateway = FakeLLMGateway()
        gateway.raise_on_generate = ConnectionError("ollama unreachable")

        with pytest.raises(ReviewGenerationError):
            await code_review_service.submit_review(
                db_session,
                gateway,
                project_id=project.id,
                milestone_id=None,
                code="x = 1",
                language="python",
                file_path=None,
            )


class TestGetReview:
    async def test_returns_review_with_comments(self, db_session):
        _, project = await _make_user_and_project(db_session, "review8@example.com")
        review = await create_review(db_session, project.id)
        await create_comment(db_session, review)
        await db_session.commit()

        fetched = await code_review_service.get_review(
            db_session, project_id=project.id, review_id=review.id
        )

        assert fetched.id == review.id
        assert len(fetched.comments) == 1

    async def test_missing_review_raises_not_found(self, db_session):
        import uuid

        _, project = await _make_user_and_project(db_session, "review9@example.com")

        with pytest.raises(ReviewNotFoundError):
            await code_review_service.get_review(
                db_session, project_id=project.id, review_id=uuid.uuid4()
            )


class TestListReviews:
    async def test_lists_most_recent_first_with_comment_counts(self, db_session):
        from datetime import UTC, datetime, timedelta

        _, project = await _make_user_and_project(db_session, "review10@example.com")
        base = datetime(2026, 7, 30, tzinfo=UTC)
        first = await create_review(db_session, project.id, summary="First", created_at=base)
        await create_comment(db_session, first)
        second = await create_review(
            db_session, project.id, summary="Second", created_at=base + timedelta(seconds=1)
        )
        await db_session.commit()

        rows, total = await code_review_service.list_reviews(
            db_session, project.id, limit=20, offset=0
        )

        assert total == 2
        assert rows[0][0].id == second.id
        assert rows[0][1] == 0
        assert rows[1][0].id == first.id
        assert rows[1][1] == 1
