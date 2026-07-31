"""Curriculum Engine — deterministic sequencing.

Pure, DB-free functions with no I/O — the same "pure function, unit
tested in isolation" split the RAG engine established for
`reciprocal_rank_fusion`/`build_context`. This is the module's highest
quality-risk piece (ARCHITECTURE.md: "a confidently wrong roadmap is
worse than a tutorial"), so it never touches the LLM and never touches
the database directly — every input arrives as a plain dataclass/dict
and every output is a plain dataclass, which is what makes it possible
to unit test every branch (cycles, ties, dropped milestones) without a
running Postgres.

Three responsibilities, in order:
1. `topological_order` — turn the prerequisite DAG into one deterministic
   sequence (lesson ordering).
2. `select_concepts_for_level` — decide which of those concepts a given
   experience level actually needs (beginner/intermediate/advanced
   adaptation + prerequisite safety net).
3. `diff_milestones` — merge a freshly-selected concept set against an
   existing roadmap's milestones without disturbing progress
   (regeneration without losing progress).
"""

from dataclasses import dataclass

SEVERITY_RANK: dict[str, int] = {"foundational": 0, "intermediate": 1, "advanced": 2}

# The minimum severity a plain (non-prerequisite) concept must have to
# be included in a roadmap generated for this experience level. A
# concept below the floor is still included if something at/above the
# floor transitively requires it — see select_concepts_for_level.
SEVERITY_FLOOR: dict[str, str] = {
    "beginner": "foundational",
    "intermediate": "intermediate",
    "advanced": "advanced",
}

# Milestone statuses a learner has already engaged with — never removed
# or reordered by a regeneration, only ever added to or unlocked further.
_STARTED_STATUSES = frozenset({"in_progress", "completed"})


@dataclass(frozen=True)
class ConceptNode:
    """The minimal shape sequencing needs from a taxonomy Concept row —
    decoupled from the ORM model so this module never imports SQLAlchemy.
    """

    id: str
    severity: str


class CycleDetectedError(Exception):
    """Raised if `topological_order` is ever handed a graph with a
    cycle. This should be unreachable in practice — taxonomy.service's
    seed-time validation (`_check_for_cycle`) rejects cyclic YAML before
    it ever reaches a database row — but sequencing re-checks rather
    than trusting that invariant silently, since a confidently-wrong
    infinite/truncated roadmap is exactly the failure mode this module
    exists to prevent.
    """


def topological_order(concepts: list[ConceptNode], edges: dict[str, list[str]]) -> list[str]:
    """Kahn's algorithm over the prerequisite DAG (`edges[concept_id]` =
    list of prerequisite ids that must come first). Ties (multiple
    concepts simultaneously available) are broken deterministically by
    `(severity_rank, concept_id)` so the same input always produces the
    same output — required for regeneration to be a stable diff rather
    than a shuffle.
    """
    by_id = {c.id: c for c in concepts}
    in_degree: dict[str, int] = dict.fromkeys(by_id, 0)
    # dependents[p] = concepts that list p as a prerequisite — the
    # "what unlocks when p is done" adjacency, the direction Kahn's
    # algorithm actually walks.
    dependents: dict[str, list[str]] = {cid: [] for cid in by_id}

    for cid, prereqs in edges.items():
        if cid not in by_id:
            continue
        for p in prereqs:
            if p not in by_id:
                continue
            in_degree[cid] += 1
            dependents[p].append(cid)

    available = [cid for cid, deg in in_degree.items() if deg == 0]
    ordered: list[str] = []

    def sort_key(cid: str) -> tuple[int, str]:
        return (SEVERITY_RANK.get(by_id[cid].severity, 99), cid)

    while available:
        available.sort(key=sort_key)
        cid = available.pop(0)
        ordered.append(cid)
        for dependent in dependents[cid]:
            in_degree[dependent] -= 1
            if in_degree[dependent] == 0:
                available.append(dependent)

    if len(ordered) != len(by_id):
        remaining = set(by_id) - set(ordered)
        raise CycleDetectedError(f"Prerequisite cycle among: {sorted(remaining)}")

    return ordered


def _transitive_prerequisites(concept_id: str, edges: dict[str, list[str]]) -> set[str]:
    seen: set[str] = set()
    stack = list(edges.get(concept_id, []))
    while stack:
        p = stack.pop()
        if p in seen:
            continue
        seen.add(p)
        stack.extend(edges.get(p, []))
    return seen


def select_concepts_for_level(
    ordered_ids: list[str],
    concepts_by_id: dict[str, ConceptNode],
    edges: dict[str, list[str]],
    experience_level: str,
) -> list[str]:
    """Decides which concepts belong in the roadmap for a given
    experience level, preserving `ordered_ids`'s relative order.

    Two-part rule, deliberately simple and explainable (no LLM
    judgment involved):
    1. Include every concept at or above the level's severity floor.
    2. Also include any concept below the floor that is a *transitive
       prerequisite* of an included concept — an advanced learner still
       needs a foundational concept if something advanced strictly
       depends on it. This is the "prerequisite detection" safety net:
       adaptation decides what to skip, but a real dependency edge
       always wins over a skip.
    """
    floor = SEVERITY_FLOOR[experience_level]
    floor_rank = SEVERITY_RANK[floor]

    at_or_above_floor = {
        cid for cid in ordered_ids if SEVERITY_RANK.get(concepts_by_id[cid].severity, 99) >= floor_rank
    }

    required_prereqs: set[str] = set()
    for cid in at_or_above_floor:
        required_prereqs |= _transitive_prerequisites(cid, edges)

    selected = at_or_above_floor | required_prereqs
    return [cid for cid in ordered_ids if cid in selected]


@dataclass(frozen=True)
class ExistingMilestone:
    """The minimal shape sequencing needs from a Milestone row."""

    id: object  # uuid.UUID, kept as `object` so this module has no ORM/uuid coupling
    concept_id: str
    status: str


@dataclass(frozen=True)
class MilestonePlanEntry:
    """One row of the merge plan `service.py` applies: either "keep this
    existing milestone, just possibly move it" (`existing_id` set) or
    "create a new milestone for this concept" (`existing_id` is None).
    """

    concept_id: str
    existing_id: object | None


@dataclass(frozen=True)
class MilestonePlan:
    entries: list[MilestonePlanEntry]
    # Existing milestones dropped entirely (concept no longer selected,
    # and the learner never started it) — service.py deletes these.
    dropped_ids: list[object]


def diff_milestones(
    existing: list[ExistingMilestone], new_concept_ids: list[str]
) -> MilestonePlan:
    """The regenerate-without-losing-progress merge.

    - Milestones already `in_progress`/`completed` are never dropped and
      never reordered *relative to each other* — they act as anchors.
    - Milestones never started (`locked`/`available`) whose concept is
      no longer selected are dropped.
    - Concepts newly selected that don't already have a milestone become
      new entries, inserted at the position `new_concept_ids` (already
      topologically ordered) puts them in — anchors keep their relative
      order, everything else slots in around them.
    """
    existing_by_concept = {m.concept_id: m for m in existing}
    new_concept_set = set(new_concept_ids)

    anchors = {m.concept_id for m in existing if m.status in _STARTED_STATUSES}
    droppable = [
        m for m in existing if m.status not in _STARTED_STATUSES and m.concept_id not in new_concept_set
    ]

    # Final concept order = new_concept_ids, but any anchor concept that
    # fell out of new_concept_ids (e.g. a stack/level change that no
    # longer selects it) is still appended at its anchor's original
    # relative position — it's historical record, not a live suggestion,
    # so exact placement matters less than "it still exists at all".
    final_ids = list(new_concept_ids)
    for m in existing:
        if m.concept_id in anchors and m.concept_id not in new_concept_set:
            final_ids.append(m.concept_id)

    entries = [
        MilestonePlanEntry(
            concept_id=cid,
            existing_id=existing_by_concept[cid].id if cid in existing_by_concept else None,
        )
        for cid in final_ids
    ]

    return MilestonePlan(entries=entries, dropped_ids=[m.id for m in droppable])
