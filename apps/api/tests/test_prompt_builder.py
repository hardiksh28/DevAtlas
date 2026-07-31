"""Unit tests for app.modules.knowledge.retrieval.prompt_builder /
prompt_templates."""

import uuid

from app.modules.knowledge.retrieval.context_builder import build_context
from app.modules.knowledge.retrieval.prompt_builder import build_prompt
from app.modules.knowledge.retrieval.prompt_templates import SYSTEM_PROMPT
from app.modules.knowledge.retrieval.retrieval_service import RetrievedChunk


def _make_chunk(content: str) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=uuid.uuid4(),
        document_id=uuid.uuid4(),
        project_id=uuid.uuid4(),
        content=content,
        heading_path=[],
        chunk_metadata={},
        source_type="markdown_file",
        source_path="intro.md",
        title="Intro",
    )


class TestBuildPrompt:
    def test_includes_system_instructions_context_and_question(self):
        context = build_context([_make_chunk("Installation requires Python 3.12.")], max_tokens=1000)
        prompt = build_prompt(context, "What Python version is required?")

        assert SYSTEM_PROMPT in prompt
        assert "Installation requires Python 3.12." in prompt
        assert "What Python version is required?" in prompt

    def test_system_prompt_requires_grounding_and_citations(self):
        # These are the two load-bearing hallucination-prevention
        # phrases (rag-engine-v1.md Section 7) — a change here should
        # be a deliberate, reviewed edit, not an accidental regression.
        assert "ONLY" in SYSTEM_PROMPT
        assert "cite" in SYSTEM_PROMPT.lower()
        assert "don't know" in SYSTEM_PROMPT.lower() or "say so" in SYSTEM_PROMPT.lower()

    def test_context_appears_before_question_in_final_prompt(self):
        context = build_context([_make_chunk("Some fact.")], max_tokens=1000)
        prompt = build_prompt(context, "A question?")
        assert prompt.index("Some fact.") < prompt.index("A question?")
