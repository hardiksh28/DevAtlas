"""Documentation website parsing — crawls same-origin pages starting
from a root URL, converting each page's main content into the same
heading-prefixed, fenced-code-block plain text that markdown files
already are (see chunking.py's module docstring for why that lets one
chunker serve both source types).
"""

import logging
from collections import deque
from typing import Any
from urllib import robotparser
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup, NavigableString, Tag

from pipeline.fetch import USER_AGENT, safe_get
from settings import config

logger = logging.getLogger(__name__)

_BOILERPLATE_TAGS = ("script", "style", "nav", "footer", "header", "aside", "noscript", "form")
_HEADING_TAGS = {"h1": 1, "h2": 2, "h3": 3, "h4": 4, "h5": 5, "h6": 6}
_TEXT_TAGS = ("p", "li", "td", "th", "blockquote", "figcaption")


def _same_origin(base: str, candidate: str) -> bool:
    return urlparse(base).netloc == urlparse(candidate).netloc


async def _load_robots_parser(client: httpx.AsyncClient, root_url: str) -> robotparser.RobotFileParser:
    parser = robotparser.RobotFileParser()
    robots_url = urljoin(root_url, "/robots.txt")
    try:
        raw = await safe_get(client, robots_url, max_bytes=1_000_000)
        parser.parse(raw.decode("utf-8", errors="replace").splitlines())
    except Exception:
        # No robots.txt, or it failed to fetch/parse — default to
        # "everything allowed" rather than blocking the whole crawl
        # over a missing courtesy file.
        logger.debug("robots.txt unavailable for %s; defaulting to allow-all", root_url)
        parser.parse([])
    return parser


def html_to_markdown_like(html: str) -> tuple[str, str | None]:
    """Returns (text, title). Strips nav/script/style/etc. boilerplate,
    converts <h1>-<h6> to '#'-prefixed lines and <pre> blocks to fenced
    code blocks, and drops everything else down to plain text."""
    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.get_text(strip=True) if soup.title else None

    for tag_name in _BOILERPLATE_TAGS:
        for tag in soup.find_all(tag_name):
            tag.decompose()

    main = soup.find("main") or soup.find("article") or soup.body or soup
    lines: list[str] = []

    def walk(node: Any) -> None:
        if isinstance(node, NavigableString) or not isinstance(node, Tag):
            return
        if node.name in _HEADING_TAGS:
            text = node.get_text(" ", strip=True)
            if text:
                lines.append(f"{'#' * _HEADING_TAGS[node.name]} {text}")
            return
        if node.name == "pre":
            code_text = node.get_text("\n")
            if code_text.strip():
                lines.append(f"```\n{code_text}\n```")
            return
        if node.name in _TEXT_TAGS:
            text = node.get_text(" ", strip=True)
            if text:
                lines.append(text)
            return
        for child in node.children:
            walk(child)

    walk(main)
    return "\n\n".join(lines), title


def extract_links(html: str, page_url: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    links = []
    for anchor in soup.find_all("a", href=True):
        absolute = urljoin(page_url, anchor["href"])
        parsed = urlparse(absolute)
        if parsed.scheme in ("http", "https"):
            links.append(absolute.split("#")[0])
    return links


async def crawl(
    client: httpx.AsyncClient, root_url: str, *, max_pages: int, max_depth: int
) -> list[dict[str, str]]:
    """Breadth-first, same-origin, robots.txt-respecting crawl. Returns
    [{"url": ..., "html": ...}] for every page discovered, capped at
    max_pages. A single page failing to fetch is skipped, not fatal to
    the whole crawl — the same per-document error isolation
    process_document applies later, just one stage earlier."""
    robots = await _load_robots_parser(client, root_url)

    visited: set[str] = set()
    queue: deque[tuple[str, int]] = deque([(root_url, 0)])
    pages: list[dict[str, str]] = []

    while queue and len(pages) < max_pages:
        url, depth = queue.popleft()
        normalized = url.split("#")[0]
        if normalized in visited:
            continue
        visited.add(normalized)

        if not robots.can_fetch(USER_AGENT, normalized):
            continue

        try:
            raw = await safe_get(client, normalized, max_bytes=config.ingestion_max_fetch_bytes)
        except Exception as exc:
            logger.debug("Skipping page that failed to fetch during crawl: %s (%s)", normalized, exc)
            continue

        html = raw.decode("utf-8", errors="replace")
        pages.append({"url": normalized, "html": html})

        if depth < max_depth:
            for link in extract_links(html, normalized):
                if _same_origin(root_url, link) and link not in visited:
                    queue.append((link, depth + 1))

    return pages
