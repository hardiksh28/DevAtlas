"""RAG orchestration — the /ask endpoint's actual implementation.

Embed query -> retrieve (vector/keyword/hybrid) -> build context ->
build prompt -> generate -> package. Every stage before "generate" is
pure Python/SQL and cheap; "generate" is the one call that talks to
Ollama and the one thing worth caching (see cache.py) and worth
insulating behind its own error type (RetrievalServiceUnavailableError)
rather than letting an httpx/ollama exception reach the router as a
raw 500.
"""

import logging
import uuid
from dataclasses import dataclass
from typing import Any

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.modules.knowledge.exceptions import RetrievalServiceUnavailableError
from app.modules.knowledge.retrieval import cache
from app.modules.knowledge.retrieval.context_builder import ContextSource, build_context
from app.modules.knowledge.retrieval.prompt_builder import build_prompt
from app.modules.knowledge.retrieval.prompt_templates import NO_RESULTS_ANSWER
from app.modules.knowledge.retrieval.retrieval_service import (
    RetrievalFilters,
    RetrievedChunk,
    hybrid_search,
    keyword_search,
    semantic_search,
)
from app.modules.llm_gateway.gateway import LLMGateway

settings = get_settings()
logger = logging.getLogger(__name__)


@dataclass
class RagAnswer:
    answer: str
    sources: list[ContextSource]
    chunks_retrieved: int
    context_tokens: int
    truncated: bool
    cached: bool
    retrieval_mode: str


def _source_to_dict(source: ContextSource) -> dict[str, Any]:
    return {
        "index": source.index,
        "chunk_id": str(source.chunk_id),
        "document_id": str(source.document_id),
        "title": source.title,
        "source_type": source.source_type,
        "source_path": source.source_path,
        "heading_path": source.heading_path,
        "score": source.score,
    }


def _dict_to_source(data: dict[str, Any]) -> ContextSource:
    # Inverse of _source_to_dict — restores real UUID objects so a
    # cache-hit RagAnswer's sources are shaped identically to a
    # freshly-computed one, not "usually a UUID, sometimes a str."
    return ContextSource(
        index=data["index"],
        chunk_id=uuid.UUID(data["chunk_id"]),
        document_id=uuid.UUID(data["document_id"]),
        title=data["title"],
        source_type=data["source_type"],
        source_path=data["source_path"],
        heading_path=data["heading_path"],
        score=data["score"],
    )


def _answer_to_cache_payload(result: RagAnswer) -> dict[str, Any]:
    return {
        "answer": result.answer,
        "sources": [_source_to_dict(s) for s in result.sources],
        "chunks_retrieved": result.chunks_retrieved,
        "context_tokens": result.context_tokens,
        "truncated": result.truncated,
        "retrieval_mode": result.retrieval_mode,
    }


async def _embed_query(gateway: LLMGateway, question: str) -> list[float]:
    try:
        vectors = await gateway.embed([question])
    except Exception as exc:  # deliberately broad — any embed failure means retrieval is unavailable
        # Logged with full detail server-side; the client only ever
        # sees the generic message below. `str(exc)` can include
        # internal infra detail (the Ollama host/port, a raw connection
        # error) that has no business appearing in an API response body.
        logger.warning("Query embedding failed: %s", exc)
        raise RetrievalServiceUnavailableError(
            "Could not embed the query — the embedding service is unavailable."
        ) from exc
    return vectors[0]


async def retrieve_chunks(
    db: AsyncSession,
    gateway: LLMGateway,
    project_id: uuid.UUID,
    question: str,
    *,
    mode: str,
    top_k: int,
    filters: RetrievalFilters | None = None,
) -> list[RetrievedChunk]:
    """Mode dispatch shared by `answer_question` (below) and
    router.py's `/search` handler — the one place that decides which
    retriever(s) a given `mode` maps to, so the two callers can never
    silently drift into answering "hybrid" differently."""
    if mode == "keyword":
        return await keyword_search(db, project_id, question, top_k=top_k, filters=filters)

    query_embedding = await _embed_query(gateway, question)

    if mode == "vector":
        return await semantic_search(db, project_id, query_embedding, top_k=top_k, filters=filters)

    # "hybrid" — the default, and the only other value the request
    # schema's Literal allows (see knowledge/schemas.py); the ValueError
    # below is unreachable through the API but keeps this function
    # honest if it's ever called directly with a bad mode.
    if mode == "hybrid":
        return await hybrid_search(
            db,
            project_id,
            question,
            query_embedding,
            top_k=top_k,
            vector_candidates=settings.retrieval_vector_candidates,
            keyword_candidates=settings.retrieval_keyword_candidates,
            rrf_k=settings.retrieval_rrf_k,
            filters=filters,
        )
    raise ValueError(f"Unknown retrieval mode: {mode!r}")


async def answer_question(
    db: AsyncSession,
    gateway: LLMGateway,
    redis: Redis,
    *,
    project_id: uuid.UUID,
    question: str,
    mode: str = "hybrid",
    top_k: int | None = None,
    filters: RetrievalFilters | None = None,
    use_cache: bool = True,
) -> RagAnswer:
    effective_top_k = top_k or settings.retrieval_top_k
    cache_key = cache.build_cache_key(
        project_id,
        question,
        mode=mode,
        top_k=effective_top_k,
        source_types=filters.source_types if filters else None,
        document_ids=filters.document_ids if filters else None,
    )

    if use_cache:
        cached_payload = await cache.get_cached_answer(redis, cache_key)
        if cached_payload is not None:
            return RagAnswer(
                answer=cached_payload["answer"],
                sources=[_dict_to_source(s) for s in cached_payload["sources"]],
                chunks_retrieved=cached_payload["chunks_retrieved"],
                context_tokens=cached_payload["context_tokens"],
                truncated=cached_payload["truncated"],
                cached=True,
                retrieval_mode=cached_payload["retrieval_mode"],
            )

    chunks = await retrieve_chunks(
        db, gateway, project_id, question, mode=mode, top_k=effective_top_k, filters=filters
    )

    if not chunks:
        # Deliberately NOT cached: an empty corpus today may have
        # results the moment the next ingestion job completes, and
        # caching "no results" would keep serving that answer past its
        # truth for the full TTL — the one case where skipping the
        # cache is more correct than using it (Section 9).
        return RagAnswer(
            answer=NO_RESULTS_ANSWER,
            sources=[],
            chunks_retrieved=0,
            context_tokens=0,
            truncated=False,
            cached=False,
            retrieval_mode=mode,
        )

    context = build_context(chunks, max_tokens=settings.context_max_tokens)
    prompt = build_prompt(context, question)

    try:
        answer_text = await gateway.generate("rag_answer", prompt)
    except Exception as exc:  # deliberately broad — any generate failure means retrieval is unavailable
        logger.warning("Answer generation failed: %s", exc)
        raise RetrievalServiceUnavailableError(
            "Could not generate an answer — the LLM service is unavailable."
        ) from exc

    result = RagAnswer(
        answer=answer_text,
        sources=context.sources,
        chunks_retrieved=len(chunks),
        context_tokens=context.total_tokens,
        truncated=context.truncated,
        cached=False,
        retrieval_mode=mode,
    )

    if use_cache:
        await cache.set_cached_answer(
            redis, cache_key, _answer_to_cache_payload(result), ttl_seconds=settings.retrieval_cache_ttl_seconds
        )
    return result
