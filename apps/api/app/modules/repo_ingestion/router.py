"""Repository Ingestion Engine — router.

Nested under /v1/projects/{project_id}/repository, same pattern as
knowledge/router.py's project_documents_router and curriculum/router.py's
roadmap_router: a resource-scoped route lives under its owning project's
prefix, ownership enforced by projects.dependencies.get_owned_project.

Thin HTTP layer only: every handler extracts what it needs, calls
service.py, and shapes the result via schemas.py.
"""

from collections.abc import AsyncGenerator

import httpx
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.projects.dependencies import get_owned_project
from app.modules.projects.models import Project
from app.modules.repo_ingestion import service
from app.modules.repo_ingestion.schemas import RepositoryConnectionRead, RepositoryIngestRequest

router = APIRouter(prefix="/v1/projects/{project_id}/repository", tags=["Repository Ingestion"])

_USER_AGENT = "DevAtlas-RepoIngestion/1.0"


async def get_http_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    async with httpx.AsyncClient(timeout=10.0, headers={"User-Agent": _USER_AGENT}) as client:
        yield client


@router.post("", response_model=RepositoryConnectionRead, status_code=status.HTTP_201_CREATED)
async def ingest_repository(
    payload: RepositoryIngestRequest,
    project: Project = Depends(get_owned_project),
    db: AsyncSession = Depends(get_db),
    client: httpx.AsyncClient = Depends(get_http_client),
) -> RepositoryConnectionRead:
    """Clones nothing to disk — reads the repo's tree and a handful of
    root manifests straight from the GitHub API (see service.py) and
    replaces this project's existing connection, if any."""
    connection = await service.sync_repository(
        db, client, project_id=project.id, repo_url=payload.repo_url
    )
    return RepositoryConnectionRead.from_model(connection)


@router.get("", response_model=RepositoryConnectionRead)
async def get_repository(
    project: Project = Depends(get_owned_project),
    db: AsyncSession = Depends(get_db),
) -> RepositoryConnectionRead:
    connection = await service.get_connection(db, project.id)
    return RepositoryConnectionRead.from_model(connection)


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def delete_repository(
    project: Project = Depends(get_owned_project),
    db: AsyncSession = Depends(get_db),
) -> None:
    connection = await service.get_connection(db, project.id)
    await service.delete_connection(db, connection)
