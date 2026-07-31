"""Unit tests for pipeline.chunking — pure functions, no DB/network."""

from pipeline.chunking import approx_token_count, chunk_markdown_like, chunk_pdf_pages


class TestApproxTokenCount:
    def test_scales_with_length(self):
        assert approx_token_count("a" * 40) == 10

    def test_never_zero_for_nonempty_text(self):
        assert approx_token_count("a") >= 1


class TestChunkMarkdownLike:
    def test_single_short_document_is_one_chunk(self):
        text = "# Title\n\nJust a short paragraph."
        chunks = chunk_markdown_like(text, target_tokens=200, overlap_tokens=20)
        assert len(chunks) == 1
        assert chunks[0].heading_path == ["Title"]

    def test_heading_path_tracks_nested_sections(self):
        text = (
            "# Guide\n\n"
            "Intro text.\n\n"
            "## Installation\n\n"
            "Install steps.\n\n"
            "### Requirements\n\n"
            "Need Python 3.12.\n\n"
            "## Usage\n\n"
            "Usage text.\n"
        )
        chunks = chunk_markdown_like(text, target_tokens=8, overlap_tokens=0)
        heading_paths = [c.heading_path for c in chunks]
        assert ["Guide"] in heading_paths
        assert ["Guide", "Installation"] in heading_paths
        assert ["Guide", "Installation", "Requirements"] in heading_paths
        assert ["Guide", "Usage"] in heading_paths

    def test_never_splits_inside_a_fenced_code_block(self):
        text = "# Title\n\n```python\nline1\nline2\nline3\n```\n\nAfter code."
        chunks = chunk_markdown_like(text, target_tokens=5, overlap_tokens=0)
        code_chunks = [c for c in chunks if c.chunk_metadata.get("is_code_heavy")]
        assert code_chunks
        for chunk in code_chunks:
            assert chunk.content.count("```") % 2 == 0  # every fence opened is closed

    def test_no_chunk_exceeds_target_tokens_even_for_one_long_paragraph(self):
        text = "# Title\n\n" + ("word " * 500)
        chunks = chunk_markdown_like(text, target_tokens=50, overlap_tokens=5)
        # A small overshoot is acceptable (word-boundary splitting isn't
        # exact), but nothing should be wildly over budget.
        assert all(c.token_count <= 60 for c in chunks)

    def test_overlap_carries_trailing_text_into_next_chunk(self):
        text = "# Title\n\n" + "\n\n".join(f"Paragraph number {i}." for i in range(20))
        chunks = chunk_markdown_like(text, target_tokens=15, overlap_tokens=10)
        assert len(chunks) > 1
        # The overlap tail from chunk N should reappear at the start of
        # chunk N+1's content.
        first_tail = chunks[0].content[-20:]
        assert first_tail[-5:] in chunks[1].content

    def test_empty_text_returns_no_chunks(self):
        assert chunk_markdown_like("", target_tokens=200, overlap_tokens=20) == []

    def test_chunk_position_is_sequential(self):
        text = "# Title\n\n" + "\n\n".join(f"Paragraph {i}." for i in range(10))
        chunks = chunk_markdown_like(text, target_tokens=10, overlap_tokens=0)
        positions = [c.chunk_metadata["chunk_position"] for c in chunks]
        assert positions == list(range(len(chunks)))


class TestChunkPdfPages:
    def test_one_chunk_per_short_page(self):
        pages = ["Short page one.", "Short page two."]
        chunks = chunk_pdf_pages(pages, target_tokens=200, overlap_tokens=0)
        assert len(chunks) == 2
        assert [c.chunk_metadata["page_number"] for c in chunks] == [1, 2]
        assert chunks[0].heading_path == []  # PDF chunks never carry a heading path

    def test_long_page_splits_into_multiple_chunks_with_same_page_number(self):
        pages = ["Paragraph. " * 100]
        chunks = chunk_pdf_pages(pages, target_tokens=30, overlap_tokens=5)
        assert len(chunks) > 1
        assert all(c.chunk_metadata["page_number"] == 1 for c in chunks)

    def test_blank_pages_produce_no_chunks(self):
        pages = ["", "   ", "\n\n"]
        assert chunk_pdf_pages(pages, target_tokens=200, overlap_tokens=0) == []
