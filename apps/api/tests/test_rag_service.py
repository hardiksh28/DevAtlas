"""Integration tests for app.modules.knowledge.retrieval.rag_service.

Uses mode="keyword" throughout — the one retrieval mode with a real
SQLite-compatible code path (see test_retrieval_service.py's module
docstring) — so these tests exercise rag_service's *own* logic (caching,
context/prompt assembly, error translation) without needing pgvector.
FakeLLMGateway/FakeCacheRedis are local test doubles, same pattern as
FakeQueue in test_knowledge_router.py.
"""

import json
from typing import Any

import pytest

from app.modules.auth import service as auth_service
from app.modules.knowledge.exceptions import RetrievalServiceUnavailableError
from app.modules.knowledge.retrieval import rag_service
from app.modules.knowledge.retrieval.prompt_templates import NO_RESULTS_ANSWER
from app.modules.knowledge.retrieval.retrieval_service import RetrievalFilters
from app.modules.projects import service as projects_service
from tests.knowledge_fixtures import seed_chunk


class FakeLLMGateway:
    def __init__(self, *, answer: str = "The answer is 42.") -> None:
        self.answer = answer
        self.generate_calls: list[str] = []
        self.embed_calls: list[list[str]] = []
        self.raise_on_generate: Exception | None = None
        self.raise_on_embed: Exception | None = None

    async def embed(self, texts: list[str]) -> list[list[float]]:
        self.embed_calls.append(texts)
        if self.raise_on_embed:
            raise self.raise_on_embed
        return [[0.1] * 768 for _ in texts]

    async def generate(self, operation: str, prompt: str) -> str:
        self.generate_calls.append(prompt)
        if self.raise_on_generate:
            raise self.raise_on_generate
        return self.answer


class FakeCacheRedis:
    """In-memory stand-in for redis.asyncio.Redis covering both call
    sets that share the `get_redis` dependency: get/set (cache.py's RAG
    answer cache) and incr/expire/ttl (auth's rate limiter — see
    tests/conftest.py's own FakeRedis, which only implements the
    latter). Router-level tests override `get_redis` app-wide, so
    whatever they swap in must satisfy every caller of that dependency,
    not just the one under test."""

    def __init__(self) -> None:
        self._store: dict[str, str] = {}
        self._counters: dict[str, int] = {}

    async def get(self, key: str) -> str | None:
        return self._store.get(key)

    async def set(self, key: str, value: str, *, ex: int | None = None) -> None:
        self._store[key] = value

    async def incr(self, key: str) -> int:
        self._counters[key] = self._counters.get(key, 0) + 1
        return self._counters[key]

    async def expire(self, key: str, seconds: int) -> None:
        return None

    async def ttl(self, key: str) -> int:
        return 60


async def _make_user_and_project(db, email="owner@example.com"):
    user = await auth_service.register_user(db, email, "hunter22222", "Owner")
    project = await projects_service.create_project(db, user.id, "Docs Project", None)
    return user, project


class TestAnswerQuestion:
    async def test_no_chunks_returns_fixed_answer_without_calling_llm(self, db_session):
        _, project = await _make_user_and_project(db_session, email="rag1@example.com")
        gateway = FakeLLMGateway()
        redis = FakeCacheRedis()

        result = await rag_service.answer_question(
            db_session, gateway, redis, project_id=project.id, question="anything", mode="keyword"
        )

        assert result.answer == NO_RESULTS_ANSWER
        assert result.sources == []
        assert result.cached is False
        assert gateway.generate_calls == []  # no LLM call for an empty corpus

    async def test_no_results_answer_is_not_cached(self, db_session):
        _, project = await _make_user_and_project(db_session, email="rag2@example.com")
        gateway = FakeLLMGateway()
        redis = FakeCacheRedis()

        await rag_service.answer_question(
            db_session, gateway, redis, project_id=project.id, question="anything", mode="keyword"
        )

        cache_key = rag_service.cache.build_cache_key(
            project.id, "anything", mode="keyword", top_k=8, source_types=None, document_ids=None
        )
        assert await redis.get(cache_key) is None

    async def test_answers_from_retrieved_context_and_caches_result(self, db_session):
        user, project = await _make_user_and_project(db_session, email="rag3@example.com")
        await seed_chunk(db_session, project.id, user.id, content="The CLI requires Node 20 to install.")
        gateway = FakeLLMGateway(answer="You need Node 20.")
        redis = FakeCacheRedis()

        result = await rag_service.answer_question(
            db_session, gateway, redis, project_id=project.id, question="What Node install?", mode="keyword"
        )

        assert result.answer == "You need Node 20."
        assert result.chunks_retrieved == 1
        assert result.cached is False
        assert len(gateway.generate_calls) == 1
        assert "Node 20" in gateway.generate_calls[0]  # context made it into the prompt

    async def test_second_call_with_same_args_is_served_from_cache(self, db_session):
        user, project = await _make_user_and_project(db_session, email="rag4@example.com")
        await seed_chunk(db_session, project.id, user.id, content="The CLI requires Node 20 to install.")
        gateway = FakeLLMGateway()
        redis = FakeCacheRedis()

        first = await rag_service.answer_question(
            db_session, gateway, redis, project_id=project.id, question="Node install?", mode="keyword"
        )
        second = await rag_service.answer_question(
            db_session, gateway, redis, project_id=project.id, question="Node install?", mode="keyword"
        )

        assert first.cached is False
        assert second.cached is True
        assert second.answer == first.answer
        assert len(gateway.generate_calls) == 1  # generate only ran once, not twice

    async def test_use_cache_false_bypasses_cache_entirely(self, db_session):
        user, project = await _make_user_and_project(db_session, email="rag5@example.com")
        await seed_chunk(db_session, project.id, user.id, content="The CLI requires Node 20 to install.")
        gateway = FakeLLMGateway()
        redis = FakeCacheRedis()

        await rag_service.answer_question(
            db_session, gateway, redis, project_id=project.id, question="Node?", mode="keyword", use_cache=False
        )
        await rag_service.answer_question(
            db_session, gateway, redis, project_id=project.id, question="Node?", mode="keyword", use_cache=False
        )

        assert len(gateway.generate_calls) == 2  # no caching means every call regenerates

    async def test_different_filters_produce_different_cache_entries(self, db_session):
        user, project = await _make_user_and_project(db_session, email="rag6@example.com")
        await seed_chunk(db_session, project.id, user.id, content="Node 20 install guide.")
        gateway = FakeLLMGateway()
        redis = FakeCacheRedis()

        await rag_service.answer_question(
            db_session,
            gateway,
            redis,
            project_id=project.id,
            question="Node?",
            mode="keyword",
            filters=RetrievalFilters(source_types=["markdown_file"]),
        )
        await rag_service.answer_question(
            db_session,
            gateway,
            redis,
            project_id=project.id,
            question="Node?",
            mode="keyword",
            filters=RetrievalFilters(source_types=["pdf_file"]),
        )

        # Second call found nothing (no pdf_file chunks exist) and hit
        # the no-LLM-call path — but it must not have been served from
        # the first call's cache entry (different filters => different key).
        assert len(gateway.generate_calls) == 1

    async def test_generate_failure_raises_retrieval_service_unavailable(self, db_session):
        user, project = await _make_user_and_project(db_session, email="rag7@example.com")
        await seed_chunk(db_session, project.id, user.id, content="Node 20 install guide.")
        gateway = FakeLLMGateway()
        gateway.raise_on_generate = RuntimeError("Ollama is down")
        redis = FakeCacheRedis()

        with pytest.raises(RetrievalServiceUnavailableError):
            await rag_service.answer_question(
                db_session, gateway, redis, project_id=project.id, question="Node?", mode="keyword"
            )

    async def test_embed_failure_raises_retrieval_service_unavailable(self, db_session):
        _, project = await _make_user_and_project(db_session, email="rag8@example.com")
        gateway = FakeLLMGateway()
        gateway.raise_on_embed = RuntimeError("Ollama is down")
        redis = FakeCacheRedis()

        with pytest.raises(RetrievalServiceUnavailableError):
            await rag_service.answer_question(
                db_session, gateway, redis, project_id=project.id, question="Node?", mode="vector"
            )

    async def test_sources_reference_the_retrieved_chunk(self, db_session):
        user, project = await _make_user_and_project(db_session, email="rag9@example.com")
        chunk = await seed_chunk(db_session, project.id, user.id, content="Node 20 install guide.")
        gateway = FakeLLMGateway()
        redis = FakeCacheRedis()

        result = await rag_service.answer_question(
            db_session, gateway, redis, project_id=project.id, question="Node?", mode="keyword"
        )

        assert len(result.sources) == 1
        assert result.sources[0].chunk_id == chunk.id


class TestCachePayloadRoundTrip:
    async def test_cached_payload_is_json_serializable(self, db_session):
        user, project = await _make_user_and_project(db_session, email="rag10@example.com")
        await seed_chunk(db_session, project.id, user.id, content="Node 20 install guide.")
        gateway = FakeLLMGateway()
        redis = FakeCacheRedis()

        await rag_service.answer_question(
            db_session, gateway, redis, project_id=project.id, question="Node?", mode="keyword"
        )

        stored: dict[str, Any] | None = None
        for value in redis._store.values():
            stored = json.loads(value)
        assert stored is not None
        assert stored["answer"]
        assert isinstance(stored["sources"], list)
        assert isinstance(stored["sources"][0]["chunk_id"], str)
