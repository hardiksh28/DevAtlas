"""Taxonomy & Concept Graph Service — loading, validation, and reads.

Function-based, `db: AsyncSession` first arg — same convention as every
other module's service.py (see knowledge/service.py). Two halves:

1. Seed-time (`load_concepts_from_yaml` / `sync_concepts_for_stack`) —
   run by scripts/seed_taxonomy.py, never by a request handler. This is
   where curated content is validated *once*, loudly, so an authoring
   mistake (a typo'd prerequisite id, an accidental cycle) fails at seed
   time instead of silently breaking roadmap generation later.
2. Request-time (`get_concepts_for_stack` / `get_prerequisite_edges` /
   `list_stacks`) — plain reads against already-validated rows.
"""

from dataclasses import dataclass
from pathlib import Path

import yaml
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.taxonomy.exceptions import StackNotFoundError, TaxonomyValidationError
from app.modules.taxonomy.models import SEVERITIES, Concept, ConceptPrerequisite


@dataclass
class ParsedConcept:
    id: str
    severity: str
    prerequisites: list[str]
    mastery_criteria: list[str]
    common_misconceptions: list[str]
    docs: list[str]


@dataclass
class ParsedStackTaxonomy:
    stack: str
    stack_version: str
    concepts: list[ParsedConcept]


def _check_for_cycle(concept_ids: set[str], edges: dict[str, list[str]]) -> None:
    """Plain DFS cycle detection over the prerequisite graph — a
    concern local to *validating curated content*, deliberately kept
    separate from curriculum/sequencing.py's topological_order (which
    solves a different problem: deterministic milestone order for an
    already-known-acyclic graph). Duplicating a ~10-line DFS here avoids
    taxonomy depending on curriculum, which would invert the module
    boundary (taxonomy is the lower-level module curriculum reads from).
    """
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {cid: WHITE for cid in concept_ids}

    def visit(node: str, path: list[str]) -> None:
        color[node] = GRAY
        for dep in edges.get(node, []):
            if color.get(dep) == GRAY:
                cycle = " -> ".join([*path, node, dep])
                raise TaxonomyValidationError(f"Prerequisite cycle detected: {cycle}")
            if color.get(dep) == WHITE:
                visit(dep, [*path, node])
        color[node] = BLACK

    for cid in concept_ids:
        if color[cid] == WHITE:
            visit(cid, [])


def load_concepts_from_yaml(path: Path | str) -> ParsedStackTaxonomy:
    """Parses and validates one curated taxonomy YAML file. Raises
    TaxonomyValidationError on any unknown severity, dangling
    prerequisite reference, or prerequisite cycle — this is the
    "fail loudly at authoring time" half of the taxonomy's data
    integrity story.
    """
    raw = yaml.safe_load(Path(path).read_text())
    stack = raw["stack"]
    stack_version = str(raw["stack_version"])

    concepts = [
        ParsedConcept(
            id=c["id"],
            severity=c["severity"],
            prerequisites=list(c.get("prerequisites") or []),
            mastery_criteria=list(c.get("mastery_criteria") or []),
            common_misconceptions=list(c.get("common_misconceptions") or []),
            docs=[str(d) for d in (c.get("docs") or [])],
        )
        for c in raw["concepts"]
    ]

    known_ids = {c.id for c in concepts}
    edges: dict[str, list[str]] = {}
    for c in concepts:
        if c.severity not in SEVERITIES:
            raise TaxonomyValidationError(
                f"{path}: concept '{c.id}' has unknown severity '{c.severity}' "
                f"(expected one of {SEVERITIES})"
            )
        unknown = [p for p in c.prerequisites if p not in known_ids]
        if unknown:
            raise TaxonomyValidationError(
                f"{path}: concept '{c.id}' references unknown prerequisite(s) {unknown} "
                "— prerequisites must resolve within the same stack file (cross-stack "
                "edges are not yet supported, see curriculum-engine-v1.md)"
            )
        edges[c.id] = c.prerequisites

    _check_for_cycle(known_ids, edges)

    return ParsedStackTaxonomy(stack=stack, stack_version=stack_version, concepts=concepts)


async def sync_concepts_for_stack(db: AsyncSession, parsed: ParsedStackTaxonomy) -> None:
    """Idempotent upsert of one stack's concepts + prerequisite edges —
    re-running the seed script converges rather than duplicating rows.

    Update-then-insert rather than a dialect-specific `ON CONFLICT`
    upsert, same reasoning as `projects.service.record_project_view`:
    this app's tests fall back to SQLite (see tests/conftest.py), and a
    plain UPDATE followed by a conditional INSERT is portable across
    both engines. Edges are delete-then-reinsert, mirroring the
    ingestion worker's `replace_document_chunks` idempotency pattern.
    """
    concept_ids = [c.id for c in parsed.concepts]

    for c in parsed.concepts:
        values = {
            "stack": parsed.stack,
            "stack_version": parsed.stack_version,
            "severity": c.severity,
            "mastery_criteria": c.mastery_criteria,
            "common_misconceptions": c.common_misconceptions,
            "docs": c.docs,
        }
        result = await db.execute(update(Concept).where(Concept.id == c.id).values(**values))
        if result.rowcount == 0:  # type: ignore[attr-defined]
            db.add(Concept(id=c.id, **values))

    await db.execute(
        delete(ConceptPrerequisite).where(ConceptPrerequisite.concept_id.in_(concept_ids))
    )
    for c in parsed.concepts:
        for prereq_id in c.prerequisites:
            db.add(ConceptPrerequisite(concept_id=c.id, prerequisite_id=prereq_id))

    await db.commit()


async def get_concepts_for_stack(
    db: AsyncSession, stack: str, stack_version: str
) -> list[Concept]:
    result = await db.execute(
        select(Concept).where(Concept.stack == stack, Concept.stack_version == stack_version)
    )
    concepts = list(result.scalars().all())
    if not concepts:
        raise StackNotFoundError(stack, stack_version)
    return concepts


async def get_prerequisite_edges(
    db: AsyncSession, concept_ids: list[str]
) -> dict[str, list[str]]:
    if not concept_ids:
        return {}
    result = await db.execute(
        select(ConceptPrerequisite).where(ConceptPrerequisite.concept_id.in_(concept_ids))
    )
    edges: dict[str, list[str]] = {cid: [] for cid in concept_ids}
    for edge in result.scalars().all():
        edges.setdefault(edge.concept_id, []).append(edge.prerequisite_id)
    return edges


async def list_stacks(db: AsyncSession) -> list[tuple[str, str, int]]:
    result = await db.execute(select(Concept.stack, Concept.stack_version, Concept.id))
    counts: dict[tuple[str, str], int] = {}
    for stack, stack_version, _id in result.all():
        counts[(stack, stack_version)] = counts.get((stack, stack_version), 0) + 1
    return [(stack, version, count) for (stack, version), count in sorted(counts.items())]


async def get_concept(db: AsyncSession, concept_id: str) -> Concept | None:
    return await db.get(Concept, concept_id)
