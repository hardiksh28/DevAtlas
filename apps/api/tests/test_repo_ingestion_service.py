"""Integration tests for app.modules.repo_ingestion.service.

Exercises the service layer against a real AsyncSession/schema (see
tests/conftest.py) and an httpx.AsyncClient bound to a MockTransport —
no real network call, same "swap the cheaper backend" approach
test_knowledge_service.py uses for object storage.
"""

import httpx
import pytest

from app.modules.auth import service as auth_service
from app.modules.projects import service as projects_service
from app.modules.repo_ingestion import service
from app.modules.repo_ingestion.exceptions import (
    InvalidRepositoryUrlError,
    RepositoryConnectionNotFoundError,
    RepositoryNotFoundError,
)

_REPO_INFO = {
    "id": 123,
    "name": "demo-app",
    "default_branch": "main",
    "language": "TypeScript",
    "size": 100,
    "private": False,
}

_TREE = {
    "truncated": False,
    "tree": [
        {"path": "package.json", "type": "blob", "size": 100},
        {"path": "package-lock.json", "type": "blob", "size": 200},
        {"path": "README.md", "type": "blob", "size": 50},
        {"path": "src", "type": "tree"},
        {"path": "src/index.ts", "type": "blob", "size": 10},
        {"path": "node_modules", "type": "tree"},
        {"path": "node_modules/foo/index.js", "type": "blob", "size": 5},
    ],
}

_PACKAGE_JSON = b'{"dependencies": {"next": "^14.0.0", "react": "^18.0.0"}}'


def _make_handler(repo_info=_REPO_INFO, tree=_TREE, files: dict[str, bytes] | None = None):
    files = files or {"package.json": _PACKAGE_JSON, "README.md": b"# Demo\n\nHello."}

    def handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        if url.startswith("https://raw.githubusercontent.com/"):
            for name, content in files.items():
                if url.endswith(name):
                    return httpx.Response(200, content=content)
            return httpx.Response(404)
        if "/git/trees/" in url:
            return httpx.Response(200, json=tree)
        if "/repos/" in url:
            return httpx.Response(200, json=repo_info)
        return httpx.Response(404)

    return handler


def _make_client(handler) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


async def _make_user_and_project(db, email="owner@example.com"):
    user = await auth_service.register_user(db, email, "hunter22222", "Owner")
    project = await projects_service.create_project(db, user.id, "Code Project", None)
    return user, project


class TestSyncRepository:
    async def test_detects_language_framework_package_manager_and_counts(self, db_session):
        _, project = await _make_user_and_project(db_session)
        async with _make_client(_make_handler()) as client:
            connection = await service.sync_repository(
                db_session, client, project_id=project.id, repo_url="https://github.com/octo/demo-app"
            )

        assert connection.owner == "octo"
        assert connection.name == "demo-app"
        assert connection.default_branch == "main"
        assert connection.primary_language == "TypeScript"
        assert connection.framework == "Next.js"
        assert connection.package_manager == "npm"
        # node_modules/foo/index.js and the node_modules tree entry are
        # both excluded; 4 files (package.json, package-lock.json,
        # README.md, src/index.ts) and 1 folder (src) remain.
        assert connection.total_files == 4
        assert connection.total_folders == 1
        assert connection.repo_metadata["dependencies"] == ["next", "react"]

    async def test_rejects_non_github_url(self, db_session):
        _, project = await _make_user_and_project(db_session, email="badurl@example.com")
        async with _make_client(_make_handler()) as client:
            with pytest.raises(InvalidRepositoryUrlError):
                await service.sync_repository(
                    db_session, client, project_id=project.id, repo_url="https://gitlab.com/owner/repo"
                )

    async def test_raises_when_repo_missing_or_private(self, db_session):
        _, project = await _make_user_and_project(db_session, email="missing@example.com")
        async with _make_client(_make_handler(repo_info={})) as client:
            with pytest.raises(RepositoryNotFoundError):
                await service.sync_repository(
                    db_session, client, project_id=project.id, repo_url="https://github.com/octo/ghost"
                )

    async def test_resync_replaces_existing_connection_in_place(self, db_session):
        _, project = await _make_user_and_project(db_session, email="resync@example.com")
        async with _make_client(_make_handler()) as client:
            first = await service.sync_repository(
                db_session, client, project_id=project.id, repo_url="https://github.com/octo/demo-app"
            )
        async with _make_client(_make_handler()) as client:
            second = await service.sync_repository(
                db_session, client, project_id=project.id, repo_url="https://github.com/octo/demo-app"
            )

        assert first.id == second.id


class TestGetConnection:
    async def test_raises_when_no_connection_yet(self, db_session):
        _, project = await _make_user_and_project(db_session, email="noconn@example.com")
        with pytest.raises(RepositoryConnectionNotFoundError):
            await service.get_connection(db_session, project.id)
