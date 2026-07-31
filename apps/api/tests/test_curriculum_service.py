"""Integration tests for app.modules.curriculum.service, calling
service functions directly against db_session (no HTTP layer) — same
pattern as test_rag_service.py."""

import json

import pytest

from app.modules.auth import service as auth_service
from app.modules.curriculum import service as curriculum_service
from app.modules.curriculum.exceptions import (
    ContentGenerationError,
    InvalidMilestoneTransitionError,
    MilestoneNotFoundError,
    RoadmapNotFoundError,
)
from app.modules.projects import service as projects_service
from app.modules.taxonomy.exceptions import StackNotFoundError
from tests.taxonomy_fixtures import create_concept


class FakeLLMGateway:
    def __init__(self, *, response: str | None = None) -> None:
        self.response = response or json.dumps(
            {
                "explanation": "Explanation text.",
                "key_points": ["point one"],
                "exercises": [{"prompt": "Do the thing.", "hint": None}],
                "quiz": [
                    {
                        "question": "Which one?",
                        "options": ["a", "b"],
                        "correct_index": 0,
                        "explanation": "Because a.",
                    }
                ],
            }
        )
        self.generate_calls: list[str] = []
        self.raise_on_generate: Exception | None = None

    async def embed(self, texts: list[str]) -> list[list[float]]:
        return [[0.1] * 768 for _ in texts]

    async def generate(self, operation: str, prompt: str) -> str:
        self.generate_calls.append(prompt)
        if self.raise_on_generate:
            raise self.raise_on_generate
        return self.response


async def _make_user_and_project(db, email: str):
    user = await auth_service.register_user(db, email, "hunter22222", "Owner")
    project = await projects_service.create_project(db, user.id, "Test Project", None)
    return user, project


async def _seed_python_stack(db):
    await create_concept(
        db,
        "python.variables",
        severity="foundational",
        mastery_criteria=["Can explain variable binding"],
    )
    await create_concept(
        db, "python.functions", severity="foundational", prerequisites=["python.variables"]
    )
    await create_concept(
        db,
        "python.async_await",
        severity="intermediate",
        prerequisites=["python.functions"],
        mastery_criteria=["Can explain await"],
        common_misconceptions=["Thinks async def alone is concurrent"],
    )
    await db.commit()


class TestGenerateRoadmap:
    async def test_generates_roadmap_with_ordered_milestones(self, db_session):
        _, project = await _make_user_and_project(db_session, "gen1@example.com")
        await _seed_python_stack(db_session)

        roadmap = await curriculum_service.generate_or_regenerate_roadmap(
            db_session,
            project_id=project.id,
            stack="python",
            stack_version="3.12",
            experience_level="beginner",
        )

        concept_ids = [m.concept_id for m in roadmap.milestones]
        assert concept_ids == ["python.variables", "python.functions", "python.async_await"]
        assert roadmap.milestones[0].status == "available"  # first milestone auto-unlocked
        assert roadmap.milestones[1].status == "locked"
        assert roadmap.estimated_total_minutes > 0

    async def test_advanced_learner_skips_foundational_unless_required(self, db_session):
        _, project = await _make_user_and_project(db_session, "gen2@example.com")
        # Two independent branches off python.variables: python.functions
        # (intermediate, feeds the advanced concept) and
        # python.error_handling (intermediate, but nothing advanced
        # depends on it) — this is what makes "advanced genuinely skips
        # something" testable, rather than every concept being required
        # transitively anyway.
        await create_concept(db_session, "python.variables", severity="foundational")
        await create_concept(
            db_session, "python.functions", severity="intermediate", prerequisites=["python.variables"]
        )
        await create_concept(
            db_session,
            "python.error_handling",
            severity="intermediate",
            prerequisites=["python.variables"],
        )
        await create_concept(
            db_session,
            "python.decorators",
            severity="advanced",
            prerequisites=["python.functions"],
        )
        await db_session.commit()

        roadmap = await curriculum_service.generate_or_regenerate_roadmap(
            db_session,
            project_id=project.id,
            stack="python",
            stack_version="3.12",
            experience_level="advanced",
        )

        concept_ids = {m.concept_id for m in roadmap.milestones}
        # python.decorators (advanced) pulls in python.functions and
        # python.variables transitively even though they're below the
        # "advanced" floor; python.error_handling is genuinely skipped —
        # nothing selected requires it.
        assert concept_ids == {"python.variables", "python.functions", "python.decorators"}

    async def test_unknown_stack_raises(self, db_session):
        _, project = await _make_user_and_project(db_session, "gen3@example.com")

        with pytest.raises(StackNotFoundError):
            await curriculum_service.generate_or_regenerate_roadmap(
                db_session,
                project_id=project.id,
                stack="nonexistent",
                stack_version="1",
                experience_level="beginner",
            )

    async def test_no_duplicate_milestone_per_concept(self, db_session):
        _, project = await _make_user_and_project(db_session, "gen4@example.com")
        await _seed_python_stack(db_session)

        roadmap = await curriculum_service.generate_or_regenerate_roadmap(
            db_session,
            project_id=project.id,
            stack="python",
            stack_version="3.12",
            experience_level="beginner",
        )
        concept_ids = [m.concept_id for m in roadmap.milestones]
        assert len(concept_ids) == len(set(concept_ids))


class TestRegenerateWithoutLosingProgress:
    async def test_completed_milestone_survives_regeneration(self, db_session):
        _, project = await _make_user_and_project(db_session, "regen1@example.com")
        await _seed_python_stack(db_session)

        roadmap = await curriculum_service.generate_or_regenerate_roadmap(
            db_session,
            project_id=project.id,
            stack="python",
            stack_version="3.12",
            experience_level="beginner",
        )
        first_milestone = roadmap.milestones[0]
        assert first_milestone.concept_id == "python.variables"

        await curriculum_service.update_milestone_status(
            db_session, project.id, first_milestone.id, "in_progress"
        )
        completed = await curriculum_service.update_milestone_status(
            db_session, project.id, first_milestone.id, "completed"
        )
        assert completed.status == "completed"

        # Add a new, more advanced concept to the stack and regenerate —
        # the completed milestone must keep its id and status.
        await create_concept(
            db_session,
            "python.decorators",
            severity="advanced",
            prerequisites=["python.functions"],
        )
        await db_session.commit()

        regenerated = await curriculum_service.generate_or_regenerate_roadmap(
            db_session,
            project_id=project.id,
            stack="python",
            stack_version="3.12",
            experience_level="beginner",
        )

        variables_milestone = next(
            m for m in regenerated.milestones if m.concept_id == "python.variables"
        )
        assert variables_milestone.id == first_milestone.id
        assert variables_milestone.status == "completed"
        assert regenerated.version == 2
        assert any(m.concept_id == "python.decorators" for m in regenerated.milestones)

    async def test_never_started_milestone_dropped_when_stack_changes(self, db_session):
        _, project = await _make_user_and_project(db_session, "regen2@example.com")
        await _seed_python_stack(db_session)
        await create_concept(db_session, "react.components_and_props", stack="react", stack_version="18")
        await db_session.commit()

        await curriculum_service.generate_or_regenerate_roadmap(
            db_session,
            project_id=project.id,
            stack="python",
            stack_version="3.12",
            experience_level="beginner",
        )
        regenerated = await curriculum_service.generate_or_regenerate_roadmap(
            db_session,
            project_id=project.id,
            stack="react",
            stack_version="18",
            experience_level="beginner",
        )

        assert [m.concept_id for m in regenerated.milestones] == ["react.components_and_props"]


class TestMilestoneStatusTransitions:
    async def test_invalid_transition_raises(self, db_session):
        _, project = await _make_user_and_project(db_session, "trans1@example.com")
        await _seed_python_stack(db_session)
        roadmap = await curriculum_service.generate_or_regenerate_roadmap(
            db_session,
            project_id=project.id,
            stack="python",
            stack_version="3.12",
            experience_level="beginner",
        )
        locked_milestone = next(m for m in roadmap.milestones if m.status == "locked")

        with pytest.raises(InvalidMilestoneTransitionError):
            await curriculum_service.update_milestone_status(
                db_session, project.id, locked_milestone.id, "in_progress"
            )

    async def test_completing_unlocks_the_next_milestone(self, db_session):
        _, project = await _make_user_and_project(db_session, "trans2@example.com")
        await _seed_python_stack(db_session)
        roadmap = await curriculum_service.generate_or_regenerate_roadmap(
            db_session,
            project_id=project.id,
            stack="python",
            stack_version="3.12",
            experience_level="beginner",
        )
        first, second = roadmap.milestones[0], roadmap.milestones[1]
        assert second.status == "locked"

        await curriculum_service.update_milestone_status(db_session, project.id, first.id, "in_progress")
        await curriculum_service.update_milestone_status(db_session, project.id, first.id, "completed")

        refreshed_roadmap = await curriculum_service.get_roadmap(db_session, project.id)
        refreshed_second = next(m for m in refreshed_roadmap.milestones if m.id == second.id)
        assert refreshed_second.status == "available"


class TestGetRoadmapAndMilestone:
    async def test_get_roadmap_raises_when_none_exists(self, db_session):
        _, project = await _make_user_and_project(db_session, "get1@example.com")
        with pytest.raises(RoadmapNotFoundError):
            await curriculum_service.get_roadmap(db_session, project.id)

    async def test_get_milestone_scoped_to_project_raises_for_other_project(self, db_session):
        _, project_a = await _make_user_and_project(db_session, "get2a@example.com")
        _, project_b = await _make_user_and_project(db_session, "get2b@example.com")
        await _seed_python_stack(db_session)
        roadmap = await curriculum_service.generate_or_regenerate_roadmap(
            db_session,
            project_id=project_a.id,
            stack="python",
            stack_version="3.12",
            experience_level="beginner",
        )
        milestone = roadmap.milestones[0]

        with pytest.raises(MilestoneNotFoundError):
            await curriculum_service.get_milestone(db_session, project_b.id, milestone.id)


class TestGenerateMilestoneContent:
    async def test_generates_and_stores_parsed_content(self, db_session):
        _, project = await _make_user_and_project(db_session, "content1@example.com")
        await _seed_python_stack(db_session)
        roadmap = await curriculum_service.generate_or_regenerate_roadmap(
            db_session,
            project_id=project.id,
            stack="python",
            stack_version="3.12",
            experience_level="beginner",
        )
        milestone = roadmap.milestones[0]
        gateway = FakeLLMGateway()

        updated = await curriculum_service.generate_milestone_content(
            db_session, gateway, project_id=project.id, milestone_id=milestone.id
        )

        assert updated.lesson_content is not None
        assert updated.lesson_content["explanation"] == "Explanation text."
        assert updated.content_version == 1
        assert len(gateway.generate_calls) == 1

    async def test_retries_once_on_invalid_json_then_succeeds(self, db_session):
        _, project = await _make_user_and_project(db_session, "content2@example.com")
        await _seed_python_stack(db_session)
        roadmap = await curriculum_service.generate_or_regenerate_roadmap(
            db_session,
            project_id=project.id,
            stack="python",
            stack_version="3.12",
            experience_level="beginner",
        )
        milestone = roadmap.milestones[0]

        class FlakyGateway(FakeLLMGateway):
            def __init__(self):
                super().__init__()
                self._call_count = 0

            async def generate(self, operation: str, prompt: str) -> str:
                self._call_count += 1
                if self._call_count == 1:
                    return "not valid json"
                return self.response

        gateway = FlakyGateway()
        updated = await curriculum_service.generate_milestone_content(
            db_session, gateway, project_id=project.id, milestone_id=milestone.id
        )

        assert updated.lesson_content is not None
        assert gateway._call_count == 2

    async def test_raises_content_generation_error_after_two_failed_parses(self, db_session):
        _, project = await _make_user_and_project(db_session, "content3@example.com")
        await _seed_python_stack(db_session)
        roadmap = await curriculum_service.generate_or_regenerate_roadmap(
            db_session,
            project_id=project.id,
            stack="python",
            stack_version="3.12",
            experience_level="beginner",
        )
        milestone = roadmap.milestones[0]
        gateway = FakeLLMGateway(response="still not valid json")

        with pytest.raises(ContentGenerationError):
            await curriculum_service.generate_milestone_content(
                db_session, gateway, project_id=project.id, milestone_id=milestone.id
            )

    async def test_gateway_failure_raises_content_generation_error(self, db_session):
        _, project = await _make_user_and_project(db_session, "content4@example.com")
        await _seed_python_stack(db_session)
        roadmap = await curriculum_service.generate_or_regenerate_roadmap(
            db_session,
            project_id=project.id,
            stack="python",
            stack_version="3.12",
            experience_level="beginner",
        )
        milestone = roadmap.milestones[0]
        gateway = FakeLLMGateway()
        gateway.raise_on_generate = RuntimeError("Ollama is down")

        with pytest.raises(ContentGenerationError):
            await curriculum_service.generate_milestone_content(
                db_session, gateway, project_id=project.id, milestone_id=milestone.id
            )
