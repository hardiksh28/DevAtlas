"""Caching Strategy for the RAG Knowledge Engine — see
docs/architecture/rag-engine-v1.md Section 9.

A plain Redis GET/SETEX cache keyed on the exact
(project, normalized query, mode, top_k, filters) tuple — not a
semantic/approximate cache (no "close enough" query matching). An
approximate cache would mean occasionally serving a stale or subtly
wrong answer for a question that only *resembles* a cached one,
silently reintroducing the grounding problem this whole engine exists
to avoid, in exchange for a hit-rate improvement that's speculative
until there's real usage data to justify the added complexity.
"""

import hashlib
import json
import uuid
from typing import Any

from redis.asyncio import Redis

_CACHE_KEY_PREFIX = "rag:answer"


def build_cache_key(
    project_id: uuid.UUID,
    query: str,
    *,
    mode: str,
    top_k: int,
    source_types: list[str] | None,
    document_ids: list[uuid.UUID] | None,
) -> str:
    # Whitespace/case normalized so "What is X?" and "what is x?  "
    # share a cache entry — anything more aggressive (stemming,
    # embedding-similarity matching) is exactly the approximate caching
    # this module's docstring explains why V1 avoids.
    normalized_query = " ".join(query.strip().lower().split())
    filter_key = json.dumps(
        {
            "source_types": sorted(source_types) if source_types else None,
            "document_ids": sorted(str(d) for d in document_ids) if document_ids else None,
        },
        sort_keys=True,
    )
    digest = hashlib.sha256(f"{normalized_query}|{mode}|{top_k}|{filter_key}".encode()).hexdigest()
    return f"{_CACHE_KEY_PREFIX}:{project_id}:{digest}"


async def get_cached_answer(redis: Redis, key: str) -> dict[str, Any] | None:
    raw = await redis.get(key)
    if raw is None:
        return None
    return json.loads(raw)


async def set_cached_answer(redis: Redis, key: str, payload: dict[str, Any], *, ttl_seconds: int) -> None:
    await redis.set(key, json.dumps(payload), ex=ttl_seconds)
