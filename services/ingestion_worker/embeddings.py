"""Embedding client for the worker — independent of apps/api's
llm_gateway (same extraction-boundary reasoning as db.py/settings.py:
this worker never imports app.*). Talks to Ollama's REST API directly
via httpx (already a worker dependency for GitHub/website fetches)
rather than adding the `ollama` Python package as a second HTTP client
just for this one call.

This is the *ingestion-side* half of the RAG Knowledge Engine's
embedding story — it turns already-chunked, already-stored text into
vectors. Query-time embedding (embedding the user's question at
retrieval time) is apps/api's llm_gateway's job instead; the two never
share code, only the same model name/dimension convention
(schemas.EMBEDDING_DIMENSIONS).
"""

import httpx

from pipeline.errors import PermanentIngestionError, RetryableIngestionError
from settings import config


async def embed_batch(client: httpx.AsyncClient, texts: list[str]) -> list[list[float]]:
    """One Ollama /api/embed call for up to `embedding_batch_size` texts.
    Callers (embed_document_chunks in worker.py) are responsible for
    chunking their input into batches — kept separate so batch-size
    policy lives in one place (worker.py, next to the retry/error
    handling it interacts with) rather than being buried in this
    low-level HTTP call.
    """
    if not texts:
        return []

    try:
        response = await client.post(
            f"{config.ollama_base_url}/api/embed",
            json={"model": config.ollama_embedding_model, "input": texts},
            timeout=config.embedding_fetch_timeout_seconds,
        )
    except httpx.TimeoutException as exc:
        raise RetryableIngestionError(
            f"Timed out calling Ollama embeddings API: {exc}", error_code="embedding_timeout"
        ) from exc
    except httpx.TransportError as exc:
        raise RetryableIngestionError(
            f"Network error calling Ollama embeddings API: {exc}", error_code="embedding_network_error"
        ) from exc

    if response.status_code >= 500:
        raise RetryableIngestionError(
            f"Ollama embeddings API returned {response.status_code}: {response.text}",
            error_code="embedding_upstream_error",
        )
    if response.status_code == 404:
        # Almost always "the embedding model isn't pulled" — retrying
        # the same job won't fix that; someone needs to run
        # `ollama pull nomic-embed-text` (see infra/docker/ollama/entrypoint.sh).
        raise PermanentIngestionError(
            f"Ollama embedding model '{config.ollama_embedding_model}' not found: {response.text}",
            error_code="embedding_model_not_found",
        )
    if response.status_code >= 400:
        raise PermanentIngestionError(
            f"Ollama embeddings API rejected the request ({response.status_code}): {response.text}",
            error_code="embedding_request_invalid",
        )

    body = response.json()
    embeddings = body.get("embeddings")
    if not isinstance(embeddings, list) or len(embeddings) != len(texts):
        raise RetryableIngestionError(
            "Ollama embeddings API returned a malformed response (embeddings count mismatch).",
            error_code="embedding_malformed_response",
        )
    return embeddings
