"""Unit tests for app.modules.knowledge.retrieval.context_builder —
pure function, no DB/network needed."""

import uuid

from app.modules.knowledge.retrieval.context_builder import build_context
from app.modules.knowledge.retrieval.retrieval_service import RetrievedChunk


def _make_chunk(content: str, *, title: str = "Doc", heading_path: list[str] | None = None, **extra) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=uuid.uuid4(),
        document_id=uuid.uuid4(),
        project_id=uuid.uuid4(),
        content=content,
        heading_path=heading_path or [],
        chunk_metadata=extra,
        source_type="markdown_file",
        source_path="intro.md",
        title=title,
    )


class TestBuildContext:
    def test_includes_all_chunks_within_budget(self):
        chunks = [_make_chunk("short content one"), _make_chunk("short content two")]
        context = build_context(chunks, max_tokens=1000)
        assert len(context.sources) == 2
        assert not context.truncated
        assert "short content one" in context.text
        assert "short content two" in context.text

    def test_truncates_once_budget_exceeded(self):
        # Each chunk is ~400 chars => ~100 tokens; a 150-token budget
        # should fit exactly one.
        chunks = [_make_chunk("word " * 100), _make_chunk("word " * 100)]
        context = build_context(chunks, max_tokens=150)
        assert len(context.sources) == 1
        assert context.truncated

    def test_always_includes_first_chunk_even_if_oversized(self):
        chunks = [_make_chunk("word " * 10_000)]
        context = build_context(chunks, max_tokens=10)
        assert len(context.sources) == 1
        assert not context.truncated  # nothing was left out — there was only one chunk

    def test_citation_indices_are_sequential_and_one_based(self):
        chunks = [_make_chunk("a"), _make_chunk("b"), _make_chunk("c")]
        context = build_context(chunks, max_tokens=10_000)
        assert [s.index for s in context.sources] == [1, 2, 3]
        assert "[1]" in context.text
        assert "[2]" in context.text
        assert "[3]" in context.text

    def test_heading_breadcrumb_and_page_number_appear_in_formatted_block(self):
        chunk = _make_chunk("content", heading_path=["Guide", "Install"], page_number=4)
        context = build_context([chunk], max_tokens=10_000)
        assert "Guide > Install" in context.text
        assert "page 4" in context.text

    def test_empty_input_returns_empty_context(self):
        context = build_context([], max_tokens=1000)
        assert context.text == ""
        assert context.sources == []
        assert context.total_tokens == 0
        assert not context.truncated

    def test_sources_carry_score_and_ids_through(self):
        chunk = _make_chunk("content")
        chunk.score = 0.42
        context = build_context([chunk], max_tokens=1000)
        assert context.sources[0].score == 0.42
        assert context.sources[0].chunk_id == chunk.chunk_id
        assert context.sources[0].document_id == chunk.document_id
