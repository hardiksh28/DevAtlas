"""Markdown parsing — separates YAML front-matter from body content.
The chunker (chunking.chunk_markdown_like) does the actual heading-aware
splitting directly against the body text, so parsing's only job here is
pulling front-matter metadata out and resolving a title.
"""

import re

import yaml

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?\n)---\s*\n?", re.DOTALL)
_H1_RE = re.compile(r"^#\s+(.*)$", re.MULTILINE)
_HEADING_RE = re.compile(r"^#{1,6}\s+(.*)$", re.MULTILINE)


def parse_markdown(raw_text: str) -> tuple[str, dict]:
    """Returns (body_text, front_matter_dict)."""
    match = _FRONTMATTER_RE.match(raw_text)
    if not match:
        return raw_text, {}

    front_matter: dict = {}
    try:
        parsed = yaml.safe_load(match.group(1))
        if isinstance(parsed, dict):
            front_matter = parsed
    except yaml.YAMLError:
        # Malformed front-matter shouldn't fail ingestion of an
        # otherwise-fine document — fall back to treating the whole
        # file (including the "---" fences) as body text.
        return raw_text, {}

    return raw_text[match.end() :], front_matter


def extract_title(body: str, front_matter: dict) -> str | None:
    """Front-matter `title` wins, then the first H1, else None (the
    caller falls back to the filename)."""
    if isinstance(front_matter.get("title"), str) and front_matter["title"].strip():
        return front_matter["title"].strip()
    h1_match = _H1_RE.search(body)
    if h1_match:
        return h1_match.group(1).strip()
    return None


def extract_heading_outline(body: str) -> list[str]:
    return [match.group(1).strip() for match in _HEADING_RE.finditer(body)]
