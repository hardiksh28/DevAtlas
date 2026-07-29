"""Integration tests for app.modules.projects.router.

Drives the real FastAPI app end-to-end (ASGI transport, no network) —
see tests/conftest.py for the client fixture and its DB/Redis overrides.
Each httpx AsyncClient instance persists cookies across requests, so
registering once at the top of a test authenticates every subsequent
call made with that same `client`.
"""

import uuid


async def _register(client, email="user@example.com"):
    return await client.post(
        "/v1/auth/register",
        json={"email": email, "password": "hunter22222", "display_name": "User One"},
    )


async def _create_project(client, name="My Project", description="A test project"):
    return await client.post("/v1/projects", json={"name": name, "description": description})


class TestCreateProject:
    async def test_requires_auth(self, client):
        resp = await _create_project(client)
        assert resp.status_code == 401

    async def test_creates_project(self, client):
        await _register(client)
        resp = await _create_project(client)
        assert resp.status_code == 201
        body = resp.json()
        assert body["name"] == "My Project"
        assert body["status"] == "active"
        assert body["deleted_at"] is None
        # icon/color come from the joined ProjectSettings row (see
        # models.py's lazy="joined") — asserted here so a regression to
        # N+1 settings fetches or a broken join shows up as a missing
        # field, not a silent extra query.
        assert body["icon"] == "📁"
        assert body["color"] == "slate"

    async def test_rejects_blank_name(self, client):
        await _register(client)
        resp = await client.post("/v1/projects", json={"name": "   "})
        assert resp.status_code == 422


class TestListProjects:
    async def test_lists_only_own_active_projects_by_default(self, client):
        await _register(client, email="lister@example.com")
        await _create_project(client, name="Active One")
        archived = await _create_project(client, name="Archived One")
        await client.post(f"/v1/projects/{archived.json()['id']}/archive")

        resp = await client.get("/v1/projects")
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 1
        assert body["items"][0]["name"] == "Active One"
        assert body["items"][0]["icon"] == "📁"

    async def test_status_filter(self, client):
        await _register(client, email="filter@example.com")
        created = await _create_project(client, name="ToArchive")
        await client.post(f"/v1/projects/{created.json()['id']}/archive")

        resp = await client.get("/v1/projects", params={"status": "archived"})
        assert resp.status_code == 200
        assert resp.json()["total"] == 1


class TestGetProject:
    async def test_get_unknown_project_is_404(self, client):
        await _register(client, email="get404@example.com")
        resp = await client.get(f"/v1/projects/{uuid.uuid4()}")
        assert resp.status_code == 404
        assert resp.json()["error_code"] == "project_not_found"

    async def test_cannot_access_another_users_project(self, client):
        await _register(client, email="owner@example.com")
        created = await _create_project(client)
        project_id = created.json()["id"]

        await client.post("/v1/auth/logout")
        await _register(client, email="intruder@example.com")

        resp = await client.get(f"/v1/projects/{project_id}")
        assert resp.status_code == 404

    async def test_get_records_recent_view(self, client):
        await _register(client, email="viewer@example.com")
        created = await _create_project(client)
        project_id = created.json()["id"]

        await client.get(f"/v1/projects/{project_id}")

        recent = await client.get("/v1/projects/recent")
        assert recent.status_code == 200
        assert [p["project"]["id"] for p in recent.json()] == [project_id]


class TestUpdateProject:
    async def test_partial_update(self, client):
        await _register(client, email="updater@example.com")
        created = await _create_project(client)
        project_id = created.json()["id"]

        resp = await client.patch(f"/v1/projects/{project_id}", json={"name": "Renamed"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["name"] == "Renamed"
        assert body["description"] == "A test project"

    async def test_can_explicitly_clear_description(self, client):
        # Sending "" (not omitting the field) must clear it — relies on
        # exclude_unset still treating the field as "provided" even
        # though the blank-to-None validator rewrites its value; the
        # field being merely omitted from the JSON body must NOT clear
        # it (covered by test_partial_update above).
        await _register(client, email="clear@example.com")
        created = await _create_project(client)
        project_id = created.json()["id"]

        resp = await client.patch(f"/v1/projects/{project_id}", json={"description": ""})
        assert resp.status_code == 200
        assert resp.json()["description"] is None


class TestArchiveDeleteRestore:
    async def test_archive_then_restore(self, client):
        await _register(client, email="lifecycle@example.com")
        created = await _create_project(client)
        project_id = created.json()["id"]

        archived = await client.post(f"/v1/projects/{project_id}/archive")
        assert archived.status_code == 200
        assert archived.json()["status"] == "archived"

        restored = await client.post(f"/v1/projects/{project_id}/restore")
        assert restored.status_code == 200
        assert restored.json()["status"] == "active"

    async def test_delete_then_invisible_then_restorable(self, client):
        await _register(client, email="deleter@example.com")
        created = await _create_project(client)
        project_id = created.json()["id"]

        deleted = await client.delete(f"/v1/projects/{project_id}")
        assert deleted.status_code == 204

        gone = await client.get(f"/v1/projects/{project_id}")
        assert gone.status_code == 404

        restored = await client.post(f"/v1/projects/{project_id}/restore")
        assert restored.status_code == 200
        assert restored.json()["status"] == "active"

    async def test_restore_already_active_project_is_conflict(self, client):
        await _register(client, email="conflict@example.com")
        created = await _create_project(client)
        project_id = created.json()["id"]

        resp = await client.post(f"/v1/projects/{project_id}/restore")
        assert resp.status_code == 409
        assert resp.json()["error_code"] == "invalid_project_state"


class TestProjectSettings:
    async def test_get_defaults(self, client):
        await _register(client, email="settingsget@example.com")
        created = await _create_project(client)
        project_id = created.json()["id"]

        resp = await client.get(f"/v1/projects/{project_id}/settings")
        assert resp.status_code == 200
        body = resp.json()
        assert body["icon"] == "📁"
        assert body["color"] == "slate"

    async def test_update_color(self, client):
        await _register(client, email="settingsupdate@example.com")
        created = await _create_project(client)
        project_id = created.json()["id"]

        resp = await client.patch(f"/v1/projects/{project_id}/settings", json={"color": "blue"})
        assert resp.status_code == 200
        assert resp.json()["color"] == "blue"

    async def test_rejects_invalid_color(self, client):
        await _register(client, email="settingsbad@example.com")
        created = await _create_project(client)
        project_id = created.json()["id"]

        resp = await client.patch(
            f"/v1/projects/{project_id}/settings", json={"color": "not-a-real-color"}
        )
        assert resp.status_code == 422

    async def test_rejects_oversized_settings_blob(self, client):
        await _register(client, email="settingsoversized@example.com")
        created = await _create_project(client)
        project_id = created.json()["id"]

        resp = await client.patch(
            f"/v1/projects/{project_id}/settings",
            json={"settings": {"blob": "x" * 20_000}},
        )
        assert resp.status_code == 422


class TestProjectLimit:
    async def test_create_rejects_past_active_project_limit(self, client, monkeypatch):
        from app.core.config import get_settings

        monkeypatch.setattr(get_settings(), "max_active_projects_per_owner", 1)
        await _register(client, email="limitrouter@example.com")

        first = await _create_project(client, name="First")
        assert first.status_code == 201

        second = await _create_project(client, name="Second")
        assert second.status_code == 422
        assert second.json()["error_code"] == "project_limit_exceeded"


class TestDashboard:
    async def test_aggregates_counts_and_recent(self, client):
        await _register(client, email="dash@example.com")
        active = await _create_project(client, name="Active")
        archived = await _create_project(client, name="Archived")
        await client.post(f"/v1/projects/{archived.json()['id']}/archive")
        await client.get(f"/v1/projects/{active.json()['id']}")  # records a view

        resp = await client.get("/v1/dashboard")
        assert resp.status_code == 200
        body = resp.json()
        assert body["active_count"] == 1
        assert body["archived_count"] == 1
        assert len(body["recent_projects"]) == 1
        assert body["recent_projects"][0]["project"]["name"] == "Active"

    async def test_requires_auth(self, client):
        resp = await client.get("/v1/dashboard")
        assert resp.status_code == 401
