"""Repository Ingestion Engine — GitHub fetch helpers.

Plain `httpx` calls, not `services/ingestion_worker/pipeline/fetch.py`'s
SSRF-hardened `safe_get`: that machinery exists because a website crawl
follows attacker-influenced URLs (arbitrary hosts, redirect chains).
Every request here targets a URL this module built itself from a
string-literal host (`api.github.com` / `raw.githubusercontent.com`)
plus a regex-validated owner/repo — the exact case
`knowledge/validation.py`'s `parse_github_repo_url` docstring already
notes needs no DNS-rebinding defense, since there's no way to smuggle a
private-network target through it. Also a separate uv workspace member
from `services/ingestion_worker`, so importing its fetch module isn't
an option even if it were wanted (see ingestion-engine-v1.md Section 2).
"""

import json

import httpx

from app.core.config import get_settings
from app.modules.repo_ingestion.exceptions import (
    RepositoryNotFoundError,
    RepositoryTooLargeError,
    RepositoryTreeTruncatedError,
    RepositoryUpstreamError,
)

_API_ROOT = "https://api.github.com"


def _auth_headers() -> dict[str, str]:
    settings = get_settings()
    headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
    if settings.github_api_token:
        headers["Authorization"] = f"Bearer {settings.github_api_token}"
    return headers


async def _get_json(client: httpx.AsyncClient, url: str) -> dict:
    try:
        response = await client.get(url, headers=_auth_headers())
    except httpx.TransportError as exc:
        raise RepositoryUpstreamError(f"Network error contacting GitHub: {exc}") from exc
    if response.status_code in (403, 429, 500, 502, 503, 504):
        raise RepositoryUpstreamError(f"GitHub returned {response.status_code} for {url}")
    return response.json() if response.content else {}


async def fetch_repo_metadata(client: httpx.AsyncClient, owner: str, repo: str) -> dict:
    """Raises RepositoryNotFoundError/RepositoryTooLargeError — both
    knowable before any file is ever fetched."""
    settings = get_settings()
    repo_info = await _get_json(client, f"{_API_ROOT}/repos/{owner}/{repo}")

    if "id" not in repo_info or repo_info.get("private"):
        raise RepositoryNotFoundError(owner, repo)

    size_bytes = repo_info.get("size", 0) * 1024  # GitHub reports `size` in KB
    if size_bytes > settings.ingestion_max_github_repo_bytes:
        raise RepositoryTooLargeError(settings.ingestion_max_github_repo_bytes)
    return repo_info


async def fetch_repo_tree(client: httpx.AsyncClient, owner: str, repo: str, ref: str) -> list[dict]:
    """Returns every entry (files and directories) in the repo's tree
    at `ref`. Recursive + non-paginated, same as the Documentation
    Ingestion Engine's equivalent call — GitHub silently truncates very
    large trees instead of erroring, which is why that's checked
    explicitly rather than trusted to just work."""
    url = f"{_API_ROOT}/repos/{owner}/{repo}/git/trees/{ref}?recursive=1"
    tree_response = await _get_json(client, url)
    if tree_response.get("truncated"):
        raise RepositoryTreeTruncatedError()
    return tree_response.get("tree", [])


async def fetch_raw_file(
    client: httpx.AsyncClient, owner: str, repo: str, ref: str, path: str, *, max_bytes: int
) -> bytes | None:
    """Returns the file's raw bytes, or None if it doesn't exist (a
    manifest file simply being absent isn't an error this pass cares
    about). Aborts a response over `max_bytes` rather than buffering it
    fully — these are metadata reads (package.json, a lockfile), never
    expected to be large."""
    url = f"https://raw.githubusercontent.com/{owner}/{repo}/{ref}/{path}"
    try:
        async with client.stream("GET", url) as response:
            if response.status_code == 404:
                return None
            if response.status_code in (403, 429, 500, 502, 503, 504):
                raise RepositoryUpstreamError(f"GitHub returned {response.status_code} for {url}")
            chunks: list[bytes] = []
            total = 0
            async for chunk in response.aiter_bytes():
                total += len(chunk)
                if total > max_bytes:
                    return b"".join(chunks)  # truncated read is fine for our metadata-only use
                chunks.append(chunk)
            return b"".join(chunks)
    except httpx.TransportError as exc:
        raise RepositoryUpstreamError(f"Network error fetching {url}: {exc}") from exc


def parse_package_json(raw: bytes) -> dict:
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return {}
    return data if isinstance(data, dict) else {}
