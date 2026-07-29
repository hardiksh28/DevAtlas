"""Project Workspace — request/response schemas.

Every route in router.py takes and returns one of these — never a bare
dict — matching every other module's convention (see auth/schemas.py).
"""

import json
import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

_NAME_MAX_LENGTH = 200
_DESCRIPTION_MAX_LENGTH = 4000

ProjectStatus = Literal["active", "archived", "deleted"]
ProjectColor = Literal["slate", "blue", "green", "amber", "rose", "violet"]


def _blank_to_none(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=_NAME_MAX_LENGTH)
    description: str | None = Field(None, max_length=_DESCRIPTION_MAX_LENGTH)

    @field_validator("name")
    @classmethod
    def _name_not_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("name cannot be blank")
        return stripped

    @field_validator("description")
    @classmethod
    def _description_blank_to_none(cls, value: str | None) -> str | None:
        return _blank_to_none(value)


class ProjectUpdate(BaseModel):
    """Partial update — every field optional, matching PATCH semantics.
    `None` in the payload means "leave unchanged," not "clear the
    field" (there's no distinct way to clear `description` in V1; add
    a sentinel if that's ever needed)."""

    name: str | None = Field(None, min_length=1, max_length=_NAME_MAX_LENGTH)
    description: str | None = Field(None, max_length=_DESCRIPTION_MAX_LENGTH)

    @field_validator("name")
    @classmethod
    def _name_not_blank(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        if not stripped:
            raise ValueError("name cannot be blank")
        return stripped

    @field_validator("description")
    @classmethod
    def _description_blank_to_none(cls, value: str | None) -> str | None:
        return _blank_to_none(value)


class ProjectRead(BaseModel):
    id: uuid.UUID
    owner_id: uuid.UUID
    name: str
    description: str | None
    status: ProjectStatus
    # Flattened in from `project.settings` (icon/color live on
    # ProjectSettings, a 1:1 loaded via lazy="joined" — see models.py)
    # so every card render gets them for free in the same query as the
    # project itself, no separate settings fetch per card.
    icon: str
    color: ProjectColor
    archived_at: datetime | None
    deleted_at: datetime | None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_model(cls, project: "object") -> "ProjectRead":
        return cls(
            id=project.id,  # type: ignore[attr-defined]
            owner_id=project.owner_id,  # type: ignore[attr-defined]
            name=project.name,  # type: ignore[attr-defined]
            description=project.description,  # type: ignore[attr-defined]
            status=project.status,  # type: ignore[attr-defined]
            icon=project.settings.icon,  # type: ignore[attr-defined]
            color=project.settings.color,  # type: ignore[attr-defined]
            archived_at=project.archived_at,  # type: ignore[attr-defined]
            deleted_at=project.deleted_at,  # type: ignore[attr-defined]
            created_at=project.created_at,  # type: ignore[attr-defined]
            updated_at=project.updated_at,  # type: ignore[attr-defined]
        )


class ProjectListResponse(BaseModel):
    items: list[ProjectRead]
    total: int
    limit: int
    offset: int


class ProjectSettingsRead(BaseModel):
    project_id: uuid.UUID
    icon: str
    color: ProjectColor
    settings: dict
    updated_at: datetime

    model_config = {"from_attributes": True}


_SETTINGS_JSON_MAX_BYTES = 10_000


class ProjectSettingsUpdate(BaseModel):
    icon: str | None = Field(None, min_length=1, max_length=16)
    color: ProjectColor | None = None
    settings: dict | None = None

    @field_validator("settings")
    @classmethod
    def _settings_size_bounded(cls, value: dict | None) -> dict | None:
        # `settings` is an open JSONB catch-all (see models.py) with no
        # column-level length limit the way `name`/`description` have —
        # without a cap here, a client could PATCH an arbitrarily large
        # blob repeatedly, a cheap storage-abuse vector for an already-
        # authenticated caller.
        if value is not None and len(json.dumps(value)) > _SETTINGS_JSON_MAX_BYTES:
            raise ValueError(f"settings must serialize to at most {_SETTINGS_JSON_MAX_BYTES} bytes")
        return value


class RecentProjectRead(BaseModel):
    """A recently-viewed project, flattened with its own view
    timestamp — the dashboard rail needs both in one shape rather than
    a raw ProjectRead plus a separate lookup."""

    project: ProjectRead
    last_viewed_at: datetime


class DashboardResponse(BaseModel):
    active_count: int
    archived_count: int
    recent_projects: list[RecentProjectRead]
