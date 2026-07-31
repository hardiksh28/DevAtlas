"""Integration tests for the RAG Knowledge Engine's /search and /ask
routes (app.modules.knowledge.router).

Only mode="keyword" is exercised here — "vector"/"hybrid" need real
pgvector, which this suite's default SQLite fallback can't provide (see
test_retrieval_service.py's module docstring); those modes are covered
end-to-end only against real Postgres in CI. Chunks are seeded directly
via `db_session` (there's no API that creates them — only the ingestion
worker does, and it's a separate process this suite doesn't run) — safe
because `db_session` and `client` share the same underlying SQLite
engine within one test (see tests/conftest.py's `engine` fixture).
"""

import uuid

import pytest_asyncio

from app.core.redis import get_redis
from app.modules.llm_gateway.gateway import get_llm_gateway
from tests.knowledge_fixtures import seed_chunk
from tests.test_rag_service import FakeCacheRedis, FakeLLMGateway


@pytest_asyncio.fixture
async def rag(client):
    """Yields (client, fake_gateway) with the LLM gateway and Redis
    dependencies overridden on the same app instance `client` talks to."""
    from app.main import app as fastapi_app

    fake_gateway = FakeLLMGateway()
    fake_redis = FakeCacheRedis()
    fastapi_app.dependency_overrides[get_llm_gateway] = lambda: fake_gateway
    fastapi_app.dependency_overrides[get_redis] = lambda: fake_redis
    yield client, fake_gateway


async def _register(client, email="user@example.com"):
    return await client.post(
        "/v1/auth/register",
        json={"email": email, "password": "hunter22222", "display_name": "User One"},
    )


async def _create_project(client, name="Docs Project"):
    resp = await client.post("/v1/projects", json={"name": name})
    return resp.json()["id"]


class TestSearchEndpoint:
    async def test_requires_auth(self, rag):
        client, _ = rag
        resp = await client.post(
            "/v1/projects/00000000-0000-0000-0000-000000000000/documents/search",
            json={"query": "test", "mode": "keyword"},
        )
        assert resp.status_code == 401

    async def test_rejects_blank_query(self, rag):
        client, _ = rag
        await _register(client, email="search1@example.com")
        project_id = await _create_project(client)

        resp = await client.post(
            f"/v1/projects/{project_id}/documents/search", json={"query": "   ", "mode": "keyword"}
        )
        assert resp.status_code == 422

    async def test_finds_seeded_chunk(self, rag, db_session):
        client, _ = rag
        registered = await _register(client, email="search2@example.com")
        user_id = uuid.UUID(registered.json()["user"]["id"])
        project_id = uuid.UUID(await _create_project(client))

        await seed_chunk(db_session, project_id, user_id, content="The CLI requires Node 20 to install.")

        resp = await client.post(
            f"/v1/projects/{project_id}/documents/search",
            json={"query": "Node install", "mode": "keyword"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["mode"] == "keyword"
        assert len(body["results"]) == 1
        assert "Node 20" in body["results"][0]["content"]
        assert body["results"][0]["keyword_rank"] == 1

    async def test_no_matches_returns_empty_results_not_an_error(self, rag):
        client, _ = rag
        await _register(client, email="search3@example.com")
        project_id = await _create_project(client)

        resp = await client.post(
            f"/v1/projects/{project_id}/documents/search",
            json={"query": "nothing matches this", "mode": "keyword"},
        )
        assert resp.status_code == 200
        assert resp.json()["results"] == []

    async def test_another_users_project_is_404(self, rag):
        client, _ = rag
        await _register(client, email="search4owner@example.com")
        project_id = await _create_project(client)
        await client.post("/v1/auth/logout")
        await _register(client, email="search4intruder@example.com")

        resp = await client.post(
            f"/v1/projects/{project_id}/documents/search", json={"query": "test", "mode": "keyword"}
        )
        assert resp.status_code == 404


class TestAskEndpoint:
    async def test_rejects_blank_question(self, rag):
        client, _ = rag
        await _register(client, email="ask1@example.com")
        project_id = await _create_project(client)

        resp = await client.post(
            f"/v1/projects/{project_id}/documents/ask", json={"question": "", "mode": "keyword"}
        )
        assert resp.status_code == 422

    async def test_answers_using_retrieved_context(self, rag, db_session):
        client, fake_gateway = rag
        fake_gateway.answer = "Node 20 is required."
        registered = await _register(client, email="ask2@example.com")
        user_id = uuid.UUID(registered.json()["user"]["id"])
        project_id = uuid.UUID(await _create_project(client))

        await seed_chunk(db_session, project_id, user_id, content="The CLI requires Node 20 to install.")

        resp = await client.post(
            f"/v1/projects/{project_id}/documents/ask",
            json={"question": "What Node is required?", "mode": "keyword"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["answer"] == "Node 20 is required."
        assert body["chunks_retrieved"] == 1
        assert len(body["sources"]) == 1
        assert body["cached"] is False

    async def test_no_results_skips_llm_call(self, rag):
        client, fake_gateway = rag
        await _register(client, email="ask3@example.com")
        project_id = await _create_project(client)

        resp = await client.post(
            f"/v1/projects/{project_id}/documents/ask",
            json={"question": "anything at all", "mode": "keyword"},
        )
        assert resp.status_code == 200
        assert resp.json()["chunks_retrieved"] == 0
        assert fake_gateway.generate_calls == []

    async def test_second_identical_ask_is_served_from_cache(self, rag, db_session):
        client, fake_gateway = rag
        registered = await _register(client, email="ask4@example.com")
        user_id = uuid.UUID(registered.json()["user"]["id"])
        project_id = uuid.UUID(await _create_project(client))
        await seed_chunk(db_session, project_id, user_id, content="Node 20 install guide.")

        payload = {"question": "Node install?", "mode": "keyword"}
        first = await client.post(f"/v1/projects/{project_id}/documents/ask", json=payload)
        second = await client.post(f"/v1/projects/{project_id}/documents/ask", json=payload)

        assert first.json()["cached"] is False
        assert second.json()["cached"] is True
        assert len(fake_gateway.generate_calls) == 1

    async def test_another_users_project_is_404(self, rag):
        client, _ = rag
        await _register(client, email="ask5owner@example.com")
        project_id = await _create_project(client)
        await client.post("/v1/auth/logout")
        await _register(client, email="ask5intruder@example.com")

        resp = await client.post(
            f"/v1/projects/{project_id}/documents/ask", json={"question": "test", "mode": "keyword"}
        )
        assert resp.status_code == 404
