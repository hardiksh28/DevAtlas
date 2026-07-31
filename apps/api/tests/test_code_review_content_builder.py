"""Unit tests for app.modules.code_review.content_builder and
prompt_builder — pure, no DB/network involved."""

import json

import pytest

from app.modules.code_review.content_builder import ReviewParseError, parse_review_output
from app.modules.code_review.prompt_builder import build_review_prompt, number_lines

_VALID_COMMENT = {
    "file_path": "app.py",
    "line_start": 2,
    "line_end": 2,
    "category": "bug",
    "severity": "major",
    "body": "What happens if `items` is empty here?",
    "suggestion": "Guard with an early return.",
    "concept_tags": ["python.iteration"],
}


def _payload(**overrides):
    payload = {
        "overall_score": 72,
        "summary": "Solid first pass, one real bug.",
        "strengths": ["Clear naming"],
        "comments": [_VALID_COMMENT],
        "refactoring_ideas": ["Extract the loop body into a helper."],
    }
    payload.update(overrides)
    return payload


class TestParseReviewOutput:
    def test_parses_valid_json(self):
        parsed = parse_review_output(json.dumps(_payload()), total_lines=5, max_comments=10)
        assert parsed.overall_score == 72
        assert len(parsed.comments) == 1
        assert parsed.comments[0].category == "bug"

    def test_strips_markdown_code_fence(self):
        fenced = f"```json\n{json.dumps(_payload())}\n```"
        parsed = parse_review_output(fenced, total_lines=5, max_comments=10)
        assert parsed.overall_score == 72

    def test_drops_comments_whose_lines_fall_outside_the_submitted_code(self):
        out_of_range = _payload(
            comments=[_VALID_COMMENT, {**_VALID_COMMENT, "line_start": 99, "line_end": 99}]
        )
        parsed = parse_review_output(json.dumps(out_of_range), total_lines=5, max_comments=10)
        assert len(parsed.comments) == 1
        assert parsed.comments[0].line_start == 2

    def test_truncates_to_max_comments_by_severity(self):
        comments = [
            {**_VALID_COMMENT, "line_start": 1, "line_end": 1, "severity": "info"},
            {**_VALID_COMMENT, "line_start": 2, "line_end": 2, "severity": "critical"},
            {**_VALID_COMMENT, "line_start": 3, "line_end": 3, "severity": "minor"},
        ]
        parsed = parse_review_output(
            json.dumps(_payload(comments=comments)), total_lines=5, max_comments=1
        )
        assert len(parsed.comments) == 1
        assert parsed.comments[0].severity == "critical"

    def test_invalid_json_raises(self):
        with pytest.raises(ReviewParseError):
            parse_review_output("not json at all", total_lines=5, max_comments=10)

    def test_score_out_of_range_raises(self):
        with pytest.raises(ReviewParseError):
            parse_review_output(
                json.dumps(_payload(overall_score=150)), total_lines=5, max_comments=10
            )

    def test_missing_required_field_raises(self):
        with pytest.raises(ReviewParseError):
            parse_review_output(json.dumps({"summary": "x"}), total_lines=5, max_comments=10)


class TestNumberLines:
    def test_numbers_from_one(self):
        numbered, total = number_lines("a = 1\nb = 2")
        assert numbered == "1: a = 1\n2: b = 2"
        assert total == 2

    def test_empty_code_still_has_one_line(self):
        _numbered, total = number_lines("")
        assert total == 1


class TestBuildReviewPrompt:
    def test_includes_language_file_and_code(self):
        numbered, _ = number_lines("def f():\n    pass")
        prompt = build_review_prompt(
            experience_level="beginner",
            max_comments=5,
            concept_context="",
            retrieved_context="",
            file_path="app.py",
            language="python",
            numbered_code=numbered,
        )
        assert "beginner" in prompt
        assert "app.py" in prompt
        assert "python" in prompt
        assert "1: def f():" in prompt
        assert "at most 5" in prompt

    def test_includes_concept_and_retrieved_context_when_present(self):
        numbered, _ = number_lines("x = 1")
        prompt = build_review_prompt(
            experience_level="advanced",
            max_comments=20,
            concept_context="python.async_await (severity: intermediate)",
            retrieved_context="Use asyncio.gather for concurrency.",
            file_path="app.py",
            language="python",
            numbered_code=numbered,
        )
        assert "python.async_await" in prompt
        assert "asyncio.gather" in prompt
