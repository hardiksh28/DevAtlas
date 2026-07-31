"""Shared test helpers for seeding roadmap/milestone data directly via
the ORM. Not a test file itself (no `test_` prefix), mirroring
tests/knowledge_fixtures.py.
"""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.curriculum.models import Milestone, Roadmap


async def create_roadmap(
    db: AsyncSession,
    project_id: uuid.UUID,
    *,
    stack: str = "python",
    stack_version: str = "3.12",
    experience_level: str = "beginner",
) -> Roadmap:
    roadmap = Roadmap(
        project_id=project_id,
        stack=stack,
        stack_version=stack_version,
        experience_level=experience_level,
    )
    db.add(roadmap)
    await db.flush()
    return roadmap


async def create_milestone(
    db: AsyncSession,
    roadmap: Roadmap,
    concept_id: str,
    *,
    sequence_index: int = 0,
    status: str = "locked",
    estimated_minutes: int = 30,
) -> Milestone:
    milestone = Milestone(
        roadmap_id=roadmap.id,
        concept_id=concept_id,
        sequence_index=sequence_index,
        status=status,
        title=concept_id,
        estimated_minutes=estimated_minutes,
    )
    db.add(milestone)
    await db.flush()
    return milestone
