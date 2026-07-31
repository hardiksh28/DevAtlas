"""Integration tests for app.modules.knowledge.router.

Drives the real FastAPI app end-to-end (see tests/conftest.py's `client`
fixture). `get_queue`/`get_storage` are additionally overridden here
(FakeQueue records enqueue_job calls instead of needing a real Redis
broker; LocalObjectStorage writes under pytest's tmp_path instead of
needing MinIO/S3) — the same "swap the backend, keep the interface"
approach conftest.py already uses for the DB and for `get_redis`.
"""

import io

import pytest_asyncio
from object_storage import LocalObjectStorage

from app.core.queue import get_queue
from app.core.storage import get_storage


class FakeQueue:
    def __init__(self) -> None:
        self.enqueued: list[tuple[str, tuple]] = []

    async def enqueue_job(self, function: str, *args: object, **kwargs: object) -> None:
        self.enqueued.append((function, args))


@pytest_asyncio.fixture
async def ingestion(client, tmp_path):
    """Yields (client, fake_queue) with storage/queue dependencies
    overridden on the same app instance `client` already talks to."""
    from app.main import app as fastapi_app

    fake_queue = FakeQueue()
    storage = LocalObjectStorage(tmp_path)
    fastapi_app.dependency_overrides[get_queue] = lambda: fake_queue
    fastapi_app.dependency_overrides[get_storage] = lambda: storage
    yield client, fake_queue


async def _register(client, email="user@example.com"):
    return await client.post(
        "/v1/auth/register",
        json={"email": email, "password": "hunter22222", "display_name": "User One"},
    )


async def _create_project(client, name="Docs Project"):
    resp = await client.post("/v1/projects", json={"name": name})
    return resp.json()["id"]


class TestUploadDocument:
    async def test_requires_auth(self, ingestion):
        client, _ = ingestion
        resp = await client.post(
            f"/v1/projects/{'00000000-0000-0000-0000-000000000000'}/documents/uploads",
            files={"file": ("intro.md", io.BytesIO(b"# Hi"), "text/markdown")},
        )
        assert resp.status_code == 401

    async def test_uploads_markdown_and_enqueues_processing(self, ingestion):
        client, fake_queue = ingestion
        await _register(client, email="upload@example.com")
        project_id = await _create_project(client)

        resp = await client.post(
            f"/v1/projects/{project_id}/documents/uploads",
            files={"file": ("intro.md", io.BytesIO(b"# Hello\n\nWorld"), "text/markdown")},
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["job"]["source_type"] == "markdown_file"
        assert body["job"]["status"] == "processing"
        assert body["document"]["source_path"] == "intro.md"
        assert body["document"]["metadata"] == {}
        assert fake_queue.enqueued == [("process_document", (body["document"]["id"],))]

    async def test_rejects_unsupported_file(self, ingestion):
        client, _ = ingestion
        await _register(client, email="badfile@example.com")
        project_id = await _create_project(client)

        resp = await client.post(
            f"/v1/projects/{project_id}/documents/uploads",
            files={"file": ("virus.exe", io.BytesIO(b"MZ\x90\x00"), "application/octet-stream")},
        )
        assert resp.status_code == 422
        assert resp.json()["error_code"] == "unsupported_source"

    async def test_upload_to_another_users_project_is_404(self, ingestion):
        client, _ = ingestion
        await _register(client, email="owner@example.com")
        project_id = await _create_project(client)
        await client.post("/v1/auth/logout")
        await _register(client, email="intruder@example.com")

        resp = await client.post(
            f"/v1/projects/{project_id}/documents/uploads",
            files={"file": ("intro.md", io.BytesIO(b"# Hi"), "text/markdown")},
        )
        assert resp.status_code == 404


class TestGithubIngest:
    async def test_creates_job(self, ingestion):
        client, fake_queue = ingestion
        await _register(client, email="gh@example.com")
        project_id = await _create_project(client)

        resp = await client.post(
            f"/v1/projects/{project_id}/documents/github",
            json={"repo_url": "https://github.com/octocat/Hello-World"},
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["source_type"] == "github_repo"
        assert body["status"] == "queued"
        assert fake_queue.enqueued == [("discover_github_documents", (body["id"],))]

    async def test_rejects_non_github_host(self, ingestion):
        client, _ = ingestion
        await _register(client, email="gh2@example.com")
        project_id = await _create_project(client)

        resp = await client.post(
            f"/v1/projects/{project_id}/documents/github",
            json={"repo_url": "https://gitlab.com/owner/repo"},
        )
        assert resp.status_code == 422
        assert resp.json()["error_code"] == "invalid_source_url"


class TestWebsiteIngest:
    async def test_creates_job(self, ingestion):
        client, fake_queue = ingestion
        await _register(client, email="site@example.com")
        project_id = await _create_project(client)

        resp = await client.post(
            f"/v1/projects/{project_id}/documents/website",
            json={"url": "https://docs.example.com/"},
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["source_type"] == "website"
        assert fake_queue.enqueued == [("discover_website_documents", (body["id"],))]

    async def test_rejects_private_network_target(self, ingestion):
        client, _ = ingestion
        await _register(client, email="ssrf@example.com")
        project_id = await _create_project(client)

        resp = await client.post(
            f"/v1/projects/{project_id}/documents/website",
            json={"url": "http://127.0.0.1/"},
        )
        assert resp.status_code == 422
        assert resp.json()["error_code"] == "invalid_source_url"


class TestJobsAndDocuments:
    async def test_list_and_get_job(self, ingestion):
        client, _ = ingestion
        await _register(client, email="jobs@example.com")
        project_id = await _create_project(client)
        created = await client.post(
            f"/v1/projects/{project_id}/documents/uploads",
            files={"file": ("a.md", io.BytesIO(b"# A"), "text/markdown")},
        )
        job_id = created.json()["job"]["id"]

        listed = await client.get(f"/v1/projects/{project_id}/documents/jobs")
        assert listed.status_code == 200
        assert listed.json()["total"] == 1

        detail = await client.get(f"/v1/projects/{project_id}/documents/jobs/{job_id}")
        assert detail.status_code == 200
        assert detail.json()["id"] == job_id

    async def test_unknown_job_is_404(self, ingestion):
        client, _ = ingestion
        await _register(client, email="jobs404@example.com")
        project_id = await _create_project(client)

        resp = await client.get(
            f"/v1/projects/{project_id}/documents/jobs/00000000-0000-0000-0000-000000000000"
        )
        assert resp.status_code == 404
        assert resp.json()["error_code"] == "ingestion_job_not_found"

    async def test_get_list_and_delete_document(self, ingestion):
        client, _ = ingestion
        await _register(client, email="docs@example.com")
        project_id = await _create_project(client)
        created = await client.post(
            f"/v1/projects/{project_id}/documents/uploads",
            files={"file": ("a.md", io.BytesIO(b"# A"), "text/markdown")},
        )
        document_id = created.json()["document"]["id"]

        listed = await client.get(f"/v1/projects/{project_id}/documents")
        assert listed.status_code == 200
        assert listed.json()["total"] == 1

        detail = await client.get(f"/v1/projects/{project_id}/documents/{document_id}")
        assert detail.status_code == 200

        chunks = await client.get(f"/v1/projects/{project_id}/documents/{document_id}/chunks")
        assert chunks.status_code == 200
        assert chunks.json()["items"] == []  # worker hasn't run in this test

        deleted = await client.delete(f"/v1/projects/{project_id}/documents/{document_id}")
        assert deleted.status_code == 204

        after_delete = await client.get(f"/v1/projects/{project_id}/documents/{document_id}")
        assert after_delete.status_code == 404
        assert after_delete.json()["error_code"] == "document_not_found"
