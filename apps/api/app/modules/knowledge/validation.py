"""Request-path validation for the Documentation Ingestion Engine's
Upload → Validation pipeline stage (docs/architecture/ingestion-engine-v1.md).

Deliberately cheap and network-free — this runs synchronously inside an
HTTP request, so it only checks what's knowable from the request itself
(file extension/magic bytes/size, URL shape, obviously-unsafe hosts).
The *thorough* version of "is this actually reachable, and safe to
fetch" — DNS resolution, redirect-chain re-validation, content-type
sniffing of the real response — happens in the worker's
pipeline/fetch.py, because that's where the actual (potentially
many, for a website crawl) network calls happen. Two layers, same
reasoning as Auth's rate limiter existing at both the request and
account level: catch what's cheap to catch early, never rely on the
cheap layer alone for something security-sensitive.
"""

import ipaddress
import re
from urllib.parse import urlparse

from schemas import SourceType

from app.modules.knowledge.exceptions import (
    InvalidSourceUrlError,
    UnsupportedSourceError,
    UploadTooLargeError,
)

_MARKDOWN_EXTENSIONS = (".md", ".markdown", ".mdx")
_PDF_EXTENSION = ".pdf"
_PDF_MAGIC = b"%PDF-"

_GITHUB_REPO_RE = re.compile(
    r"^https://github\.com/(?P<owner>[A-Za-z0-9._-]+)/(?P<repo>[A-Za-z0-9._-]+?)(?:\.git)?/?$"
)

# Hostnames that are obviously never a legitimate public documentation
# site — checked in addition to the private/loopback IP-literal check
# below, since these resolve to a loopback address via /etc/hosts on
# most systems rather than being an IP literal themselves.
_BLOCKED_HOSTNAME_SUFFIXES = (".local", ".internal", ".localhost")
_BLOCKED_HOSTNAMES = ("localhost",)


def validate_upload_source(
    *, filename: str, content_type: str, size: int, head: bytes, max_bytes: int
) -> SourceType:
    """Returns the detected SourceType, or raises. Only ever called with
    a whole in-memory upload (see the API's own upload size cap in the
    router) — `head` is the same bytes as the full body here, not a
    separate peek, but kept as its own parameter so this function's
    contract doesn't change if uploads are ever streamed instead."""
    if size > max_bytes:
        raise UploadTooLargeError(max_bytes)

    lower_name = filename.lower()
    if lower_name.endswith(_PDF_EXTENSION) or content_type == "application/pdf":
        if not head.startswith(_PDF_MAGIC):
            raise UnsupportedSourceError(
                "File has a .pdf name or content-type but doesn't start with the PDF "
                "magic number — refusing to ingest a mislabeled file."
            )
        return SourceType.PDF_FILE

    if lower_name.endswith(_MARKDOWN_EXTENSIONS) or content_type in (
        "text/markdown",
        "text/x-markdown",
    ):
        try:
            head.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise UnsupportedSourceError(
                "File has a markdown extension/content-type but isn't valid UTF-8 text."
            ) from exc
        return SourceType.MARKDOWN_FILE

    raise UnsupportedSourceError(
        f"Unsupported upload: '{filename}' ({content_type}). "
        "Only Markdown (.md, .markdown, .mdx) and PDF files are accepted."
    )


def parse_github_repo_url(url: str) -> tuple[str, str]:
    """Returns (owner, repo). Only ever accepts the exact
    `https://github.com/{owner}/{repo}` shape — no arbitrary host, no
    query string, no path beyond owner/repo — which is what makes this
    check sufficient on its own (unlike validate_website_url below,
    there's no way to smuggle a private-network target through it: the
    host is a string-literal match against github.com, not attacker-
    controlled)."""
    match = _GITHUB_REPO_RE.match(url.strip())
    if not match:
        raise InvalidSourceUrlError(
            "Expected a public GitHub repository URL, e.g. "
            "https://github.com/owner/repo"
        )
    return match.group("owner"), match.group("repo")


def validate_website_url(url: str) -> str:
    """Cheap shape + obviously-unsafe-host check. Returns the
    normalized URL. Does NOT resolve DNS (a blocking call with no place
    in a request handler, and meaningless protection anyway since
    DNS can rebind between this check and the worker's later fetch) —
    real SSRF protection is enforced by the worker re-checking the
    resolved IP immediately before every request it makes, including
    every redirect hop and every crawled page, not just the root URL
    submitted here."""
    parsed = urlparse(url.strip())
    if parsed.scheme not in ("http", "https"):
        raise InvalidSourceUrlError("URL must use http:// or https://.")
    if not parsed.hostname:
        raise InvalidSourceUrlError("URL is missing a host.")

    hostname = parsed.hostname.lower()
    if hostname in _BLOCKED_HOSTNAMES or hostname.endswith(_BLOCKED_HOSTNAME_SUFFIXES):
        raise InvalidSourceUrlError("This host cannot be crawled.")

    try:
        ip = ipaddress.ip_address(hostname)
    except ValueError:
        pass  # Expected — most doc sites are a domain name, not an IP literal.
    else:
        if not ip.is_global:
            raise InvalidSourceUrlError("This host cannot be crawled.")

    return url.strip()
