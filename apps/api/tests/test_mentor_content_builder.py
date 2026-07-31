"""Unit tests for app.modules.mentoring.content_builder and
prompt_builder — pure, no DB/network involved."""

import json

import pytest

from app.modules.mentoring.content_builder import MentorReplyParseError, parse_mentor_reply
from app.modules.mentoring.prompt_builder import build_mentor_prompt, build_summary_prompt

_VALID_PAYLOAD = {
    "reply": "What do you think happens when you call `await` outside an async function?",
    "misconceptions_detected": ["Assuming async def alone makes a function concurrent"],
}


class TestParseMentorReply:
    def test_parses_valid_json(self):
        parsed = parse_mentor_reply(json.dumps(_VALID_PAYLOAD))
        assert parsed.reply == _VALID_PAYLOAD["reply"]
        assert parsed.misconceptions_detected == _VALID_PAYLOAD["misconceptions_detected"]

    def test_strips_markdown_code_fence(self):
        fenced = f"```json\n{json.dumps(_VALID_PAYLOAD)}\n```"
        parsed = parse_mentor_reply(fenced)
        assert parsed.reply == _VALID_PAYLOAD["reply"]

    def test_defaults_misconceptions_to_empty_list(self):
        parsed = parse_mentor_reply(json.dumps({"reply": "Good question."}))
        assert parsed.misconceptions_detected == []

    def test_invalid_json_raises(self):
        with pytest.raises(MentorReplyParseError):
            parse_mentor_reply("not json at all")

    def test_missing_required_field_raises(self):
        with pytest.raises(MentorReplyParseError):
            parse_mentor_reply(json.dumps({"misconceptions_detected": []}))


class TestBuildMentorPrompt:
    def test_includes_experience_level_and_question(self):
        prompt = build_mentor_prompt(
            experience_level="beginner",
            concept_context="",
            retrieved_context="",
            summary=None,
            recent_messages=[],
            question="Why do I need await?",
        )
        assert "beginner" in prompt
        assert "Why do I need await?" in prompt
        assert "(no prior messages)" in prompt

    def test_includes_concept_summary_and_history_when_present(self):
        prompt = build_mentor_prompt(
            experience_level="advanced",
            concept_context="python.async_await (severity: intermediate)",
            retrieved_context="From the project's docs: use asyncio.gather.",
            summary="Learner already understands basic functions.",
            recent_messages=[("user", "hi"), ("assistant", "hello")],
            question="What's next?",
        )
        assert "python.async_await" in prompt
        assert "asyncio.gather" in prompt
        assert "already understands basic functions" in prompt
        assert "user: hi" in prompt
        assert "assistant: hello" in prompt


class TestBuildSummaryPrompt:
    def test_formats_turns_in_order(self):
        prompt = build_summary_prompt([("user", "What is a closure?"), ("assistant", "Good question, what do you think?")])
        assert prompt.index("user: What is a closure?") < prompt.index("assistant: Good question")
