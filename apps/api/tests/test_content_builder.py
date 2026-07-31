"""Unit tests for app.modules.curriculum.content_builder — pure,
no DB/network involved (see that module's docstring)."""

import json

import pytest

from app.modules.curriculum.content_builder import (
    LessonContentParseError,
    build_milestone_prompt,
    parse_milestone_content,
)

_VALID_PAYLOAD = {
    "explanation": "Async/await lets you write non-blocking code that reads like sync code.",
    "key_points": ["await only works inside async def", "asyncio.gather runs coroutines concurrently"],
    "exercises": [{"prompt": "Write an async function that fetches two URLs concurrently.", "hint": "Use asyncio.gather"}],
    "quiz": [
        {
            "question": "What happens if you call `await` outside an async function?",
            "options": ["SyntaxError", "It just blocks", "Nothing"],
            "correct_index": 0,
            "explanation": "await is only valid inside an async def.",
        }
    ],
}


class TestBuildMilestonePrompt:
    def test_includes_concept_metadata_and_experience_level(self):
        prompt = build_milestone_prompt(
            concept_id="python.async_await",
            severity="intermediate",
            mastery_criteria=["Can explain why await is required"],
            common_misconceptions=["Thinking async def alone is concurrent"],
            experience_level="beginner",
            context_text="",
        )
        assert "python.async_await" in prompt
        assert "beginner" in prompt
        assert "Can explain why await is required" in prompt
        assert "Thinking async def alone is concurrent" in prompt

    def test_empty_context_gets_a_placeholder_not_a_blank_section(self):
        prompt = build_milestone_prompt(
            concept_id="c",
            severity="foundational",
            mastery_criteria=[],
            common_misconceptions=[],
            experience_level="beginner",
            context_text="",
        )
        assert "no project documentation available" in prompt


class TestParseMilestoneContent:
    def test_parses_valid_json(self):
        content = parse_milestone_content(json.dumps(_VALID_PAYLOAD))
        assert content.explanation == _VALID_PAYLOAD["explanation"]
        assert len(content.exercises) == 1
        assert len(content.quiz) == 1

    def test_strips_markdown_code_fence(self):
        fenced = f"```json\n{json.dumps(_VALID_PAYLOAD)}\n```"
        content = parse_milestone_content(fenced)
        assert content.explanation == _VALID_PAYLOAD["explanation"]

    def test_invalid_json_raises_parse_error(self):
        with pytest.raises(LessonContentParseError):
            parse_milestone_content("this is not json at all")

    def test_valid_json_wrong_shape_raises_parse_error(self):
        with pytest.raises(LessonContentParseError):
            parse_milestone_content(json.dumps({"unexpected": "shape"}))

    def test_quiz_correct_index_out_of_range_raises_parse_error(self):
        bad = dict(_VALID_PAYLOAD)
        bad["quiz"] = [{**_VALID_PAYLOAD["quiz"][0], "correct_index": 5}]
        with pytest.raises(LessonContentParseError):
            parse_milestone_content(json.dumps(bad))

    def test_duplicate_exercises_are_deduped(self):
        payload = dict(_VALID_PAYLOAD)
        exercise = _VALID_PAYLOAD["exercises"][0]
        payload["exercises"] = [exercise, dict(exercise), {**exercise, "prompt": "A different exercise."}]

        content = parse_milestone_content(json.dumps(payload))

        assert len(content.exercises) == 2  # the exact duplicate was dropped

    def test_duplicate_quiz_questions_are_deduped_case_and_whitespace_insensitive(self):
        payload = dict(_VALID_PAYLOAD)
        q = _VALID_PAYLOAD["quiz"][0]
        variant = {**q, "question": "  WHAT happens IF you call `await`   outside an async function?  "}
        payload["quiz"] = [q, variant]

        content = parse_milestone_content(json.dumps(payload))

        assert len(content.quiz) == 1
