# Curriculum & Roadmap Generation Engine — V1

**Status:** Implemented — see `apps/api/app/modules/taxonomy/` (concept
graph: models, YAML loading/validation, reads) and
`apps/api/app/modules/curriculum/` (deterministic sequencing, roadmap/
milestone service, lazy per-milestone LLM narration). Builds on
`ARCHITECTURE.md` §3 ("Curriculum Engine" and "Taxonomy & Concept Graph
Service" responsibilities) and §7 (the `concepts`/`roadmaps`/`milestones`
schema, reserved but not built until this pass), and on
[`rag-engine-v1.md`](./rag-engine-v1.md) for the retrieval path milestone
narration optionally grounds itself in.

**Scope:** Converts a project's declared tech stack, the learner's
experience level, and (optionally) the project's own ingested
documentation into a structured roadmap: an ordered sequence of
milestones, one per concept, each capable of producing a narrated
lesson (explanation, exercises, quiz) and an estimated completion time.
Taxonomy content itself (which concepts exist, their prerequisites) is
curated YAML — this pass does **not** build a taxonomy-authoring UI or
an LLM-driven taxonomy generator; see Section 13 for why that's
deliberate. Progress tracking in this pass is roadmap-local (milestone
status); a cross-project `user_concept_mastery` profile is explicitly
deferred to the future Progress & Weakness Tracking module (Section 13).

---

## 1. Backend architecture

```mermaid
flowchart TB
    subgraph Data-Curated["Curated content (checked into the repo)"]
        YAML["packages/taxonomy-data/concepts/*.yaml"]
    end

    subgraph Seed["apps/api/scripts"]
        SEED["seed_taxonomy.py"]
    end

    subgraph Taxonomy["apps/api/app/modules/taxonomy"]
        TSERVICE["service.py\nload_concepts_from_yaml\nsync_concepts_for_stack\nget_concepts_for_stack"]
        TROUTER["router.py\nGET /v1/taxonomy/stacks(/{stack}/concepts)"]
    end

    subgraph Curriculum["apps/api/app/modules/curriculum"]
        CROUTER["router.py\n/v1/projects/{project_id}/roadmap"]
        CSERVICE["service.py"]
        SEQ["sequencing.py\ntopological_order\nselect_concepts_for_level\ndiff_milestones"]
        CB["content_builder.py\n+ prompt_templates.py"]
    end

    subgraph Know["knowledge/retrieval (rag-engine-v1.md)"]
        RETRIEVE["retrieve_chunks (keyword mode)"]
        CTX["context_builder.build_context"]
    end

    subgraph Data[("Postgres")]
        CONCEPTS[("concepts\nconcept_prerequisites")]
        ROADMAPS[("roadmaps\nmilestones")]
    end

    GATEWAY["llm_gateway/gateway.py\n.generate()"]

    YAML --> SEED --> TSERVICE --> CONCEPTS
    TROUTER --> TSERVICE
    CROUTER --> CSERVICE
    CSERVICE --> SEQ
    CSERVICE --> TSERVICE
    CSERVICE --> ROADMAPS
    CSERVICE --> CB
    CB --> RETRIEVE --> CTX
    CSERVICE --> GATEWAY
```

**Two modules, deliberately split, mirroring `ARCHITECTURE.md`'s own
module boundary (§2):**
- **`taxonomy/`** is the system of record for canonical concepts and
  their prerequisites — read-only at request time, written only by
  `scripts/seed_taxonomy.py` against curated YAML. It has no notion of
  a project, a learner, or a roadmap.
- **`curriculum/`** owns everything project/learner-facing: the
  deterministic sequencing algorithm, the `Roadmap`/`Milestone` rows,
  and the lazy narration step. It reads `taxonomy` the same way it reads
  `knowledge` (a dependency, not an owner).

**`sequencing.py` and `content_builder.py` are pure, DB-free functions**
— no SQLAlchemy, no LLM gateway, no I/O of any kind — the same "pure
function, unit tested in isolation" split `rag-engine-v1.md` established
for `reciprocal_rank_fusion`/`build_context`. `service.py` is the only
place that wires them together with a real DB session and the LLM
gateway. This matters more here than almost anywhere else in the
codebase: sequencing is the one piece `ARCHITECTURE.md` calls out as the
"single biggest quality-gate risk" (a confidently wrong roadmap is worse
than a tutorial), so it needs to be exhaustively testable without a
running Postgres or Ollama instance.

---

## 2. Database schema

Two migrations, chained after the RAG engine's:
`202607302000_add_taxonomy_tables.py` and
`202607302100_add_curriculum_engine_tables.py`.

**Taxonomy:**
- **`concepts`** — natural string primary key (e.g. `python.async_await`),
  not a surrogate UUID: the curated YAML already declares ids as
  globally unique and append-only (see
  `packages/taxonomy-data/concepts/example-python-basics.yaml`'s header
  comment), so a surrogate id would just be a second identity for the
  same append-only string. Columns: `stack`, `stack_version`, `severity`
  (`CheckConstraint` — `foundational`/`intermediate`/`advanced`, never a
  native enum, matching `database-schema-v1.md`'s established
  "why TEXT not native ENUM" rule), `mastery_criteria`/
  `common_misconceptions`/`docs` (JSONB lists). No soft delete — concepts
  are append-only by convention, never deleted.
- **`concept_prerequisites`** — the self-referencing edge table
  `ARCHITECTURE.md` §7 calls for: `(concept_id, prerequisite_id)`
  composite primary key, both FKs to `concepts.id` with `ondelete="CASCADE"`.

**Curriculum:**
- **`roadmaps`** — one row per project (`project_id` unique FK):
  regeneration mutates this row in place rather than creating a new one,
  which is what makes "one roadmap per project" a schema-enforced
  invariant rather than an application convention. `version` increments
  on every regeneration (a change-detection signal for the client, never
  read by any query). `estimated_total_minutes` is a denormalized sum,
  recomputed on every generate/regenerate.
- **`milestones`** — one row per selected concept per roadmap.
  `UniqueConstraint(roadmap_id, concept_id)` is the **structural**
  duplicate-lesson guard (Section 6). `concept_id` is a FK to
  `concepts.id` with `ondelete="RESTRICT"` — a concept can never be
  deleted out from under a milestone that references it, unlike every
  other FK in this schema, which cascades. `lesson_content` (nullable
  JSONB) holds the narrated `{explanation, key_points, exercises, quiz}`
  once generated; `content_version` bumps each time it's regenerated.
  `status` (`locked`/`available`/`in_progress`/`completed`) is the
  roadmap-local progress signal (Section 8).

---

## 3. AI workflow

Two independent LLM touchpoints, at opposite ends of the cost/latency
spectrum:

1. **Roadmap generation has zero LLM calls.** `generate_or_regenerate_roadmap`
   is pure graph traversal (Section 4) over already-curated data. This
   directly operationalizes `ARCHITECTURE.md`'s governing principle:
   *"structure what can be structured; let the LLM interpret or narrate
   within that structure — never let it freely invent, judge, or sequence
   from scratch."* The LLM never decides what to teach or in what order.
2. **Milestone narration is one LLM call, lazy and per-milestone.**
   `generate_milestone_content` is only ever triggered by an explicit
   `POST .../milestones/{id}/content` — never automatically as part of
   roadmap generation. Given a milestone, it:
   - loads the concept's curated metadata (severity, mastery criteria,
     common misconceptions) from `taxonomy`;
   - best-effort retrieves the project's own ingested documentation via
     `knowledge.retrieval.rag_service.retrieve_chunks` (keyword mode —
     see Section 4's note on why, in `service.py`'s
     `_gather_context_text`) and folds it into the prompt via the RAG
     engine's own `context_builder.build_context`, so exercises can
     reference the learner's actual project docs when there are any;
   - builds a single prompt (`content_builder.build_milestone_prompt` +
     `prompt_templates.py`) instructing the model to *narrate only* —
     explain the given concept, adapt tone/depth to the given experience
     level, and return strict JSON;
   - parses and validates the response (`content_builder.parse_milestone_content`)
     against the `LessonContent` Pydantic schema, retrying once with a
     stricter reminder on invalid JSON before raising `ContentGenerationError`
     (Section 11) — the same "structure enforced by the caller, not
     trusted from the model" posture the LLM Gateway's design calls for.

Why lazy, not eager: generating narration for every milestone the moment
a roadmap is created would mean paying LLM cost/latency for lessons a
learner may never reach (or reach much later, once the concept's
curated metadata may have been revised). Lazy generation also means
regenerating a roadmap (Section 7) never has to decide what to do with
stale narration for milestones that moved or were dropped — narration is
keyed to a `Milestone` row's lifetime, not regenerated speculatively.

---

## 4. Lesson ordering — deterministic sequencing

`sequencing.topological_order` runs Kahn's algorithm over the
prerequisite DAG (`concept_prerequisites`, loaded per-stack by
`taxonomy.service.get_prerequisite_edges`): concepts with no
outstanding prerequisites become "available" first; completing one
(conceptually — this is graph traversal, not roadmap state) unlocks
its dependents. Ties (multiple concepts simultaneously eligible) are
broken deterministically by `(severity_rank, concept_id)` — foundational
before intermediate before advanced, then alphabetically — so the exact
same curated content always produces the exact same order. This
determinism is not cosmetic: it's what makes regeneration a stable diff
(Section 7) rather than a shuffle, and what makes the algorithm testable
at all (`tests/test_sequencing.py::TestTopologicalOrder`).

A cycle in the prerequisite graph raises `CycleDetectedError` — in
practice unreachable through the API, because `taxonomy.service`'s
seed-time validation (`_check_for_cycle`, run when `scripts/seed_taxonomy.py`
loads a YAML file) already rejects cyclic curated content before it
ever becomes a database row. `sequencing.py` re-checks anyway rather
than trusting that invariant silently, on the theory that a confidently
wrong (or infinitely looping) roadmap is exactly the failure mode this
whole module exists to prevent.

---

## 5. Prerequisite detection

Prerequisites are never inferred — they're **curated edges**, authored
by hand in `packages/taxonomy-data/concepts/*.yaml` (`prerequisites:` per
concept) and loaded into `concept_prerequisites` by
`scripts/seed_taxonomy.py`. Validation happens once, at seed time, in
`taxonomy.service.load_concepts_from_yaml`:
- every `prerequisites` entry must resolve to a concept id declared in
  the **same file** (cross-stack prerequisite edges are an explicit,
  documented deferral — see Section 13, not a half-built feature);
- the resulting graph must be acyclic (Section 4's `_check_for_cycle`,
  duplicated intentionally rather than imported from `curriculum.sequencing`,
  since taxonomy validation and curriculum sequencing are different
  concerns that happen to both need cycle detection — see
  `taxonomy/service.py`'s docstring for why importing across that
  boundary would invert it).

This closed-set, curated-edge approach is the same trade-off
`ARCHITECTURE.md`'s Key Trade-offs table makes for the concept taxonomy
itself ("closed-set concept taxonomy" over "freeform LLM-invented
weakness labels") applied one level deeper: prerequisites are as much a
part of the curated taxonomy as the concepts themselves, and get the
same "the LLM never modifies it directly" protection.

---

## 6. Beginner / intermediate / advanced adaptation

Two independent mechanisms handle two different jobs:

1. **What to include** — `sequencing.select_concepts_for_level`.
   Each experience level has a severity floor
   (`SEVERITY_FLOOR = {"beginner": "foundational", "intermediate":
   "intermediate", "advanced": "advanced"}`). A concept is selected if
   its own severity is at or above the learner's floor, **or** — the
   safety net — it's a *transitive prerequisite* of a concept that is.
   An advanced learner skips foundational filler, but if an advanced
   concept genuinely depends on a foundational one, that foundational
   concept is still included: adaptation decides what's optional, a real
   prerequisite edge always wins over a skip. See
   `tests/test_sequencing.py::TestSelectConceptsForLevel` for the exact
   branching case this covers (a concept skippable on its own, versus
   one pulled back in because something selected needs it).
2. **How to explain it** — `content_builder.build_milestone_prompt` +
   `prompt_templates.MILESTONE_SYSTEM_PROMPT`. The narration prompt
   passes `experience_level` straight to the model with explicit
   per-level instructions (beginner: first principles, no unexplained
   jargon; intermediate: assume the basics, focus on nuance and common
   mistakes; advanced: concise, focus on edge cases and trade-offs).
   This is deliberately **not** encoded as structure — tone and depth of
   *explanation* is exactly the kind of thing `ARCHITECTURE.md` says to
   let the LLM interpret, as long as it's narrating a concept sequencing
   already chose.

---

## 7. Regeneration without losing progress

`sequencing.diff_milestones` is the merge algorithm behind "regenerate
this roadmap" (e.g. the learner changes their declared stack version,
or new concepts get added to the curated taxonomy). Given the roadmap's
existing milestones and a freshly computed concept selection:

- Milestones already `in_progress` or `completed` are **anchors** —
  never dropped, never reordered relative to each other, regardless of
  whether their concept is still selected by the new run. They're
  historical record of what the learner actually did, not a live
  suggestion.
- Milestones never started (`locked`/`available`) whose concept is no
  longer selected are dropped — they were never shown to the learner as
  real progress, so there's nothing to preserve.
- Newly selected concepts without an existing milestone become new
  entries, slotted into the fresh topological order.
- The final order is the new topological order, with any anchor whose
  concept fell out of the new selection appended at the end (kept as a
  record, not resequenced into a live position that no longer means
  anything).

`service.py`'s `generate_or_regenerate_roadmap` applies this plan by
**bulk-replacing** the ORM-level `roadmap.milestones` collection with
exactly the kept-and-new set, in final order, and relies on the
`cascade="all, delete-orphan"` relationship (`curriculum/models.py`) to
delete whatever fell out — a milestone id, its `status`, and its
`lesson_content` are only ever touched by explicitly reassigning
`sequence_index`; nothing else about a kept milestone is rewritten by a
regeneration. (An earlier version of this function issued a raw Core
`DELETE` for dropped rows instead of mutating the collection; it left
the already-loaded `roadmap.milestones` Python list stale in the
session's identity map, so a later re-fetch kept returning "deleted"
milestones — fixed by using the ORM's own cascade, which correctly
invalidates the in-memory collection. See `tests/test_curriculum_service.py::TestRegenerateWithoutLosingProgress`
for the regression test.)

Completing a milestone also unlocks the next one
(`service.update_milestone_status`, sequential unlock — see Section 8),
so "locked" is a live, recomputed signal on every regeneration
(`_recompute_unlocks`), not a status frozen at creation time.

---

## 8. Avoiding duplicate lessons

Two layers, structural first, content-level second:

1. **Structural — `UniqueConstraint(roadmap_id, concept_id)`** on
   `milestones`. A concept can appear at most once per roadmap by
   database constraint, not by application convention. Combined with
   `diff_milestones` keying every merge decision on `concept_id`, a
   roadmap can never accumulate two milestones for the same concept
   across any number of regenerations.
2. **Content-level — exact-match dedup within one milestone's generated
   material.** `content_builder.parse_milestone_content` drops exercises
   or quiz questions that normalize (lowercased, whitespace-collapsed)
   to the same text as one already kept. LLM narration occasionally
   produces near-duplicate exercises; dropping the duplicate is treated
   as a non-error (a milestone with three good exercises instead of four
   isn't a failure worth surfacing), unlike a genuinely malformed
   response (Section 11).

---

## 9. Milestone status / progress model

`locked → available → in_progress → completed`, sequential and
roadmap-local. `_ALLOWED_TRANSITIONS` in `curriculum/service.py`
permits only `available → in_progress` and `in_progress → completed` as
client-driven transitions (`PATCH .../milestones/{id}`); `locked` and
`available` are server-computed and never client-settable —
`_recompute_unlocks` runs after every generation/regeneration, and
completing a milestone directly unlocks the next `locked` one in
sequence. This is intentionally simpler than a full mastery model: there
is no cross-project skill transfer in this pass (see Section 13) — a
learner's status on `python.async_await` in one project has no bearing
on a roadmap generated for a different project, which is a real,
documented gap relative to `ARCHITECTURE.md` §7's eventual
`user_concept_mastery` design, not an oversight.

---

## 10. APIs

Taxonomy (read-only, `/v1/taxonomy`):

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/stacks` | Every curated `(stack, stack_version)` pair, with concept counts. |
| `GET` | `/stacks/{stack}/concepts` | Every concept for a stack + version, with its prerequisites. |

Curriculum, nested under the owning project (`/v1/projects/{project_id}/roadmap`,
same `get_owned_project` 404-not-403 ownership enforcement every other
project-scoped route uses):

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/generate` | Generate or regenerate the roadmap. No LLM call (Section 3). |
| `GET` | `` | Current roadmap + milestone summaries. |
| `GET` | `/milestones/{id}` | One milestone's detail, including `lesson_content` if generated. |
| `POST` | `/milestones/{id}/content` | Lazily (re)generate that milestone's narration via the LLM Gateway. |
| `PATCH` | `/milestones/{id}` | Learner-driven status transition (`in_progress`/`completed`). |

---

## 11. Error handling

Two exception hierarchies, one per module, following the established
`XxxError` base + `_STATUS_CODES` dict + `register_xxx_exception_handlers`
pattern (`knowledge/exceptions.py`):

- **`taxonomy.exceptions.TaxonomyError`** — `StackNotFoundError` (404,
  no curated taxonomy for the requested stack/version — the "stack tier"
  equivalent of a 🔴 unsupported stack, rather than fabricating a
  taxonomy on the fly) and `TaxonomyValidationError` (500, seed-time
  only — never triggered by a request, since a request only ever reads
  already-validated rows).
- **`curriculum.exceptions.CurriculumError`** — `RoadmapNotFoundError` /
  `MilestoneNotFoundError` (404), `InvalidMilestoneTransitionError` (409
  — e.g. completing a locked milestone), `ContentGenerationError` (503 —
  the LLM Gateway failed outright, or returned unparseable narration
  twice in a row; distinct from every other error here because it means
  the *narration step* is unavailable, not that the request was
  invalid, mirroring `RetrievalServiceUnavailableError`'s role in the
  RAG engine).

---

## 12. Tests

- **Pure logic, no DB/LLM:** `tests/test_sequencing.py` (topological
  order determinism and cycle rejection, severity-floor selection with
  the prerequisite safety net, the full diff/merge matrix — completed
  milestones preserved, never-started ones dropped, new concepts
  inserted) and `tests/test_content_builder.py` (prompt assembly, JSON
  parsing/validation, code-fence stripping, exercise/quiz dedup).
- **Taxonomy integration:** `tests/test_taxonomy_service.py` — YAML
  parsing against the real curated `example-python-basics.yaml`, plus
  synthetic fixtures for the failure paths (dangling prerequisite
  reference, cycle, unknown severity), and sync idempotency.
- **Curriculum integration:** `tests/test_curriculum_service.py` calls
  `service.py` functions directly against `db_session` (no HTTP layer):
  full generate → complete a milestone → add a new concept → regenerate
  → assert the completed milestone kept its id/status and the new
  concept was added; milestone status transition rules; lazy content
  generation including the retry-once-then-raise path, against a
  `FakeLLMGateway` (same pattern as `test_rag_service.py`).
- **Router:** `tests/test_curriculum_router.py` — thin HTTP-layer checks
  (auth, project-ownership 404-not-403, status codes for the unsupported-
  stack and invalid-transition cases), seeding concepts directly via
  `tests/taxonomy_fixtures.py` since there's no HTTP endpoint that
  creates them (curated content is seeded out-of-band, Section 3).

A genuine bug was caught by this test suite during development:
`generate_or_regenerate_roadmap` originally deleted dropped milestones
via a raw Core `DELETE` statement while leaving the ORM-level
`roadmap.milestones` Python collection untouched. The delete took effect
in the database, but the already-loaded collection stayed stale in the
session's identity map, so the function's own final re-fetch
(`get_roadmap`, using `selectinload`) kept returning the "deleted"
milestones — SQLAlchemy doesn't re-populate an already-loaded
relationship collection just because the underlying rows changed via a
Core statement. Fixed by bulk-replacing the collection instead (Section
7), letting the ORM's own `delete-orphan` cascade handle removal, which
also correctly invalidates the in-memory state.

---

## 13. Explicitly deferred / Future Scalability

- **Cross-project mastery (`user_concept_mastery`).** This pass adapts
  purely on `experience_level` and roadmap-local milestone status
  (Section 9). The real trigger for building `ARCHITECTURE.md` §7's
  user-scoped mastery profile is the Progress & Weakness Tracking module
  actually shipping — until then, "skip already-mastered concepts"
  means "skip concepts below this project's declared experience floor,"
  not "skip concepts this learner has already demonstrated mastery of
  elsewhere."
- **Cross-stack prerequisite edges.** `taxonomy.service.load_concepts_from_yaml`
  only resolves `prerequisites` within the same curated file (Section
  5). A FastAPI concept that genuinely depends on a Python fundamental
  has no way to express that yet. Worth building once a second stack's
  curated content actually needs it, rather than guessing the right
  cross-file resolution/versioning story in advance.
- **Eager or background content pre-generation.** Narration is
  lazy and synchronous within the request (Section 3). If narration
  latency becomes a visible UX problem, the natural next step is
  enqueuing it on a background worker (the same `arq` queue the
  ingestion engine already uses) the moment a milestone becomes
  `available`, not necessarily making it eager for the whole roadmap.
- **Hybrid/vector retrieval for narration grounding.** `_gather_context_text`
  uses keyword search only (Section 3) — narration's query is the
  concept's own name, not a nuanced user question, so hybrid search's
  extra embed call wasn't judged worth it yet. Revisit if narration
  quality turns out to depend on better-grounded retrieval once there's
  real usage to measure against.
- **Automated taxonomy authoring / benchmark-driven curation.** Matches
  `ARCHITECTURE.md`'s own deferral for the Stack Support Tier Manager
  ("once there are enough curated stacks that manual curation is
  visibly the bottleneck, not before") — concept authoring stays a
  human, reviewed process for the same reason freeform LLM roadmap
  generation was rejected in Sprint 0.
- **Content-generation cost accounting.** `generate_milestone_content`
  doesn't yet report its operation cost to a usage ledger — the Cost &
  Abuse Control module (`ARCHITECTURE.md` §3) is still a stub; wiring
  `"milestone_narration"` into a real per-user budget is additive once
  that module exists, not a redesign of this one.
