"""Thin HTTP-layer tests for the Visual Learning Engine's routes. Mirrors
test_code_review_router.py's conventions: the real LLM gateway is
exercised here (not faked), since Ollama isn't reachable in this test
environment — these tests only cover paths that don't require a
successful generation. Full generate-and-persist coverage is in
test_visuals_service.py against a fake gateway."""

import uuid


async def _register(client, email="user@example.com"):
    return await client.post(
        "/v1/auth/register",
        json={"email": email, "password": "hunter22222", "display_name": "User One"},
    )


async def _create_project(client, name="Diagram Project"):
    resp = await client.post("/v1/projects", json={"name": name})
    return resp.json()["id"]


class TestListDiagramsRoute:
    async def test_list_diagrams_before_any_generated_is_empty(self, client):
        await _register(client, email="list1@example.com")
        project_id = await _create_project(client)

        resp = await client.get(f"/v1/projects/{project_id}/diagrams")

        assert resp.status_code == 200
        body = resp.json()
        assert body["items"] == []
        assert body["total"] == 0


class TestGetDiagramRoute:
    async def test_missing_diagram_is_404(self, client):
        await _register(client, email="get1@example.com")
        project_id = await _create_project(client)

        resp = await client.get(f"/v1/projects/{project_id}/diagrams/{uuid.uuid4()}")

        assert resp.status_code == 404
        assert resp.json()["error_code"] == "diagram_not_found"


class TestGenerateDiagramValidation:
    async def test_requires_a_subject_milestone_or_code(self, client):
        await _register(client, email="submit1@example.com")
        project_id = await _create_project(client)

        resp = await client.post(
            f"/v1/projects/{project_id}/diagrams", json={"diagram_type": "sequence"}
        )

        assert resp.status_code == 422

    async def test_invalid_diagram_type_is_rejected(self, client):
        await _register(client, email="submit2@example.com")
        project_id = await _create_project(client)

        resp = await client.post(
            f"/v1/projects/{project_id}/diagrams",
            json={"diagram_type": "not_a_real_type", "subject": "Explain this"},
        )

        assert resp.status_code == 422


class TestProjectOwnershipEnforcement:
    async def test_diagram_routes_for_another_users_project_are_404(self, client):
        await _register(client, email="owner@example.com")
        project_id = await _create_project(client)
        await client.post("/v1/auth/logout")
        await _register(client, email="intruder@example.com")

        resp = await client.get(f"/v1/projects/{project_id}/diagrams")

        assert resp.status_code == 404
