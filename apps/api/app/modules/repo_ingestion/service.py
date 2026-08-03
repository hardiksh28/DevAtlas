"""Repository Ingestion Engine — service layer.

All business logic lives here, not in router.py (see projects/service.py's
own docstring for why). Scope is deliberately bounded to structural
metadata: parse the URL, pull repo info + a file tree from GitHub, read
a handful of known manifest files, derive language/framework/package
manager/file counts, persist one row per project. No content parsing,
no chunking, no queue — every GitHub call this makes is already
size-capped (repo size before fetching anything, tree-entry count,
per-file byte cap), so unlike the Documentation Ingestion Engine this
stays comfortably inside a single request/response cycle and never
needs a background job.
"""

import re
import uuid
from datetime import UTC, datetime

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.modules.repo_ingestion.exceptions import (
    InvalidRepositoryUrlError,
    RepositoryConnectionNotFoundError,
    TooManyFilesError,
)
from app.modules.repo_ingestion.github import (
    fetch_raw_file,
    fetch_repo_metadata,
    fetch_repo_tree,
    parse_package_json,
)
from app.modules.repo_ingestion.models import RepositoryConnection

settings = get_settings()

_GITHUB_REPO_RE = re.compile(
    r"^https://github\.com/(?P<owner>[A-Za-z0-9._-]+)/(?P<repo>[A-Za-z0-9._-]+?)(?:\.git)?/?$"
)

# Same four directories the task calls out, plus the two the Documentation
# Ingestion Engine's own github.py already excludes for the same reason
# (never worth counting or reading into).
_IGNORED_DIR_PARTS = {"node_modules", ".git", "dist", "build", ".next", "coverage"}

_MANIFEST_NAMES = (
    "package.json",
    "readme.md",
    "tsconfig.json",
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
)

# Checked in priority order — a Next.js repo depends on react too, so
# the meta-framework has to win over the base library it's built on.
_FRAMEWORK_MARKERS: list[tuple[str, str]] = [
    ("next", "Next.js"),
    ("nuxt", "Nuxt"),
    ("@nestjs/core", "NestJS"),
    ("@angular/core", "Angular"),
    ("svelte", "Svelte"),
    ("vue", "Vue"),
    ("express", "Express"),
    ("fastify", "Fastify"),
    ("react", "React"),
]

_README_EXCERPT_LENGTH = 500


def parse_github_repo_url(url: str) -> tuple[str, str]:
    """Returns (owner, repo). Same shape and reasoning as
    knowledge/validation.py's identical function — duplicated rather
    than imported cross-module, matching how exceptions.py mirrors
    projects/exceptions.py's shape instead of sharing a base class."""
    match = _GITHUB_REPO_RE.match(url.strip())
    if not match:
        raise InvalidRepositoryUrlError(
            "Expected a public GitHub repository URL, e.g. https://github.com/owner/repo"
        )
    return match.group("owner"), match.group("repo")


def _is_ignored(path: str) -> bool:
    return any(part in _IGNORED_DIR_PARTS for part in path.split("/"))


def _detect_package_manager(present: dict[str, str]) -> str | None:
    if "pnpm-lock.yaml" in present:
        return "pnpm"
    if "yarn.lock" in present:
        return "yarn"
    if "package-lock.json" in present:
        return "npm"
    return None


def _detect_framework(package_json: dict) -> str | None:
    deps = {**package_json.get("dependencies", {}), **package_json.get("devDependencies", {})}
    for marker, framework in _FRAMEWORK_MARKERS:
        if marker in deps:
            return framework
    return None


async def sync_repository(
    db: AsyncSession, client: httpx.AsyncClient, *, project_id: uuid.UUID, repo_url: str
) -> RepositoryConnection:
    owner, repo = parse_github_repo_url(repo_url)
    repo_info = await fetch_repo_metadata(client, owner, repo)
    ref = repo_info["default_branch"]

    tree = await fetch_repo_tree(client, owner, repo, ref)
    if len(tree) > settings.repo_ingestion_max_tree_entries:
        raise TooManyFilesError(settings.repo_ingestion_max_tree_entries)

    live_entries = [entry for entry in tree if not _is_ignored(entry.get("path", ""))]
    total_files = sum(1 for e in live_entries if e.get("type") == "blob")
    total_folders = sum(1 for e in live_entries if e.get("type") == "tree")

    # Root-level manifests only — a nested package.json inside a
    # workspace member isn't "the" project manifest for this pass.
    present = {
        entry["path"].lower(): entry["path"]
        for entry in live_entries
        if entry.get("type") == "blob"
        and "/" not in entry["path"]
        and entry["path"].lower() in _MANIFEST_NAMES
    }

    package_json: dict = {}
    if "package.json" in present:
        raw = await fetch_raw_file(
            client, owner, repo, ref, present["package.json"],
            max_bytes=settings.repo_ingestion_max_manifest_file_bytes,
        )
        if raw is not None:
            package_json = parse_package_json(raw)

    readme_excerpt = None
    if "readme.md" in present:
        raw = await fetch_raw_file(
            client, owner, repo, ref, present["readme.md"],
            max_bytes=settings.repo_ingestion_max_manifest_file_bytes,
        )
        if raw is not None:
            readme_excerpt = raw.decode("utf-8", errors="replace")[:_README_EXCERPT_LENGTH]

    connection = await _get_connection(db, project_id)
    if connection is None:
        connection = RepositoryConnection(project_id=project_id)
        db.add(connection)

    connection.repo_url = repo_url
    connection.owner = owner
    connection.name = repo_info.get("name", repo)
    connection.default_branch = ref
    connection.primary_language = repo_info.get("language")
    connection.framework = _detect_framework(package_json) if package_json else None
    connection.package_manager = _detect_package_manager(present)
    connection.total_files = total_files
    connection.total_folders = total_folders
    connection.repo_metadata = {
        "manifests_found": sorted(present.values()),
        "dependencies": sorted(package_json.get("dependencies", {}).keys()),
        "readme_excerpt": readme_excerpt,
        "synced_at": datetime.now(UTC).isoformat(),
    }

    await db.commit()
    await db.refresh(connection)
    return connection


async def _get_connection(db: AsyncSession, project_id: uuid.UUID) -> RepositoryConnection | None:
    result = await db.execute(
        select(RepositoryConnection).where(RepositoryConnection.project_id == project_id)
    )
    return result.scalar_one_or_none()


async def get_connection(db: AsyncSession, project_id: uuid.UUID) -> RepositoryConnection:
    connection = await _get_connection(db, project_id)
    if connection is None:
        raise RepositoryConnectionNotFoundError()
    return connection


async def delete_connection(db: AsyncSession, connection: RepositoryConnection) -> None:
    await db.delete(connection)
    await db.commit()
