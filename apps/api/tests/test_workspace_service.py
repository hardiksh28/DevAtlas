"""Integration tests for app.modules.workspace.service, calling service
functions directly against db_session (no HTTP layer) — same pattern as
test_mentoring_service.py / test_curriculum_service.py."""

import pytest

from app.modules.auth import service as auth_service
from app.modules.projects import service as projects_service
from app.modules.workspace import service as workspace_service
from app.modules.workspace.exceptions import (
    ContentConflictError,
    FileLimitExceededError,
    FileTooLargeError,
    PathAlreadyExistsError,
    WorkspaceFileNotFoundError,
)


async def _make_user_and_project(db, email: str):
    user = await auth_service.register_user(db, email, "hunter22222", "Owner")
    project = await projects_service.create_project(db, user.id, "Workspace Project", None)
    return user, project


class TestCreateFile:
    async def test_creates_file_with_computed_hash_and_size(self, db_session):
        _, project = await _make_user_and_project(db_session, "ws1@example.com")

        file = await workspace_service.create_file(db_session, project.id, "src/index.js", "console.log(1);")

        assert file.path == "src/index.js"
        assert file.content == "console.log(1);"
        assert file.size_bytes == len(b"console.log(1);")
        assert file.content_hash == workspace_service._hash_content("console.log(1);")

    async def test_rejects_duplicate_path(self, db_session):
        _, project = await _make_user_and_project(db_session, "ws2@example.com")
        await workspace_service.create_file(db_session, project.id, "a.txt", "one")

        with pytest.raises(PathAlreadyExistsError):
            await workspace_service.create_file(db_session, project.id, "a.txt", "two")

    async def test_rejects_content_over_the_byte_ceiling(self, db_session, monkeypatch):
        _, project = await _make_user_and_project(db_session, "ws3@example.com")
        monkeypatch.setattr(workspace_service.settings, "workspace_file_max_bytes", 4)

        with pytest.raises(FileTooLargeError):
            await workspace_service.create_file(db_session, project.id, "big.txt", "way too long")

    async def test_rejects_creation_past_the_file_count_ceiling(self, db_session, monkeypatch):
        _, project = await _make_user_and_project(db_session, "ws4@example.com")
        monkeypatch.setattr(workspace_service.settings, "max_workspace_files_per_project", 1)
        await workspace_service.create_file(db_session, project.id, "one.txt", "")

        with pytest.raises(FileLimitExceededError):
            await workspace_service.create_file(db_session, project.id, "two.txt", "")


class TestGetFile:
    async def test_returns_file_scoped_to_project(self, db_session):
        _, project = await _make_user_and_project(db_session, "ws5@example.com")
        created = await workspace_service.create_file(db_session, project.id, "a.txt", "hi")

        fetched = await workspace_service.get_file(db_session, project.id, created.id)

        assert fetched.id == created.id

    async def test_raises_when_file_belongs_to_a_different_project(self, db_session):
        _, project_a = await _make_user_and_project(db_session, "ws6a@example.com")
        _, project_b = await _make_user_and_project(db_session, "ws6b@example.com")
        created = await workspace_service.create_file(db_session, project_a.id, "a.txt", "hi")

        with pytest.raises(WorkspaceFileNotFoundError):
            await workspace_service.get_file(db_session, project_b.id, created.id)


class TestUpdateFileContent:
    async def test_updates_content_and_recomputes_hash(self, db_session):
        _, project = await _make_user_and_project(db_session, "ws7@example.com")
        file = await workspace_service.create_file(db_session, project.id, "a.txt", "one")

        updated = await workspace_service.update_file_content(
            db_session, file, "two", expected_content_hash=file.content_hash
        )

        assert updated.content == "two"
        assert updated.content_hash == workspace_service._hash_content("two")

    async def test_raises_conflict_on_stale_hash(self, db_session):
        _, project = await _make_user_and_project(db_session, "ws8@example.com")
        file = await workspace_service.create_file(db_session, project.id, "a.txt", "one")

        with pytest.raises(ContentConflictError):
            await workspace_service.update_file_content(
                db_session, file, "two", expected_content_hash="stale-hash"
            )

    async def test_allows_first_save_without_a_hash(self, db_session):
        _, project = await _make_user_and_project(db_session, "ws9@example.com")
        file = await workspace_service.create_file(db_session, project.id, "a.txt", "")

        updated = await workspace_service.update_file_content(
            db_session, file, "first content", expected_content_hash=None
        )

        assert updated.content == "first content"


class TestRenameFile:
    async def test_renames_to_a_free_path(self, db_session):
        _, project = await _make_user_and_project(db_session, "ws10@example.com")
        file = await workspace_service.create_file(db_session, project.id, "old.txt", "")

        renamed = await workspace_service.rename_file(db_session, project.id, file, "new.txt")

        assert renamed.path == "new.txt"

    async def test_rejects_rename_onto_an_existing_path(self, db_session):
        _, project = await _make_user_and_project(db_session, "ws11@example.com")
        await workspace_service.create_file(db_session, project.id, "taken.txt", "")
        file = await workspace_service.create_file(db_session, project.id, "movable.txt", "")

        with pytest.raises(PathAlreadyExistsError):
            await workspace_service.rename_file(db_session, project.id, file, "taken.txt")


class TestDeleteFile:
    async def test_deletes_file_and_prunes_it_from_open_tabs(self, db_session):
        _, project = await _make_user_and_project(db_session, "ws12@example.com")
        file = await workspace_service.create_file(db_session, project.id, "a.txt", "")
        layout = await workspace_service.get_or_create_layout(db_session, project.id)
        await workspace_service.update_layout(
            db_session, layout, {"open_tabs": [file.id], "active_tab_id": file.id}
        )

        await workspace_service.delete_file(db_session, project.id, file)

        with pytest.raises(WorkspaceFileNotFoundError):
            await workspace_service.get_file(db_session, project.id, file.id)
        refreshed_layout = await workspace_service.get_or_create_layout(db_session, project.id)
        assert refreshed_layout.open_tabs == []
        assert refreshed_layout.active_tab_id is None


class TestLayout:
    async def test_get_or_create_is_idempotent(self, db_session):
        _, project = await _make_user_and_project(db_session, "ws13@example.com")

        first = await workspace_service.get_or_create_layout(db_session, project.id)
        second = await workspace_service.get_or_create_layout(db_session, project.id)

        assert first.project_id == second.project_id == project.id
        assert first.right_rail_tab == "lesson"
        assert first.bottom_panel_tab == "terminal"

    async def test_update_layout_applies_partial_changes(self, db_session):
        _, project = await _make_user_and_project(db_session, "ws14@example.com")
        layout = await workspace_service.get_or_create_layout(db_session, project.id)

        updated = await workspace_service.update_layout(
            db_session, layout, {"bottom_panel_visible": True, "right_rail_tab": "chat"}
        )

        assert updated.bottom_panel_visible is True
        assert updated.right_rail_tab == "chat"
