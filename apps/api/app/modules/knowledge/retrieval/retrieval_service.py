"""Retrieval services — the RAG Knowledge Engine's search layer.

Two independent retrievers (`semantic_search`, `keyword_search`) plus a
fusion function (`hybrid_search`) that combines their ranked outputs by
*rank position*, not raw score — see
docs/architecture/rag-engine-v1.md Section 5 ("Retrieval Scoring") for
why Reciprocal Rank Fusion, not a weighted sum of cosine similarity and
`ts_rank_cd`, is the principled way to combine two retrievers whose raw
scores live on incomparable scales.
"""

import re
import uuid
from dataclasses import dataclass, replace
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.knowledge.models import ProjectDocument, ProjectDocumentChunk, ProjectEmbedding


@dataclass
class RetrievalFilters:
    """Metadata filtering — narrows both retrievers to a subset of the
    project's corpus before ranking, not after (a `WHERE` clause, not a
    post-hoc list filter), so `top_k` candidates are always drawn from
    the filtered set rather than being wasted on chunks that get thrown
    away afterward."""

    source_types: list[str] | None = None
    document_ids: list[uuid.UUID] | None = None


@dataclass
class RetrievedChunk:
    chunk_id: uuid.UUID
    document_id: uuid.UUID
    project_id: uuid.UUID
    content: str
    heading_path: list[str]
    chunk_metadata: dict[str, Any]
    source_type: str
    source_path: str
    title: str | None
    # Populated by whichever retriever(s) actually found this chunk —
    # a chunk only `semantic_search` found has keyword_score=None, not
    # 0.0 (0.0 would wrongly imply "keyword search considered this and
    # ranked it worst," rather than "keyword search never saw it").
    vector_score: float | None = None
    keyword_score: float | None = None
    vector_rank: int | None = None
    keyword_rank: int | None = None
    # The fused score hybrid_search assigns — 0.0 (not None) for a
    # chunk returned by a single retriever directly (semantic_search or
    # keyword_search alone, no fusion involved).
    score: float = 0.0


def _row_to_chunk(chunk: ProjectDocumentChunk, document: ProjectDocument) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=chunk.id,
        document_id=chunk.document_id,
        project_id=chunk.project_id,
        content=chunk.content,
        heading_path=chunk.heading_path,
        chunk_metadata=chunk.chunk_metadata,
        source_type=document.source_type,
        source_path=document.source_path,
        title=document.title,
    )


def _apply_filters(stmt: Any, filters: RetrievalFilters | None) -> Any:
    if filters is None:
        return stmt
    if filters.source_types:
        stmt = stmt.where(ProjectDocument.source_type.in_(filters.source_types))
    if filters.document_ids:
        stmt = stmt.where(ProjectDocumentChunk.document_id.in_(filters.document_ids))
    return stmt


async def semantic_search(
    db: AsyncSession,
    project_id: uuid.UUID,
    query_embedding: list[float],
    *,
    top_k: int,
    filters: RetrievalFilters | None = None,
) -> list[RetrievedChunk]:
    """Dense retrieval: nearest chunks to `query_embedding` by cosine
    distance (pgvector's `<=>` operator, via the HNSW index on
    `project_embeddings.embedding` — see the migration). The INNER JOIN
    to `project_embeddings` is what restricts results to successfully-
    embedded chunks; there's no separate `embedding_status` filter to
    remember because a chunk without an embedding row simply can't
    appear in this join at all.
    """
    distance = ProjectEmbedding.embedding.cosine_distance(query_embedding)
    stmt = (
        select(ProjectDocumentChunk, ProjectDocument, distance.label("distance"))
        .join(ProjectEmbedding, ProjectEmbedding.chunk_id == ProjectDocumentChunk.id)
        .join(ProjectDocument, ProjectDocument.id == ProjectDocumentChunk.document_id)
        .where(
            ProjectDocumentChunk.project_id == project_id,
            ProjectDocument.deleted_at.is_(None),
        )
    )
    stmt = _apply_filters(stmt, filters).order_by(distance.asc()).limit(top_k)

    result = await db.execute(stmt)
    chunks: list[RetrievedChunk] = []
    for rank, (chunk, document, distance_value) in enumerate(result.all(), start=1):
        retrieved = _row_to_chunk(chunk, document)
        # cosine_distance lives in [0, 2]; similarity = 1 - distance
        # gives the familiar [-1, 1] cosine-similarity scale for display
        # (Section 8, Retrieval Scoring) — never used for fusion math,
        # only for showing a human/debugging a relevance number.
        retrieved.vector_score = 1.0 - float(distance_value)
        retrieved.vector_rank = rank
        chunks.append(retrieved)
    return chunks


async def keyword_search(
    db: AsyncSession,
    project_id: uuid.UUID,
    query_text: str,
    *,
    top_k: int,
    filters: RetrievalFilters | None = None,
) -> list[RetrievedChunk]:
    """Lexical retrieval — Postgres full-text search
    (`websearch_to_tsquery` + `ts_rank_cd`) against the GIN expression
    index on `to_tsvector('english', content)` (see the migration; no
    stored/generated column, so this query's expression and the index's
    expression are kept identical on purpose — see that migration's
    docstring).

    Falls back to a plain case-insensitive substring match on SQLite —
    this codebase's test-only dialect (tests/conftest.py) — so
    everything built on top of retrieval (fusion, the context builder,
    the prompt builder) stays testable without a running Postgres. The
    real ranking function only ever executes against real Postgres.
    """
    dialect = db.bind.dialect.name if db.bind is not None else "postgresql"
    if dialect == "postgresql":
        return await _keyword_search_postgres(db, project_id, query_text, top_k=top_k, filters=filters)
    return await _keyword_search_fallback(db, project_id, query_text, top_k=top_k, filters=filters)


async def _keyword_search_postgres(
    db: AsyncSession,
    project_id: uuid.UUID,
    query_text: str,
    *,
    top_k: int,
    filters: RetrievalFilters | None,
) -> list[RetrievedChunk]:
    tsquery = func.websearch_to_tsquery("english", query_text)
    tsvector = func.to_tsvector("english", ProjectDocumentChunk.content)
    rank = func.ts_rank_cd(tsvector, tsquery)

    stmt = (
        select(ProjectDocumentChunk, ProjectDocument, rank.label("rank"))
        .join(ProjectDocument, ProjectDocument.id == ProjectDocumentChunk.document_id)
        .where(
            ProjectDocumentChunk.project_id == project_id,
            ProjectDocument.deleted_at.is_(None),
            tsvector.op("@@")(tsquery),
        )
    )
    stmt = _apply_filters(stmt, filters).order_by(rank.desc()).limit(top_k)

    result = await db.execute(stmt)
    chunks: list[RetrievedChunk] = []
    for rank_index, (chunk, document, rank_value) in enumerate(result.all(), start=1):
        retrieved = _row_to_chunk(chunk, document)
        retrieved.keyword_score = float(rank_value)
        retrieved.keyword_rank = rank_index
        chunks.append(retrieved)
    return chunks


_WORD_RE = re.compile(r"[a-z0-9]+")


def _tokenize(text: str) -> list[str]:
    """Lowercase, punctuation-stripped word tokens — used for both the
    query and each chunk's content, so a natural-language question
    ("What Node version?") matches content on the word "node", not on
    the literal substring "node?" which never occurs anywhere. Also
    avoids the substring-match false positive a naive `in` check would
    have (e.g. counting "cat" as found inside "concatenate")."""
    return _WORD_RE.findall(text.lower())


async def _keyword_search_fallback(
    db: AsyncSession,
    project_id: uuid.UUID,
    query_text: str,
    *,
    top_k: int,
    filters: RetrievalFilters | None,
) -> list[RetrievedChunk]:
    terms = _tokenize(query_text)
    if not terms:
        return []

    stmt = (
        select(ProjectDocumentChunk, ProjectDocument)
        .join(ProjectDocument, ProjectDocument.id == ProjectDocumentChunk.document_id)
        .where(
            ProjectDocumentChunk.project_id == project_id,
            ProjectDocument.deleted_at.is_(None),
        )
    )
    stmt = _apply_filters(stmt, filters)
    result = await db.execute(stmt)

    scored: list[tuple[float, ProjectDocumentChunk, ProjectDocument]] = []
    for chunk, document in result.all():
        content_tokens = _tokenize(chunk.content)
        match_count = sum(content_tokens.count(term) for term in terms)
        if match_count > 0:
            scored.append((float(match_count), chunk, document))
    scored.sort(key=lambda item: item[0], reverse=True)

    chunks: list[RetrievedChunk] = []
    for rank_index, (match_score, chunk, document) in enumerate(scored[:top_k], start=1):
        retrieved = _row_to_chunk(chunk, document)
        retrieved.keyword_score = match_score
        retrieved.keyword_rank = rank_index
        chunks.append(retrieved)
    return chunks


def reciprocal_rank_fusion(ranked_lists: list[list[RetrievedChunk]], *, k: int) -> list[RetrievedChunk]:
    """Combines ranked lists by rank *position*, never by raw score —
    see this module's docstring. `k` (default 60, the constant from the
    original RRF paper) smooths the influence of exact rank: a chunk
    ranked #1 by one retriever and unranked by the other still competes
    fairly against a chunk ranked #2-#3 by both.

    Never mutates the `RetrievedChunk` objects in `ranked_lists` —
    returns fresh copies with `.score` (and merged vector_*/keyword_*
    fields) set on them instead. Mutating the inputs in place would
    make this function unsafe to call twice over the same candidate
    lists (e.g. comparing two `k` values against one retrieval), since
    the second call would silently overwrite the first call's result
    through the shared object references.
    """
    fused_scores: dict[uuid.UUID, float] = {}
    by_id: dict[uuid.UUID, RetrievedChunk] = {}

    for ranked_list in ranked_lists:
        for rank, chunk in enumerate(ranked_list, start=1):
            fused_scores[chunk.chunk_id] = fused_scores.get(chunk.chunk_id, 0.0) + 1.0 / (k + rank)
            existing = by_id.get(chunk.chunk_id)
            if existing is None:
                by_id[chunk.chunk_id] = replace(chunk)
            else:
                # A chunk both retrievers found should carry both
                # signals on the one canonical copy, not whichever
                # list happened to be merged into `by_id` first.
                existing.vector_score = existing.vector_score if existing.vector_score is not None else chunk.vector_score
                existing.vector_rank = existing.vector_rank if existing.vector_rank is not None else chunk.vector_rank
                existing.keyword_score = existing.keyword_score if existing.keyword_score is not None else chunk.keyword_score
                existing.keyword_rank = existing.keyword_rank if existing.keyword_rank is not None else chunk.keyword_rank

    for chunk_id, fused_score in fused_scores.items():
        by_id[chunk_id].score = fused_score

    return sorted(by_id.values(), key=lambda c: c.score, reverse=True)


async def hybrid_search(
    db: AsyncSession,
    project_id: uuid.UUID,
    query_text: str,
    query_embedding: list[float],
    *,
    top_k: int,
    vector_candidates: int,
    keyword_candidates: int,
    rrf_k: int,
    filters: RetrievalFilters | None = None,
) -> list[RetrievedChunk]:
    """The default retrieval mode — see
    docs/architecture/rag-engine-v1.md Section 4 for why hybrid beats
    either retriever alone. Pulls `vector_candidates`/`keyword_candidates`
    from each retriever (deliberately wider than `top_k` — RRF needs a
    real ranked list from each side to fuse, not just the final count)
    and returns the fused top `top_k`.
    """
    vector_results = await semantic_search(
        db, project_id, query_embedding, top_k=vector_candidates, filters=filters
    )
    keyword_results = await keyword_search(
        db, project_id, query_text, top_k=keyword_candidates, filters=filters
    )
    fused = reciprocal_rank_fusion([vector_results, keyword_results], k=rrf_k)
    return fused[:top_k]
