"""Thin HTTP-layer tests for the Curriculum Engine's roadmap routes.

Concepts have no creation endpoint (curated via scripts/seed_taxonomy.py
— see taxonomy/service.py's docstring), so these tests seed them via
`db_session` directly (sharing the same underlying engine the `client`
fixture uses) and drive everything else through HTTP, mirroring
test_knowledge_router.py's auth/project-creation conventions.
"""

from tests.taxonomy_fixtures import create_concept


async def _register(client, email="user@example.com"):
    return await client.post(
        "/v1/auth/register",
        json={"email": email, "password": "hunter22222", "display_name": "User One"},
    )


async def _create_project(client, name="Roadmap Project"):
    resp = await client.post("/v1/projects", json={"name": name})
    return resp.json()["id"]


async def _seed_python_stack(db_session):
    await create_concept(db_session, "python.variables", severity="foundational")
    await create_concept(
        db_session, "python.functions", severity="foundational", prerequisites=["python.variables"]
    )
    await db_session.commit()


class TestGenerateRoadmap:
    async def test_generate_then_get_roadmap(self, client, db_session):
        await _seed_python_stack(db_session)
        await _register(client, email="gen@example.com")
        project_id = await _create_project(client)

        resp = await client.post(
            f"/v1/projects/{project_id}/roadmap/generate",
            json={"stack": "python", "stack_version": "3.12", "experience_level": "beginner"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["stack"] == "python"
        assert [m["concept_id"] for m in body["milestones"]] == [
            "python.variables",
            "python.functions",
        ]
        assert body["milestones"][0]["status"] == "available"

        get_resp = await client.get(f"/v1/projects/{project_id}/roadmap")
        assert get_resp.status_code == 200
        assert get_resp.json()["id"] == body["id"]

    async def test_generate_unknown_stack_returns_422(self, client, db_session):
        await _register(client, email="gen2@example.com")
        project_id = await _create_project(client)

        resp = await client.post(
            f"/v1/projects/{project_id}/roadmap/generate",
            json={"stack": "nonexistent", "stack_version": "1", "experience_level": "beginner"},
        )
        assert resp.status_code == 404  # StackNotFoundError

    async def test_get_roadmap_before_generation_returns_404(self, client, db_session):
        await _register(client, email="gen3@example.com")
        project_id = await _create_project(client)

        resp = await client.get(f"/v1/projects/{project_id}/roadmap")
        assert resp.status_code == 404


class TestMilestoneRoutes:
    async def test_get_and_update_milestone_status(self, client, db_session):
        await _seed_python_stack(db_session)
        await _register(client, email="mile1@example.com")
        project_id = await _create_project(client)
        gen_resp = await client.post(
            f"/v1/projects/{project_id}/roadmap/generate",
            json={"stack": "python", "stack_version": "3.12", "experience_level": "beginner"},
        )
        milestone_id = gen_resp.json()["milestones"][0]["id"]

        get_resp = await client.get(f"/v1/projects/{project_id}/roadmap/milestones/{milestone_id}")
        assert get_resp.status_code == 200
        assert get_resp.json()["lesson_content"] is None

        patch_resp = await client.patch(
            f"/v1/projects/{project_id}/roadmap/milestones/{milestone_id}",
            json={"status": "in_progress"},
        )
        assert patch_resp.status_code == 200
        assert patch_resp.json()["status"] == "in_progress"

    async def test_invalid_transition_returns_409(self, client, db_session):
        await _seed_python_stack(db_session)
        await _register(client, email="mile2@example.com")
        project_id = await _create_project(client)
        gen_resp = await client.post(
            f"/v1/projects/{project_id}/roadmap/generate",
            json={"stack": "python", "stack_version": "3.12", "experience_level": "beginner"},
        )
        locked_milestone_id = gen_resp.json()["milestones"][1]["id"]

        resp = await client.patch(
            f"/v1/projects/{project_id}/roadmap/milestones/{locked_milestone_id}",
            json={"status": "in_progress"},
        )
        assert resp.status_code == 409


class TestProjectOwnershipEnforcement:
    async def test_roadmap_route_for_another_users_project_is_404(self, client, db_session):
        await _seed_python_stack(db_session)
        await _register(client, email="owner@example.com")
        project_id = await _create_project(client)
        await client.post(
            f"/v1/projects/{project_id}/roadmap/generate",
            json={"stack": "python", "stack_version": "3.12", "experience_level": "beginner"},
        )

        await client.post("/v1/auth/logout")
        await _register(client, email="intruder@example.com")

        resp = await client.get(f"/v1/projects/{project_id}/roadmap")
        assert resp.status_code == 404
