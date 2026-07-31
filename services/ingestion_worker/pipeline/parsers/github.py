"""GitHub repository parsing — discovers documentation files via the
GitHub REST API (tree listing) and fetches each one's raw content via
raw.githubusercontent.com.

Deliberately API + raw-fetch rather than `git clone`: every request
goes through pipeline/fetch.py's SSRF-safe wrapper this way, and file
count/total size can be checked *before* fetching any content at all —
a clone has already pulled everything to disk by the time you'd know
it was too big.
"""

import json

import httpx

from pipeline.errors import PermanentIngestionError
from pipeline.fetch import safe_get
from settings import config

_DOC_EXTENSIONS = (".md", ".mdx", ".markdown", ".rst", ".txt")
_EXCLUDED_DIR_PARTS = ("node_modules", ".git", "dist", "build", "vendor", "__pycache__")
_API_ROOT = "https://api.github.com"
_METADATA_FETCH_CAP = 2_000_000  # API responses (repo info, tree listing) are small JSON, not content


def _auth_headers() -> dict[str, str]:
    headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
    if config.github_api_token:
        headers["Authorization"] = f"Bearer {config.github_api_token}"
    return headers


async def get_repo_metadata(client: httpx.AsyncClient, owner: str, repo: str) -> dict:
    """Raises PermanentIngestionError if the repo doesn't exist, is
    private, or exceeds the configured size ceiling — all of which are
    known the instant this call returns, before any file is fetched."""
    url = f"{_API_ROOT}/repos/{owner}/{repo}"
    raw = await safe_get(client, url, max_bytes=_METADATA_FETCH_CAP, headers=_auth_headers())
    repo_info = json.loads(raw)

    if "id" not in repo_info:
        raise PermanentIngestionError(
            f"GitHub repo not found or inaccessible: {owner}/{repo}",
            error_code="github_repo_not_found",
        )
    if repo_info.get("private"):
        raise PermanentIngestionError(
            f"{owner}/{repo} is private — only public repositories are supported.",
            error_code="github_repo_private",
        )

    size_bytes = repo_info.get("size", 0) * 1024  # GitHub reports `size` in KB
    if size_bytes > config.ingestion_max_github_repo_bytes:
        raise PermanentIngestionError(
            f"{owner}/{repo} ({size_bytes} bytes) exceeds the "
            f"{config.ingestion_max_github_repo_bytes}-byte repo size limit.",
            error_code="github_repo_too_large",
        )
    return repo_info


async def list_doc_files(client: httpx.AsyncClient, owner: str, repo: str, ref: str) -> list[dict]:
    """Returns [{"path": ..., "size": ...}, ...] for every blob under the
    supported doc extensions, outside excluded directories."""
    url = f"{_API_ROOT}/repos/{owner}/{repo}/git/trees/{ref}?recursive=1"
    raw = await safe_get(client, url, max_bytes=_METADATA_FETCH_CAP, headers=_auth_headers())
    tree_response = json.loads(raw)

    if tree_response.get("truncated"):
        # GitHub silently truncates very large trees instead of
        # erroring — permanent, not retryable: this repo's tree is
        # simply too large for a single non-paginated fetch.
        raise PermanentIngestionError(
            f"{owner}/{repo}'s file tree is too large to list in one request.",
            error_code="github_tree_truncated",
        )

    matched = []
    for entry in tree_response.get("tree", []):
        if entry.get("type") != "blob":
            continue
        path = entry["path"]
        if any(f"/{part}/" in f"/{path}/" for part in _EXCLUDED_DIR_PARTS):
            continue
        if not path.lower().endswith(_DOC_EXTENSIONS):
            continue
        matched.append({"path": path, "size": entry.get("size", 0)})

    if len(matched) > config.ingestion_max_github_files:
        raise PermanentIngestionError(
            f"{owner}/{repo} has {len(matched)} matching documentation files, over the "
            f"{config.ingestion_max_github_files}-file limit.",
            error_code="github_too_many_files",
        )
    return matched


def raw_content_url(owner: str, repo: str, ref: str, path: str) -> str:
    return f"https://raw.githubusercontent.com/{owner}/{repo}/{ref}/{path}"


async def fetch_file_content(client: httpx.AsyncClient, owner: str, repo: str, ref: str, path: str) -> bytes:
    return await safe_get(
        client, raw_content_url(owner, repo, ref, path), max_bytes=config.ingestion_max_fetch_bytes
    )
