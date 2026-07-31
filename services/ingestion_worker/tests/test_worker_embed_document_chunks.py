"""Unit tests for worker.embed_document_chunks — the orchestration
logic (batching, per-batch failure isolation, final document status).

Monkeypatches `db.*` and `worker.embed_batch` rather than hitting a real
Postgres/Ollama — this module owns the *decisions* (what to do with a
batch that fails, when to mark the document complete); the actual
persistence (db.py) and HTTP call (embeddings.py) are tested separately
(no DB/network integration test exists for this worker — see
services/ingestion_worker's own CI job, which runs against no live
Postgres either; this mirrors that same constraint).
"""

import uuid

import pytest

import worker
from pipeline.errors import PermanentIngestionError, RetryableIngestionError


class FakeDb:
    """Records every call worker.embed_document_chunks makes through
    `db.*`, and serves canned pending-chunk data."""

    def __init__(self, pending_chunks: list[dict]) -> None:
        self.pending_chunks = pending_chunks
        self.upserted: list[dict] = []
        self.status_updates: list[tuple[list, str]] = []
        self.document_updates: list[dict] = []

    async def get_pending_embedding_chunks(self, document_id):
        return self.pending_chunks

    async def upsert_embeddings(self, rows):
        self.upserted.extend(rows)

    async def set_chunks_embedding_status(self, chunk_ids, status):
        self.status_updates.append((list(chunk_ids), status))

    async def update_document(self, document_id, **values):
        self.document_updates.append(values)


def _pending_chunk(content: str = "some content", project_id=None) -> dict:
    return {
        "id": uuid.uuid4(),
        "document_id": uuid.uuid4(),
        "project_id": project_id or uuid.uuid4(),
        "content": content,
    }


@pytest.fixture
def document_id() -> str:
    return str(uuid.uuid4())


class TestEmbedDocumentChunks:
    async def test_no_pending_chunks_marks_document_completed_without_embedding(
        self, monkeypatch, document_id
    ):
        fake_db = FakeDb(pending_chunks=[])
        monkeypatch.setattr(worker, "db", fake_db)

        async def fail_if_called(*args, **kwargs):
            raise AssertionError("embed_batch should never be called with zero pending chunks")

        monkeypatch.setattr(worker, "embed_batch", fail_if_called)

        await worker.embed_document_chunks({}, document_id)

        assert fake_db.document_updates == [{"status": "completed"}]

    async def test_successful_batch_upserts_and_marks_chunks_completed(self, monkeypatch, document_id):
        chunk = _pending_chunk()
        fake_db = FakeDb(pending_chunks=[chunk])
        monkeypatch.setattr(worker, "db", fake_db)

        async def fake_embed_batch(client, texts):
            return [[0.1] * 768 for _ in texts]

        monkeypatch.setattr(worker, "embed_batch", fake_embed_batch)

        await worker.embed_document_chunks({}, document_id)

        assert len(fake_db.upserted) == 1
        assert fake_db.upserted[0]["chunk_id"] == chunk["id"]
        assert fake_db.status_updates == [([chunk["id"]], "completed")]
        assert fake_db.document_updates == [{"status": "completed"}]

    async def test_batches_respect_configured_batch_size(self, monkeypatch, document_id):
        chunks = [_pending_chunk() for _ in range(5)]
        fake_db = FakeDb(pending_chunks=chunks)
        monkeypatch.setattr(worker, "db", fake_db)
        monkeypatch.setattr(worker.config, "embedding_batch_size", 2)

        batch_sizes_seen = []

        async def fake_embed_batch(client, texts):
            batch_sizes_seen.append(len(texts))
            return [[0.1] * 768 for _ in texts]

        monkeypatch.setattr(worker, "embed_batch", fake_embed_batch)

        await worker.embed_document_chunks({}, document_id)

        assert batch_sizes_seen == [2, 2, 1]  # 5 chunks, batch size 2 -> 2+2+1
        assert len(fake_db.upserted) == 5

    async def test_permanent_error_in_one_batch_marks_it_failed_and_continues(self, monkeypatch, document_id):
        chunks = [_pending_chunk(content="bad content"), _pending_chunk(content="good content")]
        fake_db = FakeDb(pending_chunks=chunks)
        monkeypatch.setattr(worker, "db", fake_db)
        monkeypatch.setattr(worker.config, "embedding_batch_size", 1)

        async def fake_embed_batch(client, texts):
            if texts[0] == "bad content":
                raise PermanentIngestionError("bad batch", error_code="embedding_request_invalid")
            return [[0.1] * 768]

        monkeypatch.setattr(worker, "embed_batch", fake_embed_batch)

        await worker.embed_document_chunks({}, document_id)

        assert fake_db.status_updates[0] == ([chunks[0]["id"]], "failed")
        assert fake_db.status_updates[1] == ([chunks[1]["id"]], "completed")
        # The document still reaches 'completed' — a per-chunk embedding
        # failure doesn't block the ingestion pipeline's own completion
        # status (see embed_document_chunks' docstring).
        assert fake_db.document_updates == [{"status": "completed"}]

    async def test_retryable_error_propagates_and_stops_processing_remaining_batches(
        self, monkeypatch, document_id
    ):
        chunks = [_pending_chunk() for _ in range(2)]
        fake_db = FakeDb(pending_chunks=chunks)
        monkeypatch.setattr(worker, "db", fake_db)
        monkeypatch.setattr(worker.config, "embedding_batch_size", 1)

        async def fake_embed_batch(client, texts):
            raise RetryableIngestionError("ollama down", error_code="embedding_upstream_error")

        monkeypatch.setattr(worker, "embed_batch", fake_embed_batch)

        with pytest.raises(RetryableIngestionError):
            await worker.embed_document_chunks({}, document_id)

        # Never reached the "mark document completed" step, and never
        # marked any chunk's status — the whole job aborts for arq to retry.
        assert fake_db.document_updates == []
        assert fake_db.status_updates == []
