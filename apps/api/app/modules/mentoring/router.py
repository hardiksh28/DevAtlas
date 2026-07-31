"""Mentoring / Hint Ladder Engine — router.

Two routers, mirroring knowledge/curriculum's own split: `router`
(`/v1/mentoring`) stays the pre-existing stub. `mentor_router`
(`/v1/projects/{project_id}/mentor`) is the conversational mentor built
in this pass, nested under its owning project.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.cost_control.limits import llm_rate_limit
from app.modules.llm_gateway.gateway import LLMGateway, get_llm_gateway
from app.modules.mentoring import service
from app.modules.mentoring.schemas import (
    MessageListResponse,
    MessageRead,
    SendMessageRequest,
    SendMessageResponse,
)
from app.modules.projects.dependencies import get_owned_project
from app.modules.projects.models import Project

router = APIRouter(prefix="/v1/mentoring", tags=["Mentoring / Hint Ladder Engine"])

mentor_router = APIRouter(
    prefix="/v1/projects/{project_id}/mentor", tags=["Mentoring — Conversational Mentor"]
)


@mentor_router.post(
    "/messages",
    response_model=SendMessageResponse,
    dependencies=[llm_rate_limit("mentor_message", times=60, seconds=3600)],
)
async def send_message(
    payload: SendMessageRequest,
    project: Project = Depends(get_owned_project),
    db: AsyncSession = Depends(get_db),
    gateway: LLMGateway = Depends(get_llm_gateway),
) -> SendMessageResponse:
    user_message, reply = await service.send_message(
        db,
        gateway,
        project_id=project.id,
        milestone_id=payload.milestone_id,
        content=payload.content,
    )
    return SendMessageResponse(
        user_message=MessageRead.from_model(user_message), reply=MessageRead.from_model(reply)
    )


@mentor_router.get("/messages", response_model=MessageListResponse)
async def list_messages(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    project: Project = Depends(get_owned_project),
    db: AsyncSession = Depends(get_db),
) -> MessageListResponse:
    items, total = await service.list_messages(db, project.id, limit, offset)
    return MessageListResponse(
        items=[MessageRead.from_model(m) for m in items], total=total, limit=limit, offset=offset
    )
