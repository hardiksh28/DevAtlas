"""Metadata Extraction stage — shared helpers.

Most metadata is source-type-specific (page_count from pypdf, a repo's
commit sha from the GitHub API, a markdown file's front-matter) and is
assembled inline in worker.py's process_document, right next to the
parser call that produced it. This module only holds the handful of
computations every source type needs identically.
"""

import hashlib
import re

_SLUG_RE = re.compile(r"[^a-z0-9]+")


def sha256_hex(data: bytes | str) -> str:
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def slugify(text: str) -> str:
    """Used for a chunk's `url_anchor` metadata (website source type) —
    a best-effort reconstruction of the deep link a browser would jump
    to for that heading, not a guarantee of matching the site's own
    anchor-generation rules exactly."""
    return _SLUG_RE.sub("-", text.lower()).strip("-")
