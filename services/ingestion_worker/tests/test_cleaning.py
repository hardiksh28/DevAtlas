"""Unit tests for pipeline.cleaning."""

from pipeline.cleaning import normalize_text, strip_repeated_boilerplate


class TestNormalizeText:
    def test_collapses_excess_blank_lines(self):
        assert normalize_text("a\n\n\n\n\nb") == "a\n\nb"

    def test_strips_trailing_whitespace_per_line(self):
        assert normalize_text("a   \nb\t\n") == "a\nb"

    def test_strips_control_characters(self):
        assert normalize_text("a\x00\x01b") == "ab"

    def test_normalizes_unicode_compatibility_forms(self):
        # U+FB01 LATIN SMALL LIGATURE FI -> "fi" under NFKC.
        assert normalize_text("ﬁle") == "file"

    def test_strips_leading_and_trailing_overall_whitespace(self):
        assert normalize_text("\n\n  hello  \n\n") == "hello"


class TestStripRepeatedBoilerplate:
    def test_removes_lines_repeated_across_most_pages(self):
        pages = [
            "Header\nUnique content one\nFooter",
            "Header\nUnique content two\nFooter",
            "Header\nUnique content three\nFooter",
            "Header\nUnique content four\nFooter",
        ]
        cleaned = strip_repeated_boilerplate(pages)
        for page in cleaned:
            assert "Header" not in page
            assert "Footer" not in page
        assert "Unique content one" in cleaned[0]

    def test_leaves_pages_untouched_when_too_few_to_compare(self):
        pages = ["Header\nContent\nFooter", "Header\nContent 2\nFooter"]
        assert strip_repeated_boilerplate(pages) == pages

    def test_does_not_remove_content_that_only_repeats_occasionally(self):
        pages = [
            "Common intro\nUnique A",
            "Different intro\nUnique B",
            "Different intro\nUnique C",
            "Different intro\nUnique D",
        ]
        cleaned = strip_repeated_boilerplate(pages)
        assert "Common intro" in cleaned[0]  # appeared on only 1/4 pages — not boilerplate
