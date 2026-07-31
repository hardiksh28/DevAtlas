"""Thin HTTP-layer tests for the Code Review Engine's routes. Mirrors
test_mentoring_router.py's conventions: the real LLM gateway is
exercised here (not faked), since Ollama isn't reachable in this test
environment — these tests only cover paths that don't require a
successful generation. Full submit-and-persist coverage is in
test_code_review_service.py against a fake gateway."""

import uuid

from tests.code_review_fixtures import create_comment, create_review


async def _register(client, email="user@example.com"):
    return await client.post(
        "/v1/auth/register",
        json={"email": email, "password": "hunter22222", "display_name": "User One"},
    )


async def _create_project(client, name="Review Project"):
    resp = await client.post("/v1/projects", json={"name": name})
    return resp.json()["id"]


class TestListReviewsRoute:
    async def test_list_reviews_before_any_submitted_is_empty(self, client):
        await _register(client, email="list1@example.com")
        project_id = await _create_project(client)

        resp = await client.get(f"/v1/projects/{project_id}/reviews")

        assert resp.status_code == 200
        body = resp.json()
        assert body["items"] == []
        assert body["total"] == 0

    async def test_lists_seeded_review_with_comment_count(self, client, db_session):
        await _register(client, email="list2@example.com")
        project_id = await _create_project(client)
        review = await create_review(db_session, uuid.UUID(project_id), summary="Seeded review")
        await create_comment(db_session, review)
        await db_session.commit()

        resp = await client.get(f"/v1/projects/{project_id}/reviews")

        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 1
        assert body["items"][0]["summary"] == "Seeded review"
        assert body["items"][0]["comment_count"] == 1


class TestGetReviewRoute:
    async def test_returns_full_detail(self, client, db_session):
        await _register(client, email="get1@example.com")
        project_id = await _create_project(client)
        review = await create_review(db_session, uuid.UUID(project_id), overall_score=77)
        await create_comment(db_session, review, body="Watch this edge case.")
        await db_session.commit()

        resp = await client.get(f"/v1/projects/{project_id}/reviews/{review.id}")

        assert resp.status_code == 200
        body = resp.json()
        assert body["overall_score"] == 77
        assert body["comments"][0]["body"] == "Watch this edge case."

    async def test_missing_review_is_404(self, client):
        await _register(client, email="get2@example.com")
        project_id = await _create_project(client)

        resp = await client.get(f"/v1/projects/{project_id}/reviews/{uuid.uuid4()}")

        assert resp.status_code == 404
        assert resp.json()["error_code"] == "review_not_found"


class TestSubmitReviewValidation:
    async def test_blank_code_is_rejected(self, client):
        await _register(client, email="submit1@example.com")
        project_id = await _create_project(client)

        resp = await client.post(
            f"/v1/projects/{project_id}/reviews", json={"code": "   ", "language": "python"}
        )

        assert resp.status_code == 422

    async def test_blank_language_is_rejected(self, client):
        await _register(client, email="submit2@example.com")
        project_id = await _create_project(client)

        resp = await client.post(
            f"/v1/projects/{project_id}/reviews", json={"code": "x = 1", "language": "  "}
        )

        assert resp.status_code == 422


class TestProjectOwnershipEnforcement:
    async def test_review_routes_for_another_users_project_are_404(self, client):
        await _register(client, email="owner@example.com")
        project_id = await _create_project(client)
        await client.post("/v1/auth/logout")
        await _register(client, email="intruder@example.com")

        resp = await client.get(f"/v1/projects/{project_id}/reviews")

        assert resp.status_code == 404
