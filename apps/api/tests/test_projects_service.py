"""Integration tests for app.modules.projects.service.

Exercises the service layer against a real AsyncSession/schema — see
tests/conftest.py for how the backing database is provided without
requiring Docker/Postgres locally.
"""

import pytest

from app.core.config import get_settings
from app.modules.auth import service as auth_service
from app.modules.projects import service
from app.modules.projects.exceptions import (
    InvalidProjectStateError,
    ProjectLimitExceededError,
    ProjectNotFoundError,
)

settings = get_settings()


async def _make_user(db, email="owner@example.com"):
    return await auth_service.register_user(db, email, "hunter22222", "Owner")


class TestCreateProject:
    async def test_creates_project_and_settings_row(self, db_session):
        user = await _make_user(db_session)
        project = await service.create_project(db_session, user.id, "My Project", "A description")

        assert project.id is not None
        assert project.status == "active"
        assert project.owner_id == user.id

        project_settings = await service.get_project_settings(db_session, project.id)
        assert project_settings.icon == "📁"
        assert project_settings.color == "slate"

    async def test_rejects_creation_past_the_active_project_limit(self, db_session, monkeypatch):
        monkeypatch.setattr(settings, "max_active_projects_per_owner", 1)
        user = await _make_user(db_session, email="limit@example.com")
        await service.create_project(db_session, user.id, "First", None)

        with pytest.raises(ProjectLimitExceededError):
            await service.create_project(db_session, user.id, "Second", None)

    async def test_archived_projects_dont_count_against_the_limit(self, db_session, monkeypatch):
        monkeypatch.setattr(settings, "max_active_projects_per_owner", 1)
        user = await _make_user(db_session, email="limit2@example.com")
        first = await service.create_project(db_session, user.id, "First", None)
        await service.archive_project(db_session, first)

        # Doesn't raise — archiving freed up the one active slot.
        await service.create_project(db_session, user.id, "Second", None)


class TestGetProject:
    async def test_raises_not_found_for_unknown_id(self, db_session):
        user = await _make_user(db_session)
        import uuid

        with pytest.raises(ProjectNotFoundError):
            await service.get_project(db_session, uuid.uuid4(), user.id)

    async def test_raises_not_found_for_non_owner(self, db_session):
        owner = await _make_user(db_session, email="owner2@example.com")
        other = await _make_user(db_session, email="other@example.com")
        project = await service.create_project(db_session, owner.id, "Private", None)

        with pytest.raises(ProjectNotFoundError):
            await service.get_project(db_session, project.id, other.id)

    async def test_raises_not_found_for_deleted_project(self, db_session):
        user = await _make_user(db_session, email="del@example.com")
        project = await service.create_project(db_session, user.id, "Gone", None)
        await service.delete_project(db_session, project)

        with pytest.raises(ProjectNotFoundError):
            await service.get_project(db_session, project.id, user.id)


class TestUpdateProject:
    async def test_partial_update_only_touches_included_fields(self, db_session):
        user = await _make_user(db_session, email="upd@example.com")
        project = await service.create_project(db_session, user.id, "Original", "Desc")

        updated = await service.update_project(db_session, project, {"name": "Renamed"})
        assert updated.name == "Renamed"
        assert updated.description == "Desc"

    async def test_can_clear_description_explicitly(self, db_session):
        user = await _make_user(db_session, email="clr@example.com")
        project = await service.create_project(db_session, user.id, "Original", "Desc")

        updated = await service.update_project(db_session, project, {"description": None})
        assert updated.description is None


class TestArchiveDeleteRestore:
    async def test_archive_is_idempotent(self, db_session):
        user = await _make_user(db_session, email="arch@example.com")
        project = await service.create_project(db_session, user.id, "Archivable", None)

        first = await service.archive_project(db_session, project)
        archived_at = first.archived_at
        second = await service.archive_project(db_session, project)
        assert second.archived_at == archived_at
        assert second.status == "archived"

    async def test_delete_then_restore_returns_to_active(self, db_session):
        user = await _make_user(db_session, email="restore@example.com")
        project = await service.create_project(db_session, user.id, "Restorable", None)
        await service.delete_project(db_session, project)

        restored = await service.restore_project(db_session, project.id, user.id)
        assert restored.status == "active"
        assert restored.deleted_at is None
        assert restored.archived_at is None

    async def test_restore_rejects_already_active_project(self, db_session):
        user = await _make_user(db_session, email="noop-restore@example.com")
        project = await service.create_project(db_session, user.id, "AlreadyActive", None)

        with pytest.raises(InvalidProjectStateError):
            await service.restore_project(db_session, project.id, user.id)

    async def test_restore_rejects_past_the_active_project_limit(self, db_session, monkeypatch):
        monkeypatch.setattr(settings, "max_active_projects_per_owner", 1)
        user = await _make_user(db_session, email="limit3@example.com")
        first = await service.create_project(db_session, user.id, "First", None)
        await service.archive_project(db_session, first)
        await service.create_project(db_session, user.id, "Second", None)  # back at the cap

        with pytest.raises(ProjectLimitExceededError):
            await service.restore_project(db_session, first.id, user.id)

    async def test_restore_raises_not_found_for_non_owner(self, db_session):
        owner = await _make_user(db_session, email="rowner@example.com")
        other = await _make_user(db_session, email="rother@example.com")
        project = await service.create_project(db_session, owner.id, "NotYours", None)
        await service.delete_project(db_session, project)

        with pytest.raises(ProjectNotFoundError):
            await service.restore_project(db_session, project.id, other.id)


class TestListProjects:
    async def test_filters_by_status_and_orders_by_recency(self, db_session):
        user = await _make_user(db_session, email="list@example.com")
        first = await service.create_project(db_session, user.id, "First", None)
        second = await service.create_project(db_session, user.id, "Second", None)
        await service.archive_project(db_session, first)

        active_items, active_total = await service.list_projects(db_session, user.id, "active", 20, 0)
        assert active_total == 1
        assert [p.id for p in active_items] == [second.id]

        archived_items, archived_total = await service.list_projects(
            db_session, user.id, "archived", 20, 0
        )
        assert archived_total == 1
        assert [p.id for p in archived_items] == [first.id]

    async def test_pagination(self, db_session):
        user = await _make_user(db_session, email="page@example.com")
        for i in range(5):
            await service.create_project(db_session, user.id, f"Project {i}", None)

        page1, total = await service.list_projects(db_session, user.id, "active", 2, 0)
        page2, _ = await service.list_projects(db_session, user.id, "active", 2, 2)
        assert total == 5
        assert len(page1) == 2
        assert len(page2) == 2
        assert {p.id for p in page1}.isdisjoint({p.id for p in page2})


class TestProjectSettings:
    async def test_update_settings_partial(self, db_session):
        user = await _make_user(db_session, email="settings@example.com")
        project = await service.create_project(db_session, user.id, "Themed", None)
        settings = await service.get_project_settings(db_session, project.id)

        updated = await service.update_project_settings(db_session, settings, {"color": "blue"})
        assert updated.color == "blue"
        assert updated.icon == "📁"  # untouched


class TestRecentProjects:
    async def test_record_view_upserts_single_row_per_pair(self, db_session):
        user = await _make_user(db_session, email="recent@example.com")
        project = await service.create_project(db_session, user.id, "Viewed", None)

        await service.record_project_view(db_session, user.id, project.id)
        first = await service.list_recent_projects(db_session, user.id, 10)
        await service.record_project_view(db_session, user.id, project.id)
        second = await service.list_recent_projects(db_session, user.id, 10)

        assert len(first) == 1
        assert len(second) == 1  # still one row — updated, not duplicated

    async def test_orders_most_recently_viewed_first(self, db_session):
        user = await _make_user(db_session, email="order@example.com")
        older = await service.create_project(db_session, user.id, "Older view", None)
        newer = await service.create_project(db_session, user.id, "Newer view", None)

        await service.record_project_view(db_session, user.id, older.id)
        await service.record_project_view(db_session, user.id, newer.id)

        recents = await service.list_recent_projects(db_session, user.id, 10)
        assert [r.project_id for r in recents] == [newer.id, older.id]

    async def test_excludes_deleted_projects(self, db_session):
        user = await _make_user(db_session, email="exclude@example.com")
        project = await service.create_project(db_session, user.id, "WillDelete", None)
        await service.record_project_view(db_session, user.id, project.id)
        await service.delete_project(db_session, project)

        recents = await service.list_recent_projects(db_session, user.id, 10)
        assert recents == []
