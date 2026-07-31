"""Interactive Learning Workspace — request/response schemas."""

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

_MAX_PATH_LENGTH = 500


def _normalize_path(value: str) -> str:
    stripped = value.strip().strip("/")
    if not stripped:
        raise ValueError("path cannot be blank")
    if len(stripped) > _MAX_PATH_LENGTH:
        raise ValueError(f"path cannot exceed {_MAX_PATH_LENGTH} characters")
    for segment in stripped.split("/"):
        if segment in ("", ".", ".."):
            raise ValueError("path cannot contain empty, '.', or '..' segments")
    return stripped


class WorkspaceFileCreate(BaseModel):
    path: str
    content: str = ""

    @field_validator("path")
    @classmethod
    def _validate_path(cls, value: str) -> str:
        return _normalize_path(value)


class WorkspaceFileRename(BaseModel):
    new_path: str

    @field_validator("new_path")
    @classmethod
    def _validate_new_path(cls, value: str) -> str:
        return _normalize_path(value)


class WorkspaceFileContentUpdate(BaseModel):
    content: str
    # Omitted on a file's first save after creation; required (and
    # checked) on every subsequent save — see service.update_file_content.
    expected_content_hash: str | None = None


class WorkspaceFileMeta(BaseModel):
    id: uuid.UUID
    path: str
    size_bytes: int
    updated_at: datetime

    @classmethod
    def from_model(cls, file: "object") -> "WorkspaceFileMeta":
        return cls(
            id=file.id,  # type: ignore[attr-defined]
            path=file.path,  # type: ignore[attr-defined]
            size_bytes=file.size_bytes,  # type: ignore[attr-defined]
            updated_at=file.updated_at,  # type: ignore[attr-defined]
        )


class WorkspaceFileDetail(WorkspaceFileMeta):
    content: str
    content_hash: str | None

    @classmethod
    def from_model(cls, file: "object") -> "WorkspaceFileDetail":
        return cls(
            id=file.id,  # type: ignore[attr-defined]
            path=file.path,  # type: ignore[attr-defined]
            size_bytes=file.size_bytes,  # type: ignore[attr-defined]
            updated_at=file.updated_at,  # type: ignore[attr-defined]
            content=file.content,  # type: ignore[attr-defined]
            content_hash=file.content_hash,  # type: ignore[attr-defined]
        )


class WorkspaceLayoutUpdate(BaseModel):
    """Every field optional — PATCH semantics, `exclude_unset` in the
    router, same as ProjectSettingsUpdate."""

    open_tabs: list[uuid.UUID] | None = None
    active_tab_id: uuid.UUID | None = None
    panel_sizes: dict[str, float] | None = None
    bottom_panel_visible: bool | None = None
    right_rail_tab: Literal["lesson", "chat", "diagrams"] | None = None
    bottom_panel_tab: Literal["terminal", "preview"] | None = None


class WorkspaceLayoutRead(BaseModel):
    open_tabs: list[uuid.UUID]
    active_tab_id: uuid.UUID | None
    panel_sizes: dict[str, float]
    bottom_panel_visible: bool
    right_rail_tab: str
    bottom_panel_tab: str
    updated_at: datetime

    @classmethod
    def from_model(cls, layout: "object") -> "WorkspaceLayoutRead":
        return cls(
            open_tabs=[uuid.UUID(tab_id) for tab_id in layout.open_tabs],  # type: ignore[attr-defined]
            active_tab_id=layout.active_tab_id,  # type: ignore[attr-defined]
            panel_sizes=layout.panel_sizes,  # type: ignore[attr-defined]
            bottom_panel_visible=layout.bottom_panel_visible,  # type: ignore[attr-defined]
            right_rail_tab=layout.right_rail_tab,  # type: ignore[attr-defined]
            bottom_panel_tab=layout.bottom_panel_tab,  # type: ignore[attr-defined]
            updated_at=layout.updated_at,  # type: ignore[attr-defined]
        )


class WorkspaceFileListResponse(BaseModel):
    items: list[WorkspaceFileMeta] = Field(default_factory=list)
