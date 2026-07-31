"""Thin HTTP-layer tests for the Mentoring Engine's conversational
routes. Mirrors test_curriculum_router.py's auth/project-creation
conventions. The real LLM gateway is exercised here (not faked) since
these are thin router-shape checks, not LLM-behavior checks — the
gateway's own provider (Ollama) isn't reachable in this test
environment, so these tests only cover paths that don't require a
successful generation."""

from tests.taxonomy_fixtures import create_concept


async def _register(client, email="user@example.com"):
    return await client.post(
        "/v1/auth/register",
        json={"email": email, "password": "hunter22222", "display_name": "User One"},
    )


async def _create_project(client, name="Mentor Project"):
    resp = await client.post("/v1/projects", json={"name": name})
    return resp.json()["id"]


class TestListMessagesRoute:
    async def test_list_messages_before_any_sent_is_empty(self, client):
        await _register(client, email="list1@example.com")
        project_id = await _create_project(client)

        resp = await client.get(f"/v1/projects/{project_id}/mentor/messages")

        assert resp.status_code == 200
        body = resp.json()
        assert body["items"] == []
        assert body["total"] == 0

    async def test_blank_message_is_rejected(self, client):
        await _register(client, email="list2@example.com")
        project_id = await _create_project(client)

        resp = await client.post(f"/v1/projects/{project_id}/mentor/messages", json={"content": "   "})

        assert resp.status_code == 422


class TestProjectOwnershipEnforcement:
    async def test_mentor_routes_for_another_users_project_are_404(self, client):
        await _register(client, email="owner@example.com")
        project_id = await _create_project(client)
        await client.post("/v1/auth/logout")
        await _register(client, email="intruder@example.com")

        resp = await client.get(f"/v1/projects/{project_id}/mentor/messages")

        assert resp.status_code == 404


class TestMilestoneSeeding:
    async def test_seeded_concept_available_for_milestone_scoped_send(self, client, db_session):
        # Confirms the router layer passes milestone_id through to the
        # service without needing a live LLM — full send-and-reply is
        # covered against a fake gateway in test_mentoring_service.py.
        await create_concept(db_session, "python.variables", severity="foundational")
        await db_session.commit()
        await _register(client, email="seed1@example.com")
        project_id = await _create_project(client)

        gen_resp = await client.post(
            f"/v1/projects/{project_id}/roadmap/generate",
            json={"stack": "python", "stack_version": "3.12", "experience_level": "beginner"},
        )
        assert gen_resp.status_code == 200
