"""Unit tests for pipeline.parsers.markdown."""

from pipeline.parsers.markdown import extract_heading_outline, extract_title, parse_markdown


class TestParseMarkdown:
    def test_extracts_frontmatter_and_body(self):
        raw = "---\ntitle: My Doc\ntags:\n  - a\n  - b\n---\n\n# Heading\n\nBody text.\n"
        body, front_matter = parse_markdown(raw)
        assert front_matter == {"title": "My Doc", "tags": ["a", "b"]}
        assert body.strip().startswith("# Heading")

    def test_no_frontmatter_returns_whole_text_as_body(self):
        raw = "# Just a heading\n\nNo front matter here.\n"
        body, front_matter = parse_markdown(raw)
        assert front_matter == {}
        assert body == raw

    def test_malformed_frontmatter_falls_back_to_whole_file_as_body(self):
        raw = "---\nnot: [valid: yaml: at: all\n---\n\nBody.\n"
        body, front_matter = parse_markdown(raw)
        assert front_matter == {}
        assert body == raw


class TestExtractTitle:
    def test_frontmatter_title_wins_over_h1(self):
        body = "# A Different H1\n\nText."
        assert extract_title(body, {"title": "Front Matter Title"}) == "Front Matter Title"

    def test_falls_back_to_first_h1(self):
        body = "Some intro.\n\n# The Real Title\n\nMore text.\n\n# Second H1"
        assert extract_title(body, {}) == "The Real Title"

    def test_returns_none_when_nothing_found(self):
        body = "Just a paragraph, no headings at all."
        assert extract_title(body, {}) is None


class TestExtractHeadingOutline:
    def test_returns_headings_in_document_order(self):
        body = "# Top\n\nText\n\n## Middle\n\nText\n\n### Bottom\n"
        assert extract_heading_outline(body) == ["Top", "Middle", "Bottom"]

    def test_empty_for_no_headings(self):
        assert extract_heading_outline("Just plain text.") == []
