"""Thin HTTP-layer tests for the Interactive Learning Workspace's
file-tree and layout-persistence routes. Mirrors test_mentoring_router.py's
auth/project-creation conventions."""


async def _register(client, email="user@example.com"):
    return await client.post(
        "/v1/auth/register",
        json={"email": email, "password": "hunter22222", "display_name": "User One"},
    )


async def _create_project(client, name="Workspace Project"):
    resp = await client.post("/v1/projects", json={"name": name})
    return resp.json()["id"]


class TestFileRoutes:
    async def test_create_then_list_tree(self, client):
        await _register(client, email="wsr1@example.com")
        project_id = await _create_project(client)

        create_resp = await client.post(
            f"/v1/projects/{project_id}/workspace/files",
            json={"path": "src/index.js", "content": "console.log(1);"},
        )
        assert create_resp.status_code == 201
        body = create_resp.json()
        assert body["path"] == "src/index.js"
        assert body["content_hash"] is not None

        tree_resp = await client.get(f"/v1/projects/{project_id}/workspace/tree")
        assert tree_resp.status_code == 200
        assert [f["path"] for f in tree_resp.json()["items"]] == ["src/index.js"]

    async def test_duplicate_path_is_conflict(self, client):
        await _register(client, email="wsr2@example.com")
        project_id = await _create_project(client)
        await client.post(f"/v1/projects/{project_id}/workspace/files", json={"path": "a.txt"})

        resp = await client.post(f"/v1/projects/{project_id}/workspace/files", json={"path": "a.txt"})

        assert resp.status_code == 409

    async def test_path_traversal_is_rejected(self, client):
        await _register(client, email="wsr3@example.com")
        project_id = await _create_project(client)

        resp = await client.post(
            f"/v1/projects/{project_id}/workspace/files", json={"path": "../etc/passwd"}
        )

        assert resp.status_code == 422

    async def test_update_content_conflict_on_stale_hash(self, client):
        await _register(client, email="wsr4@example.com")
        project_id = await _create_project(client)
        created = (
            await client.post(f"/v1/projects/{project_id}/workspace/files", json={"path": "a.txt"})
        ).json()

        resp = await client.patch(
            f"/v1/projects/{project_id}/workspace/files/{created['id']}",
            json={"content": "new", "expected_content_hash": "stale"},
        )

        assert resp.status_code == 409

    async def test_update_content_succeeds_with_matching_hash(self, client):
        await _register(client, email="wsr5@example.com")
        project_id = await _create_project(client)
        created = (
            await client.post(f"/v1/projects/{project_id}/workspace/files", json={"path": "a.txt"})
        ).json()

        resp = await client.patch(
            f"/v1/projects/{project_id}/workspace/files/{created['id']}",
            json={"content": "new content", "expected_content_hash": created["content_hash"]},
        )

        assert resp.status_code == 200
        assert resp.json()["content"] == "new content"

    async def test_rename_and_delete(self, client):
        await _register(client, email="wsr6@example.com")
        project_id = await _create_project(client)
        created = (
            await client.post(f"/v1/projects/{project_id}/workspace/files", json={"path": "old.txt"})
        ).json()

        rename_resp = await client.patch(
            f"/v1/projects/{project_id}/workspace/files/{created['id']}/path",
            json={"new_path": "new.txt"},
        )
        assert rename_resp.status_code == 200
        assert rename_resp.json()["path"] == "new.txt"

        delete_resp = await client.delete(f"/v1/projects/{project_id}/workspace/files/{created['id']}")
        assert delete_resp.status_code == 204

        get_resp = await client.get(f"/v1/projects/{project_id}/workspace/files/{created['id']}")
        assert get_resp.status_code == 404


class TestLayoutRoutes:
    async def test_get_layout_creates_default_lazily(self, client):
        await _register(client, email="wsr7@example.com")
        project_id = await _create_project(client)

        resp = await client.get(f"/v1/projects/{project_id}/workspace/layout")

        assert resp.status_code == 200
        body = resp.json()
        assert body["right_rail_tab"] == "lesson"
        assert body["bottom_panel_tab"] == "terminal"
        assert body["open_tabs"] == []

    async def test_update_layout_persists_partial_changes(self, client):
        await _register(client, email="wsr8@example.com")
        project_id = await _create_project(client)
        created = (
            await client.post(f"/v1/projects/{project_id}/workspace/files", json={"path": "a.txt"})
        ).json()

        resp = await client.patch(
            f"/v1/projects/{project_id}/workspace/layout",
            json={
                "open_tabs": [created["id"]],
                "active_tab_id": created["id"],
                "right_rail_tab": "chat",
                "bottom_panel_visible": True,
            },
        )

        assert resp.status_code == 200
        body = resp.json()
        assert body["open_tabs"] == [created["id"]]
        assert body["active_tab_id"] == created["id"]
        assert body["right_rail_tab"] == "chat"
        assert body["bottom_panel_visible"] is True


class TestProjectOwnershipEnforcement:
    async def test_workspace_routes_for_another_users_project_are_404(self, client):
        await _register(client, email="wsr-owner@example.com")
        project_id = await _create_project(client)
        await client.post("/v1/auth/logout")
        await _register(client, email="wsr-intruder@example.com")

        resp = await client.get(f"/v1/projects/{project_id}/workspace/tree")

        assert resp.status_code == 404
