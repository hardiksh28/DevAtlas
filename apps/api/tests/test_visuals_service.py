"""Integration tests for app.modules.visuals.service, calling service
functions directly against db_session (no HTTP layer) — same pattern as
test_code_review_service.py."""

import json
import uuid

import pytest

from app.modules.auth import service as auth_service
from app.modules.curriculum import service as curriculum_service
from app.modules.projects import service as projects_service
from app.modules.visuals import service as visuals_service
from app.modules.visuals.exceptions import DiagramGenerationError, DiagramNotFoundError
from tests.taxonomy_fixtures import create_concept


class FakeLLMGateway:
    def __init__(self, *, diagram_response: str | None = None) -> None:
        self.diagram_response = diagram_response or json.dumps(
            {
                "title": "Login Sequence",
                "mermaid_source": "sequenceDiagram\n    Client->>Server: POST /login\n    Server-->>Client: 200 OK",
            }
        )
        self.generate_calls: list[tuple[str, str]] = []
        self.raise_on_generate: Exception | None = None

    async def embed(self, texts: list[str]) -> list[list[float]]:
        return [[0.1] * 768 for _ in texts]

    async def generate(self, operation: str, prompt: str) -> str:
        self.generate_calls.append((operation, prompt))
        if self.raise_on_generate:
            raise self.raise_on_generate
        return self.diagram_response


async def _make_user_and_project(db, email: str):
    user = await auth_service.register_user(db, email, "hunter22222", "Owner")
    project = await projects_service.create_project(db, user.id, "Diagram Project", None)
    return user, project


class TestGenerateDiagram:
    async def test_creates_diagram_with_title_and_source(self, db_session):
        _, project = await _make_user_and_project(db_session, "diagram1@example.com")
        gateway = FakeLLMGateway()

        diagram = await visuals_service.generate_diagram(
            db_session,
            gateway,
            project_id=project.id,
            diagram_type="sequence",
            subject="How login works",
            milestone_id=None,
            code=None,
        )

        assert diagram.title == "Login Sequence"
        assert diagram.mermaid_source.startswith("sequenceDiagram")
        assert diagram.diagram_type == "sequence"

    async def test_tags_the_generate_call_with_the_diagram_generation_operation(self, db_session):
        _, project = await _make_user_and_project(db_session, "diagram2@example.com")
        gateway = FakeLLMGateway()

        await visuals_service.generate_diagram(
            db_session,
            gateway,
            project_id=project.id,
            diagram_type="sequence",
            subject="How login works",
            milestone_id=None,
            code=None,
        )

        assert gateway.generate_calls[0][0] == "diagram_generation"

    async def test_pulls_concept_context_from_milestone(self, db_session):
        _, project = await _make_user_and_project(db_session, "diagram3@example.com")
        await create_concept(db_session, "python.variables", severity="foundational")
        await db_session.commit()
        roadmap = await curriculum_service.generate_or_regenerate_roadmap(
            db_session,
            project_id=project.id,
            stack="python",
            stack_version="3.12",
            experience_level="beginner",
        )
        milestone = roadmap.milestones[0]
        gateway = FakeLLMGateway()

        diagram = await visuals_service.generate_diagram(
            db_session,
            gateway,
            project_id=project.id,
            diagram_type="sequence",
            subject=None,
            milestone_id=milestone.id,
            code=None,
        )

        assert "python.variables" in diagram.subject
        assert "python.variables" in gateway.generate_calls[0][1]

    async def test_wrong_diagram_header_triggers_retry_then_raises(self, db_session):
        _, project = await _make_user_and_project(db_session, "diagram4@example.com")
        gateway = FakeLLMGateway(
            diagram_response=json.dumps({"title": "x", "mermaid_source": "erDiagram\n    A ||--o{ B : has"})
        )

        with pytest.raises(DiagramGenerationError):
            await visuals_service.generate_diagram(
                db_session,
                gateway,
                project_id=project.id,
                diagram_type="sequence",
                subject="Something",
                milestone_id=None,
                code=None,
            )

        assert len(gateway.generate_calls) == 2

    async def test_gateway_failure_raises_diagram_generation_error(self, db_session):
        _, project = await _make_user_and_project(db_session, "diagram5@example.com")
        gateway = FakeLLMGateway()
        gateway.raise_on_generate = ConnectionError("ollama unreachable")

        with pytest.raises(DiagramGenerationError):
            await visuals_service.generate_diagram(
                db_session,
                gateway,
                project_id=project.id,
                diagram_type="sequence",
                subject="Something",
                milestone_id=None,
                code=None,
            )


class TestGetAndListDiagrams:
    async def test_get_missing_diagram_raises_not_found(self, db_session):
        _, project = await _make_user_and_project(db_session, "diagram6@example.com")

        with pytest.raises(DiagramNotFoundError):
            await visuals_service.get_diagram(db_session, project_id=project.id, diagram_id=uuid.uuid4())

    async def test_lists_most_recent_first(self, db_session):
        _, project = await _make_user_and_project(db_session, "diagram7@example.com")
        gateway = FakeLLMGateway()
        first = await visuals_service.generate_diagram(
            db_session,
            gateway,
            project_id=project.id,
            diagram_type="sequence",
            subject="First",
            milestone_id=None,
            code=None,
        )
        second = await visuals_service.generate_diagram(
            db_session,
            gateway,
            project_id=project.id,
            diagram_type="sequence",
            subject="Second",
            milestone_id=None,
            code=None,
        )

        items, total = await visuals_service.list_diagrams(db_session, project.id, limit=20, offset=0)

        assert total == 2
        assert items[0].id == second.id
        assert items[1].id == first.id
