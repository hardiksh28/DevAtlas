"""Cleaning stage — normalizes raw parsed text before chunking.

HTML boilerplate (nav/footer/script/style tags) is already stripped by
parsers/website.py itself, since removing it requires the DOM structure
this stage no longer has. What's left here is source-agnostic: unicode
normalization, whitespace collapsing, and stripping mechanical
artifacts that repeat across an entire multi-page document (PDF running
headers/footers, a website's repeated cookie-banner text) — the kind of
noise that's only detectable by comparing pages against each other, not
by looking at any single page in isolation.
"""

import re
import unicodedata
from collections import Counter

_MULTI_BLANK_RE = re.compile(r"\n{3,}")
_TRAILING_WS_RE = re.compile(r"[ \t]+\n")
_CONTROL_CHARS_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


def normalize_text(text: str) -> str:
    """Unicode NFKC normalization, control-character stripping, and
    whitespace collapsing — applied to every document regardless of
    source type, always before chunking."""
    text = unicodedata.normalize("NFKC", text)
    text = _CONTROL_CHARS_RE.sub("", text)
    text = _TRAILING_WS_RE.sub("\n", text)
    text = _MULTI_BLANK_RE.sub("\n\n", text)
    return text.strip()


def strip_repeated_boilerplate(pages: list[str], *, min_repeat_ratio: float = 0.6) -> list[str]:
    """Drops lines that appear near-identically across most pages of a
    multi-page document — a line repeated across at least
    `min_repeat_ratio` of pages is boilerplate by definition (real
    content varies page to page; running headers/footers and repeated
    nav text don't). Used for PDF pages and, in principle, any other
    multi-page source; a 1-2 page document has no meaningful "repeated
    across pages" signal, so it's left untouched.
    """
    if len(pages) < 3:
        return pages

    line_counts: Counter[str] = Counter()
    for page in pages:
        seen_this_page = {line.strip() for line in page.splitlines() if line.strip()}
        line_counts.update(seen_this_page)

    threshold = max(2, int(len(pages) * min_repeat_ratio))
    boilerplate = {line for line, count in line_counts.items() if count >= threshold}

    cleaned_pages = []
    for page in pages:
        kept_lines = [line for line in page.splitlines() if line.strip() not in boilerplate]
        cleaned_pages.append("\n".join(kept_lines))
    return cleaned_pages
