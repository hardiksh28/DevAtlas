"""Integration tests for app.modules.mentoring.service, calling service
functions directly against db_session (no HTTP layer) — same pattern as
test_rag_service.py / test_curriculum_service.py."""

import json
from datetime import UTC, datetime, timedelta

import pytest

from app.modules.auth import service as auth_service
from app.modules.curriculum import service as curriculum_service
from app.modules.mentoring import service as mentoring_service
from app.modules.mentoring.exceptions import MentorReplyGenerationError
from app.modules.projects import service as projects_service
from tests.mentoring_fixtures import create_conversation, create_message
from tests.taxonomy_fixtures import create_concept


class FakeLLMGateway:
    def __init__(self, *, reply_response: str | None = None, summary_response: str = "Summary text.") -> None:
        self.reply_response = reply_response or json.dumps(
            {"reply": "Good question — what do you think happens?", "misconceptions_detected": []}
        )
        self.summary_response = summary_response
        self.generate_calls: list[tuple[str, str]] = []
        self.raise_on_generate: Exception | None = None

    async def embed(self, texts: list[str]) -> list[list[float]]:
        return [[0.1] * 768 for _ in texts]

    async def generate(self, operation: str, prompt: str) -> str:
        self.generate_calls.append((operation, prompt))
        if self.raise_on_generate:
            raise self.raise_on_generate
        if operation == "mentor_summarize":
            return self.summary_response
        return self.reply_response


async def _make_user_and_project(db, email: str):
    user = await auth_service.register_user(db, email, "hunter22222", "Owner")
    project = await projects_service.create_project(db, user.id, "Mentor Project", None)
    return user, project


class TestSendMessage:
    async def test_creates_conversation_and_both_messages(self, db_session):
        _, project = await _make_user_and_project(db_session, "mentor1@example.com")
        gateway = FakeLLMGateway(
            reply_response=json.dumps({"reply": "Let's think through it together.", "misconceptions_detected": []})
        )

        user_message, reply = await mentoring_service.send_message(
            db_session, gateway, project_id=project.id, milestone_id=None, content="What is a closure?"
        )

        assert user_message.role == "user"
        assert user_message.content == "What is a closure?"
        assert reply.role == "assistant"
        assert reply.content == "Let's think through it together."
        assert reply.detected_misconceptions == []

    async def test_defaults_experience_level_without_a_roadmap(self, db_session):
        _, project = await _make_user_and_project(db_session, "mentor2@example.com")
        gateway = FakeLLMGateway()

        await mentoring_service.send_message(
            db_session, gateway, project_id=project.id, milestone_id=None, content="hi"
        )

        assert "intermediate" in gateway.generate_calls[0][1]

    async def test_uses_roadmap_experience_level_when_present(self, db_session):
        _, project = await _make_user_and_project(db_session, "mentor3@example.com")
        await create_concept(db_session, "python.variables", severity="foundational")
        await db_session.commit()
        await curriculum_service.generate_or_regenerate_roadmap(
            db_session, project_id=project.id, stack="python", stack_version="3.12", experience_level="advanced"
        )
        gateway = FakeLLMGateway()

        await mentoring_service.send_message(
            db_session, gateway, project_id=project.id, milestone_id=None, content="hi"
        )

        assert "advanced" in gateway.generate_calls[0][1]

    async def test_milestone_context_includes_curated_misconceptions(self, db_session):
        _, project = await _make_user_and_project(db_session, "mentor4@example.com")
        await create_concept(
            db_session,
            "python.async_await",
            severity="intermediate",
            common_misconceptions=["Thinks async def alone is concurrent"],
        )
        await db_session.commit()
        roadmap = await curriculum_service.generate_or_regenerate_roadmap(
            db_session, project_id=project.id, stack="python", stack_version="3.12", experience_level="beginner"
        )
        milestone = roadmap.milestones[0]
        gateway = FakeLLMGateway()

        user_message, _ = await mentoring_service.send_message(
            db_session, gateway, project_id=project.id, milestone_id=milestone.id, content="explain async"
        )

        assert user_message.milestone_id == milestone.id
        assert "Thinks async def alone is concurrent" in gateway.generate_calls[0][1]

    async def test_stores_detected_misconceptions_from_reply(self, db_session):
        _, project = await _make_user_and_project(db_session, "mentor5@example.com")
        gateway = FakeLLMGateway(
            reply_response=json.dumps(
                {"reply": "Careful — that's a common mix-up.", "misconceptions_detected": ["closures capture by value"]}
            )
        )

        _, reply = await mentoring_service.send_message(
            db_session, gateway, project_id=project.id, milestone_id=None, content="I think closures copy the variable"
        )

        assert reply.detected_misconceptions == ["closures capture by value"]

    async def test_retries_once_on_invalid_json_then_succeeds(self, db_session):
        _, project = await _make_user_and_project(db_session, "mentor6@example.com")

        class FlakyGateway(FakeLLMGateway):
            def __init__(self):
                super().__init__()
                self._calls = 0

            async def generate(self, operation, prompt):
                self._calls += 1
                if self._calls == 1:
                    return "not valid json"
                return self.reply_response

        gateway = FlakyGateway()
        _, reply = await mentoring_service.send_message(
            db_session, gateway, project_id=project.id, milestone_id=None, content="hi"
        )
        assert reply.content
        assert gateway._calls == 2

    async def test_raises_after_two_failed_parses(self, db_session):
        _, project = await _make_user_and_project(db_session, "mentor7@example.com")
        gateway = FakeLLMGateway(reply_response="still not json")

        with pytest.raises(MentorReplyGenerationError):
            await mentoring_service.send_message(
                db_session, gateway, project_id=project.id, milestone_id=None, content="hi"
            )

    async def test_gateway_failure_raises_mentor_reply_generation_error(self, db_session):
        _, project = await _make_user_and_project(db_session, "mentor8@example.com")
        gateway = FakeLLMGateway()
        gateway.raise_on_generate = RuntimeError("Ollama is down")

        with pytest.raises(MentorReplyGenerationError):
            await mentoring_service.send_message(
                db_session, gateway, project_id=project.id, milestone_id=None, content="hi"
            )


class TestHistoryCompaction:
    async def test_compacts_older_messages_once_threshold_exceeded(self, db_session):
        _, project = await _make_user_and_project(db_session, "mentor9@example.com")
        conversation = await create_conversation(db_session, project.id)

        base = datetime.now(UTC) - timedelta(hours=1)
        for i in range(19):
            await create_message(
                db_session,
                conversation,
                role="user" if i % 2 == 0 else "assistant",
                content=f"turn {i}",
                created_at=base + timedelta(seconds=i),
            )
        await db_session.commit()

        gateway = FakeLLMGateway(summary_response="Learner covered closures and scope.")
        await mentoring_service.send_message(
            db_session, gateway, project_id=project.id, milestone_id=None, content="one more question"
        )

        await db_session.refresh(conversation)
        assert conversation.summary == "Learner covered closures and scope."
        assert conversation.summarized_up_to is not None
        assert any(op == "mentor_summarize" for op, _ in gateway.generate_calls)

        # Older messages are never deleted — append-only transcript.
        _, total = await mentoring_service.list_messages(db_session, project.id, limit=100, offset=0)
        assert total == 19 + 2  # seeded turns + this exchange's user/assistant pair

    async def test_no_compaction_below_threshold(self, db_session):
        _, project = await _make_user_and_project(db_session, "mentor10@example.com")
        gateway = FakeLLMGateway()

        await mentoring_service.send_message(
            db_session, gateway, project_id=project.id, milestone_id=None, content="hi"
        )

        assert not any(op == "mentor_summarize" for op, _ in gateway.generate_calls)


class TestListMessages:
    async def test_returns_empty_when_no_conversation_exists(self, db_session):
        _, project = await _make_user_and_project(db_session, "mentor11@example.com")
        items, total = await mentoring_service.list_messages(db_session, project.id, limit=10, offset=0)
        assert items == []
        assert total == 0

    async def test_paginates_in_chronological_order(self, db_session):
        _, project = await _make_user_and_project(db_session, "mentor12@example.com")
        conversation = await create_conversation(db_session, project.id)
        base = datetime.now(UTC) - timedelta(minutes=10)
        for i in range(5):
            await create_message(db_session, conversation, content=f"m{i}", created_at=base + timedelta(seconds=i))
        await db_session.commit()

        items, total = await mentoring_service.list_messages(db_session, project.id, limit=2, offset=1)

        assert total == 5
        assert [m.content for m in items] == ["m1", "m2"]
