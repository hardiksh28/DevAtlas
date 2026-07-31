"""Taxonomy & Concept Graph Service — router.

Read-only introspection over the curated concept graph (curation itself
happens via scripts/seed_taxonomy.py against the YAML source of truth in
packages/taxonomy-data/, not through this API — see service.py's
docstring). Thin HTTP layer: extract, call service.py, shape via
schemas.py, same pattern as every other module.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.taxonomy import service
from app.modules.taxonomy.schemas import (
    ConceptListResponse,
    ConceptRead,
    StackListResponse,
    StackSummary,
)

router = APIRouter(prefix="/v1/taxonomy", tags=["Taxonomy & Concept Graph"])


@router.get("/stacks", response_model=StackListResponse)
async def list_stacks(db: AsyncSession = Depends(get_db)) -> StackListResponse:
    stacks = await service.list_stacks(db)
    return StackListResponse(
        items=[
            StackSummary(stack=stack, stack_version=version, concept_count=count)
            for stack, version, count in stacks
        ]
    )


@router.get("/stacks/{stack}/concepts", response_model=ConceptListResponse)
async def list_concepts_for_stack(
    stack: str,
    stack_version: str = Query(...),
    db: AsyncSession = Depends(get_db),
) -> ConceptListResponse:
    concepts = await service.get_concepts_for_stack(db, stack, stack_version)
    edges = await service.get_prerequisite_edges(db, [c.id for c in concepts])
    return ConceptListResponse(
        items=[ConceptRead.from_model(c, edges.get(c.id, [])) for c in concepts]
    )
