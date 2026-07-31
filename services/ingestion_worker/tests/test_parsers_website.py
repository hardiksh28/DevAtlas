"""Unit tests for pipeline.parsers.website's pure (non-network) helpers."""

from pipeline.parsers.website import extract_links, html_to_markdown_like


class TestHtmlToMarkdownLike:
    def test_strips_boilerplate_tags(self):
        html = (
            "<html><head><title>My Page</title></head><body>"
            "<nav>Site nav</nav>"
            "<main><h1>Intro</h1><p>Hello world</p></main>"
            "<footer>Copyright 2026</footer>"
            "</body></html>"
        )
        text, title = html_to_markdown_like(html)
        assert title == "My Page"
        assert "Site nav" not in text
        assert "Copyright" not in text
        assert "# Intro" in text
        assert "Hello world" in text

    def test_converts_headings_to_hash_prefixed_lines(self):
        html = "<body><h1>Top</h1><h2>Sub</h2><p>Text</p></body>"
        text, _ = html_to_markdown_like(html)
        assert "# Top" in text
        assert "## Sub" in text

    def test_converts_pre_blocks_to_fenced_code(self):
        html = "<body><main><pre><code>print(1)</code></pre></main></body>"
        text, _ = html_to_markdown_like(html)
        assert "```" in text
        assert "print(1)" in text

    def test_missing_title_returns_none(self):
        _, title = html_to_markdown_like("<body><p>No title here</p></body>")
        assert title is None


class TestExtractLinks:
    def test_resolves_relative_links_against_page_url(self):
        html = '<a href="/docs/intro">Intro</a>'
        links = extract_links(html, "https://example.com/home")
        assert links == ["https://example.com/docs/intro"]

    def test_includes_absolute_links(self):
        html = '<a href="https://other.example.com/page">Other</a>'
        links = extract_links(html, "https://example.com/")
        assert links == ["https://other.example.com/page"]

    def test_drops_fragment_identifiers(self):
        html = '<a href="/docs/intro#section-2">Intro</a>'
        links = extract_links(html, "https://example.com/")
        assert links == ["https://example.com/docs/intro"]

    def test_ignores_non_http_schemes(self):
        html = '<a href="mailto:hello@example.com">Email</a><a href="javascript:void(0)">JS</a>'
        assert extract_links(html, "https://example.com/") == []
