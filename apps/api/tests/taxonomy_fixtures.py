"""Shared test helpers for seeding taxonomy data directly via the ORM.
Not a test file itself (no `test_` prefix — pytest won't collect it),
mirroring tests/knowledge_fixtures.py.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.taxonomy.models import Concept, ConceptPrerequisite


async def create_concept(
    db: AsyncSession,
    concept_id: str,
    *,
    stack: str = "python",
    stack_version: str = "3.12",
    severity: str = "foundational",
    prerequisites: list[str] | None = None,
    mastery_criteria: list[str] | None = None,
    common_misconceptions: list[str] | None = None,
    docs: list[str] | None = None,
) -> Concept:
    concept = Concept(
        id=concept_id,
        stack=stack,
        stack_version=stack_version,
        severity=severity,
        mastery_criteria=mastery_criteria or [],
        common_misconceptions=common_misconceptions or [],
        docs=docs or [],
    )
    db.add(concept)
    await db.flush()

    for prereq_id in prerequisites or []:
        db.add(ConceptPrerequisite(concept_id=concept_id, prerequisite_id=prereq_id))
    await db.flush()

    return concept
