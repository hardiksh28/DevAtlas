"""Tests for app.modules.knowledge.retrieval.retrieval_service.

`reciprocal_rank_fusion` is pure Python and fully tested here regardless
of dialect. `keyword_search` is tested against its SQLite fallback path
(this repo's default test dialect — see tests/conftest.py), which is
enough to exercise metadata filtering and ranking end-to-end without a
running Postgres. `semantic_search`/`hybrid_search` need pgvector's real
`<=>` operator, which SQLite cannot provide at all — those tests are
skipped unless TEST_DATABASE_URL points at real Postgres (CI does; see
.github/workflows/ci.yml), mirroring how auth's CITEXT-dependent
behavior is treated in this same test suite.
"""

import uuid
from datetime import UTC, datetime

import pytest

from app.modules.auth import service as auth_service
from app.modules.knowledge.retrieval.retrieval_service import (
    RetrievalFilters,
    RetrievedChunk,
    hybrid_search,
    keyword_search,
    reciprocal_rank_fusion,
    semantic_search,
)
from app.modules.projects import service as projects_service
from tests.knowledge_fixtures import create_chunk, create_document, create_ingestion_job, seed_chunk


def _is_postgres(db_session) -> bool:
    bind = db_session.get_bind()
    return bind.dialect.name == "postgresql"


async def _make_user_and_project(db, email="owner@example.com"):
    user = await auth_service.register_user(db, email, "hunter22222", "Owner")
    project = await projects_service.create_project(db, user.id, "Docs Project", None)
    return user, project


def _chunk(chunk_id: uuid.UUID, **overrides) -> RetrievedChunk:
    base = {
        "chunk_id": chunk_id,
        "document_id": uuid.uuid4(),
        "project_id": uuid.uuid4(),
        "content": "content",
        "heading_path": [],
        "chunk_metadata": {},
        "source_type": "markdown_file",
        "source_path": "a.md",
        "title": "A",
    }
    base.update(overrides)
    return RetrievedChunk(**base)


class TestReciprocalRankFusion:
    def test_chunk_ranked_first_by_both_retrievers_wins(self):
        a, b = uuid.uuid4(), uuid.uuid4()
        vector_results = [_chunk(a), _chunk(b)]
        keyword_results = [_chunk(a), _chunk(b)]

        fused = reciprocal_rank_fusion([vector_results, keyword_results], k=60)

        assert fused[0].chunk_id == a
        assert fused[0].score > fused[1].score

    def test_chunk_found_by_only_one_retriever_still_included(self):
        a, b = uuid.uuid4(), uuid.uuid4()
        vector_results = [_chunk(a)]
        keyword_results = [_chunk(b)]

        fused = reciprocal_rank_fusion([vector_results, keyword_results], k=60)

        assert {c.chunk_id for c in fused} == {a, b}

    def test_merges_per_retriever_scores_onto_one_canonical_chunk(self):
        shared_id = uuid.uuid4()
        vector_chunk = _chunk(shared_id, vector_score=0.9, vector_rank=1)
        keyword_chunk = _chunk(shared_id, keyword_score=5.0, keyword_rank=2)

        fused = reciprocal_rank_fusion([[vector_chunk], [keyword_chunk]], k=60)

        assert len(fused) == 1
        assert fused[0].vector_score == 0.9
        assert fused[0].keyword_score == 5.0
        assert fused[0].vector_rank == 1
        assert fused[0].keyword_rank == 2

    def test_empty_lists_produce_empty_result(self):
        assert reciprocal_rank_fusion([[], []], k=60) == []

    def test_larger_k_flattens_rank_influence(self):
        # With a small k, rank #1 dominates rank #2 heavily; with a
        # very large k, the two scores converge toward equal.
        a, b = uuid.uuid4(), uuid.uuid4()
        ranked = [_chunk(a), _chunk(b)]

        small_k = reciprocal_rank_fusion([ranked], k=1)
        large_k = reciprocal_rank_fusion([ranked], k=10_000)

        small_k_ratio = small_k[0].score / small_k[1].score
        large_k_ratio = large_k[0].score / large_k[1].score
        assert small_k_ratio > large_k_ratio > 1.0


class TestKeywordSearchFallback:
    async def test_finds_chunk_containing_query_terms(self, db_session):
        _, project = await _make_user_and_project(db_session, email="kw1@example.com")
        await seed_chunk(db_session, project.id, project.owner_id, content="Installing the CLI requires Node 20.")
        await seed_chunk(db_session, project.id, project.owner_id, content="Unrelated content about cooking pasta.")

        results = await keyword_search(db_session, project.id, "Node CLI", top_k=10)

        assert len(results) == 1
        assert "Node 20" in results[0].content
        assert results[0].keyword_rank == 1
        assert results[0].keyword_score is not None

    async def test_ranks_more_matching_terms_higher(self, db_session):
        _, project = await _make_user_and_project(db_session, email="kw2@example.com")
        await seed_chunk(db_session, project.id, project.owner_id, content="python python python install guide")
        await seed_chunk(db_session, project.id, project.owner_id, content="python install guide only once")

        results = await keyword_search(db_session, project.id, "python install", top_k=10)

        assert len(results) == 2
        assert results[0].keyword_score >= results[1].keyword_score

    async def test_no_matches_returns_empty(self, db_session):
        _, project = await _make_user_and_project(db_session, email="kw3@example.com")
        await seed_chunk(db_session, project.id, project.owner_id, content="something entirely different")

        results = await keyword_search(db_session, project.id, "nonexistent_term_xyz", top_k=10)
        assert results == []

    async def test_blank_query_returns_empty_without_error(self, db_session):
        _, project = await _make_user_and_project(db_session, email="kw4@example.com")
        await seed_chunk(db_session, project.id, project.owner_id, content="some content")

        assert await keyword_search(db_session, project.id, "   ", top_k=10) == []

    async def test_filters_by_source_type(self, db_session):
        _, project = await _make_user_and_project(db_session, email="kw5@example.com")
        job = await create_ingestion_job(db_session, project.id, project.owner_id)
        md_doc = await create_document(db_session, project.id, job.id, source_path="a.md", source_type="markdown_file")
        pdf_doc = await create_document(db_session, project.id, job.id, source_path="b.pdf", source_type="pdf_file")

        await create_chunk(db_session, md_doc, content="widget configuration guide")
        await create_chunk(db_session, pdf_doc, content="widget configuration guide")
        await db_session.commit()

        results = await keyword_search(
            db_session,
            project.id,
            "widget configuration",
            top_k=10,
            filters=RetrievalFilters(source_types=["pdf_file"]),
        )

        assert len(results) == 1
        assert results[0].source_type == "pdf_file"

    async def test_filters_by_document_id(self, db_session):
        _, project = await _make_user_and_project(db_session, email="kw6@example.com")
        job = await create_ingestion_job(db_session, project.id, project.owner_id)
        doc_a = await create_document(db_session, project.id, job.id, source_path="a.md")
        doc_b = await create_document(db_session, project.id, job.id, source_path="b.md")

        await create_chunk(db_session, doc_a, content="shared search term here")
        await create_chunk(db_session, doc_b, content="shared search term here")
        await db_session.commit()

        results = await keyword_search(
            db_session, project.id, "shared search term", top_k=10, filters=RetrievalFilters(document_ids=[doc_a.id])
        )

        assert len(results) == 1
        assert results[0].document_id == doc_a.id

    async def test_excludes_soft_deleted_documents(self, db_session):
        _, project = await _make_user_and_project(db_session, email="kw7@example.com")
        job = await create_ingestion_job(db_session, project.id, project.owner_id)
        doc = await create_document(db_session, project.id, job.id)

        doc.deleted_at = datetime.now(UTC)

        await create_chunk(db_session, doc, content="findable unique term xyzzy")
        await db_session.commit()

        results = await keyword_search(db_session, project.id, "xyzzy", top_k=10)
        assert results == []

    async def test_does_not_leak_across_projects(self, db_session):
        _, project_a = await _make_user_and_project(db_session, email="kw8a@example.com")
        _, project_b = await _make_user_and_project(db_session, email="kw8b@example.com")
        await seed_chunk(db_session, project_a.id, project_a.owner_id, content="cross project unique marker")

        results = await keyword_search(db_session, project_b.id, "cross project unique marker", top_k=10)
        assert results == []


class TestSemanticSearchPostgresOnly:
    async def test_orders_by_cosine_similarity(self, db_session):
        if not _is_postgres(db_session):
            pytest.skip("semantic_search requires real pgvector — set TEST_DATABASE_URL to a Postgres instance")

        _, project = await _make_user_and_project(db_session, email="vec1@example.com")
        dims = 768
        close_vector = [1.0] + [0.0] * (dims - 1)
        far_vector = [0.0, 1.0] + [0.0] * (dims - 2)

        await seed_chunk(db_session, project.id, project.owner_id, content="close match", vector=close_vector)
        await seed_chunk(db_session, project.id, project.owner_id, content="far match", vector=far_vector)

        results = await semantic_search(db_session, project.id, close_vector, top_k=10)

        assert results[0].content == "close match"
        assert results[0].vector_score > results[1].vector_score


class TestHybridSearchPostgresOnly:
    async def test_combines_vector_and_keyword_results(self, db_session):
        if not _is_postgres(db_session):
            pytest.skip("hybrid_search requires real pgvector — set TEST_DATABASE_URL to a Postgres instance")

        _, project = await _make_user_and_project(db_session, email="hyb1@example.com")
        dims = 768
        vector = [1.0] + [0.0] * (dims - 1)
        await seed_chunk(
            db_session, project.id, project.owner_id, content="unique keyword marker zzy", vector=vector
        )

        results = await hybrid_search(
            db_session,
            project.id,
            "unique keyword marker zzy",
            vector,
            top_k=5,
            vector_candidates=10,
            keyword_candidates=10,
            rrf_k=60,
        )

        assert len(results) == 1
        assert results[0].vector_rank == 1
        assert results[0].keyword_rank == 1
