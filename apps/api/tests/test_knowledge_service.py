"""Integration tests for app.modules.knowledge.service.

Exercises the service layer against a real AsyncSession/schema (see
tests/conftest.py) and a real LocalObjectStorage backed by a pytest
tmp_path — no mocking of storage, just the cheaper backend
(object_storage.LocalObjectStorage) the same way conftest.py's SQLite
fallback stands in for Postgres. FakeQueue stands in for arq's ArqRedis
so these tests never need a real Redis broker.
"""

import uuid

import pytest
from object_storage import LocalObjectStorage

from app.core.config import get_settings
from app.modules.auth import service as auth_service
from app.modules.knowledge import service
from app.modules.knowledge.exceptions import (
    IngestionJobLimitExceededError,
    IngestionJobNotFoundError,
    InvalidSourceUrlError,
    ProjectDocumentNotFoundError,
    UnsupportedSourceError,
    UploadTooLargeError,
)
from app.modules.projects import service as projects_service

settings = get_settings()


class FakeQueue:
    def __init__(self) -> None:
        self.enqueued: list[tuple[str, tuple]] = []

    async def enqueue_job(self, function: str, *args: object, **kwargs: object) -> None:
        self.enqueued.append((function, args))


async def _make_user_and_project(db, email="owner@example.com"):
    user = await auth_service.register_user(db, email, "hunter22222", "Owner")
    project = await projects_service.create_project(db, user.id, "Docs Project", None)
    return user, project


class TestCreateUploadJob:
    async def test_creates_job_and_document_for_markdown(self, db_session, tmp_path):
        user, project = await _make_user_and_project(db_session)
        storage = LocalObjectStorage(tmp_path)
        queue = FakeQueue()

        job, document = await service.create_upload_job(
            db_session,
            storage,
            queue,
            project_id=project.id,
            user_id=user.id,
            filename="intro.md",
            content_type="text/markdown",
            data=b"# Hello\n\nWorld",
        )

        assert job.source_type == "markdown_file"
        assert job.status == "processing"
        assert job.documents_discovered == 1
        assert document.source_path == "intro.md"
        assert document.checksum
        assert document.raw_storage_key is not None
        assert await storage.exists(document.raw_storage_key)
        assert queue.enqueued == [("process_document", (str(document.id),))]

    async def test_detects_pdf_from_magic_bytes(self, db_session, tmp_path):
        user, project = await _make_user_and_project(db_session, email="pdf@example.com")
        storage = LocalObjectStorage(tmp_path)
        queue = FakeQueue()

        job, document = await service.create_upload_job(
            db_session,
            storage,
            queue,
            project_id=project.id,
            user_id=user.id,
            filename="guide.pdf",
            content_type="application/pdf",
            data=b"%PDF-1.4 minimal fake body",
        )
        assert job.source_type == "pdf_file"
        assert document.mime_type == "application/pdf"

    async def test_rejects_unsupported_file_type(self, db_session, tmp_path):
        user, project = await _make_user_and_project(db_session, email="unsupported@example.com")
        storage = LocalObjectStorage(tmp_path)
        queue = FakeQueue()

        with pytest.raises(UnsupportedSourceError):
            await service.create_upload_job(
                db_session,
                storage,
                queue,
                project_id=project.id,
                user_id=user.id,
                filename="virus.exe",
                content_type="application/octet-stream",
                data=b"MZ\x90\x00",
            )

    async def test_rejects_pdf_without_pdf_magic_bytes(self, db_session, tmp_path):
        user, project = await _make_user_and_project(db_session, email="badpdf@example.com")
        storage = LocalObjectStorage(tmp_path)
        queue = FakeQueue()

        with pytest.raises(UnsupportedSourceError):
            await service.create_upload_job(
                db_session,
                storage,
                queue,
                project_id=project.id,
                user_id=user.id,
                filename="fake.pdf",
                content_type="application/pdf",
                data=b"not a real pdf",
            )

    async def test_rejects_oversized_upload(self, db_session, tmp_path, monkeypatch):
        monkeypatch.setattr(settings, "ingestion_max_upload_bytes", 10)
        user, project = await _make_user_and_project(db_session, email="oversized@example.com")
        storage = LocalObjectStorage(tmp_path)
        queue = FakeQueue()

        with pytest.raises(UploadTooLargeError):
            await service.create_upload_job(
                db_session,
                storage,
                queue,
                project_id=project.id,
                user_id=user.id,
                filename="big.md",
                content_type="text/markdown",
                data=b"#" * 100,
            )

    async def test_enforces_active_job_limit(self, db_session, tmp_path, monkeypatch):
        monkeypatch.setattr(settings, "max_active_ingestion_jobs_per_project", 1)
        user, project = await _make_user_and_project(db_session, email="joblimit@example.com")
        storage = LocalObjectStorage(tmp_path)
        queue = FakeQueue()

        await service.create_upload_job(
            db_session,
            storage,
            queue,
            project_id=project.id,
            user_id=user.id,
            filename="one.md",
            content_type="text/markdown",
            data=b"# One",
        )
        # The first job is left in status="processing" (non-terminal),
        # so it counts against the ceiling — the second create is rejected.
        with pytest.raises(IngestionJobLimitExceededError):
            await service.create_upload_job(
                db_session,
                storage,
                queue,
                project_id=project.id,
                user_id=user.id,
                filename="two.md",
                content_type="text/markdown",
                data=b"# Two",
            )


class TestCreateGithubJob:
    async def test_creates_job_and_enqueues_discovery(self, db_session):
        user, project = await _make_user_and_project(db_session, email="gh@example.com")
        queue = FakeQueue()

        job = await service.create_github_job(
            db_session,
            queue,
            project_id=project.id,
            user_id=user.id,
            repo_url="https://github.com/octocat/Hello-World",
            ref=None,
        )

        assert job.source_type == "github_repo"
        assert job.status == "queued"
        assert job.source_input["owner"] == "octocat"
        assert job.source_input["repo"] == "Hello-World"
        assert queue.enqueued == [("discover_github_documents", (str(job.id),))]

    async def test_rejects_non_github_url(self, db_session):
        user, project = await _make_user_and_project(db_session, email="gh2@example.com")
        queue = FakeQueue()

        with pytest.raises(InvalidSourceUrlError):
            await service.create_github_job(
                db_session,
                queue,
                project_id=project.id,
                user_id=user.id,
                repo_url="https://gitlab.com/owner/repo",
                ref=None,
            )


class TestCreateWebsiteJob:
    async def test_creates_job_and_enqueues_discovery(self, db_session):
        user, project = await _make_user_and_project(db_session, email="site@example.com")
        queue = FakeQueue()

        job = await service.create_website_job(
            db_session,
            queue,
            project_id=project.id,
            user_id=user.id,
            url="https://docs.example.com/",
            max_pages=None,
            max_depth=None,
        )

        assert job.source_type == "website"
        assert job.status == "queued"
        assert queue.enqueued == [("discover_website_documents", (str(job.id),))]

    @pytest.mark.parametrize(
        "blocked_url",
        ["http://127.0.0.1/", "http://localhost/", "http://10.0.0.5/", "ftp://example.com/"],
    )
    async def test_rejects_private_or_invalid_targets(self, db_session, blocked_url):
        user, project = await _make_user_and_project(db_session, email=f"ssrf-{uuid.uuid4()}@example.com")
        queue = FakeQueue()

        with pytest.raises(InvalidSourceUrlError):
            await service.create_website_job(
                db_session,
                queue,
                project_id=project.id,
                user_id=user.id,
                url=blocked_url,
                max_pages=None,
                max_depth=None,
            )


class TestReadsAndDelete:
    async def test_get_document_not_found(self, db_session):
        _, project = await _make_user_and_project(db_session, email="notfound@example.com")
        with pytest.raises(ProjectDocumentNotFoundError):
            await service.get_document(db_session, project.id, uuid.uuid4())

    async def test_get_job_not_found(self, db_session):
        _, project = await _make_user_and_project(db_session, email="jobnotfound@example.com")
        with pytest.raises(IngestionJobNotFoundError):
            await service.get_job(db_session, project.id, uuid.uuid4())

    async def test_delete_document_soft_deletes(self, db_session, tmp_path):
        user, project = await _make_user_and_project(db_session, email="del@example.com")
        storage = LocalObjectStorage(tmp_path)
        queue = FakeQueue()
        _, document = await service.create_upload_job(
            db_session,
            storage,
            queue,
            project_id=project.id,
            user_id=user.id,
            filename="gone.md",
            content_type="text/markdown",
            data=b"# Gone",
        )

        await service.delete_document(db_session, document)

        with pytest.raises(ProjectDocumentNotFoundError):
            await service.get_document(db_session, project.id, document.id)

    async def test_list_documents_excludes_deleted(self, db_session, tmp_path):
        user, project = await _make_user_and_project(db_session, email="listexc@example.com")
        storage = LocalObjectStorage(tmp_path)
        queue = FakeQueue()
        _, kept = await service.create_upload_job(
            db_session,
            storage,
            queue,
            project_id=project.id,
            user_id=user.id,
            filename="kept.md",
            content_type="text/markdown",
            data=b"# Kept",
        )
        _, removed = await service.create_upload_job(
            db_session,
            storage,
            queue,
            project_id=project.id,
            user_id=user.id,
            filename="removed.md",
            content_type="text/markdown",
            data=b"# Removed",
        )
        await service.delete_document(db_session, removed)

        items, total = await service.list_documents(
            db_session, project.id, source_type=None, status=None, limit=20, offset=0
        )
        assert total == 1
        assert [d.id for d in items] == [kept.id]
