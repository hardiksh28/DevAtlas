"""Repository Ingestion Engine — request/response schemas.

Every route in router.py takes and returns one of these — never a bare
dict — matching every other module's convention (see projects/schemas.py).
"""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator

_URL_MAX_LENGTH = 2048


class RepositoryIngestRequest(BaseModel):
    repo_url: str = Field(..., min_length=1, max_length=_URL_MAX_LENGTH)

    @field_validator("repo_url")
    @classmethod
    def _not_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("repo_url cannot be blank")
        return stripped


class RepositoryConnectionRead(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    repo_url: str
    owner: str
    name: str
    default_branch: str
    primary_language: str | None
    framework: str | None
    package_manager: str | None
    total_files: int
    total_folders: int
    metadata: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_model(cls, connection: "object") -> "RepositoryConnectionRead":
        # Explicit adapter, not from_attributes — the response field is
        # named `metadata` while the column is `repo_metadata` (SQLAlchemy's
        # Base reserves the plain `metadata` attribute name), same
        # reasoning as knowledge/schemas.py's ProjectDocumentRead.
        return cls(
            id=connection.id,  # type: ignore[attr-defined]
            project_id=connection.project_id,  # type: ignore[attr-defined]
            repo_url=connection.repo_url,  # type: ignore[attr-defined]
            owner=connection.owner,  # type: ignore[attr-defined]
            name=connection.name,  # type: ignore[attr-defined]
            default_branch=connection.default_branch,  # type: ignore[attr-defined]
            primary_language=connection.primary_language,  # type: ignore[attr-defined]
            framework=connection.framework,  # type: ignore[attr-defined]
            package_manager=connection.package_manager,  # type: ignore[attr-defined]
            total_files=connection.total_files,  # type: ignore[attr-defined]
            total_folders=connection.total_folders,  # type: ignore[attr-defined]
            metadata=connection.repo_metadata,  # type: ignore[attr-defined]
            created_at=connection.created_at,  # type: ignore[attr-defined]
            updated_at=connection.updated_at,  # type: ignore[attr-defined]
        )
