"""Unit tests for embeddings.embed_batch — uses httpx.MockTransport
(built into httpx, no extra dependency) to simulate Ollama's /api/embed
responses without a real Ollama server."""

import json

import httpx
import pytest

from embeddings import embed_batch
from pipeline.errors import PermanentIngestionError, RetryableIngestionError


def _client_with_handler(handler) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


class TestEmbedBatch:
    async def test_empty_input_returns_empty_without_a_request(self):
        def handler(request: httpx.Request) -> httpx.Response:
            raise AssertionError("should never be called for empty input")

        async with _client_with_handler(handler) as client:
            assert await embed_batch(client, []) == []

    async def test_returns_one_vector_per_input_text(self):
        def handler(request: httpx.Request) -> httpx.Response:
            payload = json.loads(request.read())
            return httpx.Response(200, json={"embeddings": [[0.1, 0.2]] * len(payload["input"])})

        async with _client_with_handler(handler) as client:
            result = await embed_batch(client, ["a", "b", "c"])

        assert result == [[0.1, 0.2], [0.1, 0.2], [0.1, 0.2]]

    async def test_sends_configured_model_and_all_texts_in_one_request(self):
        captured = {}

        def handler(request: httpx.Request) -> httpx.Response:
            captured["payload"] = json.loads(request.read())
            return httpx.Response(200, json={"embeddings": [[0.0]] * 2})

        async with _client_with_handler(handler) as client:
            await embed_batch(client, ["x", "y"])

        assert captured["payload"]["input"] == ["x", "y"]
        assert "model" in captured["payload"]

    async def test_404_raises_permanent_model_not_found(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(404, text="model not found")

        async with _client_with_handler(handler) as client:
            with pytest.raises(PermanentIngestionError) as exc_info:
                await embed_batch(client, ["a"])
        assert exc_info.value.error_code == "embedding_model_not_found"

    async def test_400_raises_permanent_request_invalid(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(400, text="bad request")

        async with _client_with_handler(handler) as client:
            with pytest.raises(PermanentIngestionError) as exc_info:
                await embed_batch(client, ["a"])
        assert exc_info.value.error_code == "embedding_request_invalid"

    async def test_500_raises_retryable_upstream_error(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(500, text="internal error")

        async with _client_with_handler(handler) as client:
            with pytest.raises(RetryableIngestionError) as exc_info:
                await embed_batch(client, ["a"])
        assert exc_info.value.error_code == "embedding_upstream_error"

    async def test_malformed_response_raises_retryable(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={"embeddings": [[0.0]]})  # only 1, but 2 texts sent

        async with _client_with_handler(handler) as client:
            with pytest.raises(RetryableIngestionError) as exc_info:
                await embed_batch(client, ["a", "b"])
        assert exc_info.value.error_code == "embedding_malformed_response"

    async def test_missing_embeddings_key_raises_retryable(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={"unexpected": "shape"})

        async with _client_with_handler(handler) as client:
            with pytest.raises(RetryableIngestionError) as exc_info:
                await embed_batch(client, ["a"])
        assert exc_info.value.error_code == "embedding_malformed_response"

    async def test_timeout_raises_retryable(self):
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.TimeoutException("timed out")

        async with _client_with_handler(handler) as client:
            with pytest.raises(RetryableIngestionError) as exc_info:
                await embed_batch(client, ["a"])
        assert exc_info.value.error_code == "embedding_timeout"

    async def test_network_error_raises_retryable(self):
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("connection refused")

        async with _client_with_handler(handler) as client:
            with pytest.raises(RetryableIngestionError) as exc_info:
                await embed_batch(client, ["a"])
        assert exc_info.value.error_code == "embedding_network_error"
