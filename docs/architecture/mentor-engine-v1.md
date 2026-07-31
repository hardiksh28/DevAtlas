# Mentoring Engine — V1

**Status:** Implemented — see `apps/api/app/modules/mentoring/`
(models, prompt architecture, service, router). Builds on
`ARCHITECTURE.md` §3 ("Mentoring / Hint Ladder Engine"), and reuses
[`curriculum-engine-v1.md`](./curriculum-engine-v1.md)'s
`Roadmap.experience_level` (adaptive tutoring) and
[`rag-engine-v1.md`](./rag-engine-v1.md)'s retrieval path (optional
grounding in the project's own docs).

**Scope:** A persistent, per-project mentor conversation that explains
concepts, asks guiding questions, gives hints instead of answers,
detects misconceptions, remembers prior turns, and adapts to the
learner's declared experience level. **Not** in this pass: the formal
Effort-Evidence-gated hint-ladder rung state machine `ARCHITECTURE.md`
§3 describes (`explain → question → hint → doc pointer → attempt
review → reveal`, each transition gated by a separate Effort & Evidence
Evaluator reading structured signals). That evaluator is still an
unbuilt stub module and wasn't part of this step's actual requirements
— building it now would be inventing scope, not meeting it. This pass
is the conversational memory/prompting substrate that module would sit
on top of; "hints instead of answers" is enforced here as a
prompt/response contract (Section 2), not a rung you can be denied
advancement past. See Section 7 for the exact trigger to revisit this.

---

## 1. Backend architecture

```mermaid
flowchart TB
    subgraph API["apps/api/app/modules/mentoring"]
        ROUTER["router.py\nPOST/GET /v1/projects/{id}/mentor/messages"]
        SERVICE["service.py"]
        PB["prompt_builder.py\n+ prompt_templates.py"]
        CB["content_builder.py\nparse_mentor_reply"]
    end

    subgraph Curriculum["curriculum (Step 7)"]
        ROADMAP["service.get_roadmap\n.experience_level"]
        TAX["taxonomy.service.get_concept\nmastery_criteria / misconceptions"]
    end

    subgraph Know["knowledge/retrieval (rag-engine-v1.md)"]
        RETRIEVE["retrieve_chunks (keyword mode)"]
        CTX["context_builder.build_context"]
    end

    subgraph Data[("Postgres")]
        CONV[("conversations\nmessages")]
    end

    GATEWAY["llm_gateway/gateway.py\n.generate()"]

    ROUTER --> SERVICE
    SERVICE --> ROADMAP
    SERVICE --> TAX
    SERVICE --> RETRIEVE --> CTX
    SERVICE --> PB --> GATEWAY
    SERVICE --> CB
    SERVICE --> CONV
```

**One module, not two.** Unlike Curriculum/Taxonomy, there's no
separate "memory service" — `Conversation`/`Message` are owned directly
by `mentoring/models.py`, because conversation storage has no life
independent of the mentor that produces it (unlike the concept graph,
which several future modules will read). `prompt_builder.py` and
`content_builder.py` are pure, DB-free functions, the same split
`curriculum/` and `knowledge/retrieval/` already established — only
`service.py` wires them to a real DB session and the LLM gateway.

---

## 2. Database schema

One migration: `202607302200_add_mentoring_tables.py`.

- **`conversations`** — one row per project (`project_id` unique FK,
  same "one thread per project" pattern as `Roadmap`). `summary`
  (nullable text) and `summarized_up_to` (nullable timestamp) are the
  entire memory-compaction story — see Section 3.
- **`messages`** — append-only transcript (no soft delete, no edit;
  same "historical record" reasoning as `evidence_log`,
  `ARCHITECTURE.md` §7). `role` (`user`/`assistant`, `CheckConstraint`,
  never a native enum). `milestone_id` (nullable FK to
  `curriculum.milestones`, `ondelete="SET NULL"`) optionally anchors one
  turn to the concept being discussed — a conversation is not required
  to be milestone-scoped, but a single message can be, which is what
  lets misconception detection ground itself in curated data (Section
  4) without forcing every mentor interaction through the curriculum
  flow first. `detected_misconceptions` (JSONB list, assistant messages
  only) is the model's own tagging of that turn — see Section 4.

---

## 3. Memory strategy

**Sliding window + rolling summary, not a vector-embedded long-term
memory store.** A conversation's context need — "what have we already
covered in this thread" — is small, strictly sequential, and exactly
known; it is not a retrieval problem the way a large document corpus is.
This is the same "structured state vs. retrieval" distinction
`ARCHITECTURE.md` §3 draws for the Knowledge System (live project state
fetched directly, never embedded, "because it's small, exact, and
known") applied one level down, to conversation history instead of
project metadata.

Concretely:
- Every message is stored, forever, in `messages` — nothing is ever
  deleted or edited. The transcript itself is the ground truth.
- `Conversation.summary` covers everything **before**
  `summarized_up_to`; every message **after** that checkpoint is used
  verbatim. Prompt assembly (`service._recent_turns`) is: `summary` (if
  any) + the last `mentor_recent_message_limit` (default 20)
  uncompacted messages, by plain count.
- When the uncompacted tail exceeds `mentor_summary_trigger_messages`
  (default 20), `service._maybe_compact_history` makes one extra LLM
  call (`gateway.generate("mentor_summarize", ...)`) to fold everything
  except the last 4 turns into `summary`, and advances
  `summarized_up_to` to the last folded message's timestamp. The last 4
  turns are never summarized away, so a follow-up question always has
  its immediately preceding exchange available verbatim, not
  paraphrased.
- Compaction is **best-effort**: a failed summarization call is logged
  and skipped (`except Exception` there is deliberately swallowed, not
  re-raised — `# noqa: BLE001` marks the one place in this codebase that
  does that on purpose). A skipped compaction just means the next call
  carries a slightly longer uncompacted tail; it never breaks the
  conversation.

`# ponytail: context window management caps by plain message count, not
a token budget — conversation turns are short relative to a RAG
document chunk, so a count cap is the honestly-sized V1 version. Add a
token-aware version (mirroring context_builder.build_context's
token-budget packing) once conversations with large code pastes make a
count cap measurably wrong.`

---

## 4. Prompt engineering

`prompt_templates.py`'s `MENTOR_SYSTEM_PROMPT` encodes the entire
behavioral contract as ranked instructions, in this priority order:
explain the concept first, prefer a guiding question over a stated
conclusion, hint rather than solve (full reveal only on explicit
request, and even then with reasoning attached, never bare code), name
and correct a revealed misconception rather than staying gentle about
it, adapt tone/depth to the given experience level, and ground every
claim in the information actually provided — never invent facts about
the learner's own codebase.

**Structured output**, the same pattern `curriculum/content_builder.py`
established: the model must respond with exactly one JSON object,
`{"reply": str, "misconceptions_detected": [str]}`, parsed and validated
(`content_builder.parse_mentor_reply`) before anything is persisted or
returned. One retry with a stricter reminder
(`MENTOR_REPLY_RETRY_REMINDER`) on invalid JSON, then
`MentorReplyGenerationError` (503) — mirrors curriculum's
retry-once-then-fail shape exactly.

**Why "hints, not answers" is prompt-level, not a gate:** the full
architecture's hint ladder derives its actual security property from
the Effort Evaluator reading *structured evidence*, not conversation
text — `ARCHITECTURE.md` §3: "a user cannot argue their way past the
gate by wording a chat message persuasively, because the gate doesn't
read the chat message directly." That property doesn't exist yet in
this pass; a sufficiently insistent learner probably can talk the model
into revealing more than intended, the same way any single-prompt LLM
behavior contract can be pushed on. Building the actual gate (structured
signals, a state machine, a resistant boundary) is real, separate work
tracked in Section 7 — this pass is honest about not having it yet
rather than pretending a system prompt instruction is an enforcement
mechanism.

---

## 5. Hallucination prevention

Three mechanisms, layered:

1. **Explicit grounding instruction** in the system prompt — never
   invent facts about the learner's codebase or an API not shown.
2. **Optional RAG context** — `service._gather_retrieved_context` reuses
   `knowledge.retrieval.rag_service.retrieve_chunks` (keyword mode, same
   choice and reasoning as `curriculum.service._gather_context_text`:
   the query here is a short excerpt of the learner's own message, not a
   nuanced question worth an extra embed call) so the mentor can
   reference the project's own ingested documentation when there is
   any, rather than guessing at project-specific details.
3. **Misconception detection anchored to curated ground truth, when
   possible.** When a message is milestone-scoped,
   `service._resolve_concept_context` includes that concept's curated
   `common_misconceptions` (`taxonomy.Concept`, authored content, Step
   7) directly in the prompt — the model is asked to match against a
   known list first, not invent a label. Unanchored messages (no
   `milestone_id`) still get free-text misconception detection, which is
   necessarily less grounded; this is a real, accepted trade-off for
   conversations that aren't tied to a specific concept yet.

What this does **not** do, matching `rag-engine-v1.md`'s own
acknowledged gap: no automated post-hoc verification that a reply's
claims are actually grounded in what was provided. Same deferred-work
shape as that document's Section 13.

---

## 6. Context window management

Handled entirely by the memory strategy (Section 3): `summary` +
last-N-by-count messages, assembled once per `send_message` call in
`prompt_builder.build_mentor_prompt`. No token-budget accounting exists
yet for conversation turns (unlike `knowledge.retrieval.context_builder`,
which does token-budget RAG chunks) — see Section 3's `ponytail` note
for the exact trigger to add one.

---

## 7. Adaptive tutoring strategy

Reuses `curriculum.service.get_roadmap(db, project_id).experience_level`
directly — not a second, competing preference store. If the project has
no roadmap yet (`RoadmapNotFoundError`), the mentor defaults to
`"intermediate"` rather than failing; the mentor must be usable before a
learner has generated a roadmap. Adaptation happens entirely through the
prompt (Section 4's system prompt explicitly branches tone/depth by
level) — there is no separate code path per experience level, keeping
"what to say" (curriculum's job) and "how to say it" (the mentor's job)
cleanly split, the same two-mechanism division `curriculum-engine-v1.md`
Section 6 describes for its own beginner/intermediate/advanced handling.

---

## 8. APIs

Nested under the owning project (`/v1/projects/{project_id}/mentor`),
same `get_owned_project` 404-not-403 enforcement as every other
project-scoped route:

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/messages` | Send a message, get the mentor's reply. Creates the conversation lazily. |
| `GET` | `/messages` | Paginated conversation history (never creates a conversation as a read side-effect). |

`SendMessageRequest` accepts `content` and an optional `milestone_id` to
anchor the turn to a specific concept.

---

## 9. Error handling

`mentoring.exceptions.MentoringError` base; one subclass,
`MentorReplyGenerationError` (503) — raised when the LLM Gateway fails
outright, or returns unparseable JSON twice in a row. Mirrors
`curriculum.exceptions.ContentGenerationError` exactly: distinct from a
validation error because it means the *generation step* is unavailable,
not that the request was invalid. Blank/oversized message content is
caught by `SendMessageRequest`'s Pydantic validation before it ever
reaches `service.py`.

---

## 10. Tests

- **Pure logic, no DB/LLM:** `tests/test_mentor_content_builder.py` —
  prompt assembly (experience level, concept context, retrieved
  context, summary, and history all appear where expected), JSON
  parse/validate, code-fence stripping, invalid-JSON and missing-field
  error paths.
- **Service integration:** `tests/test_mentoring_service.py`, against
  `db_session` with a `FakeLLMGateway` (same pattern as
  `test_rag_service.py`/`test_curriculum_service.py`) — conversation and
  both messages created on send; experience level resolved from an
  existing roadmap and defaulted sanely without one; milestone-scoped
  sends include curated misconceptions in the prompt; detected
  misconceptions are stored; retry-then-`MentorReplyGenerationError` on
  repeated bad JSON; gateway failure translates to the same error;
  history compaction fires once the uncompacted tail exceeds the
  threshold (summary set, checkpoint advanced, no messages deleted) and
  stays quiet below it; pagination and the empty-conversation case for
  `list_messages`.
- **Router:** `tests/test_mentoring_router.py` — empty history before
  any message, blank-content 422, project-ownership 404-not-403.

---

## Explicitly deferred / Future Scalability

- **The formal Effort-Evidence-gated hint-ladder rung state machine**
  (`ARCHITECTURE.md` §3's full Mentoring Engine design). Trigger: the
  Effort & Evidence Evaluator module actually gets built. Until then,
  "hints not answers" is a prompt contract (Section 4), not an
  enforced gate — this is the single most important gap this document
  names explicitly rather than hides.
- **Token-budget-aware context window management** (Section 3/6) —
  once large code pastes in conversation make a plain message-count cap
  measurably wrong.
- **Hybrid/vector retrieval for mentor grounding** (Section 5) — same
  deferral and reasoning as curriculum's narration step; revisit
  together if ever revisited.
- **Cross-conversation / cross-project mentor memory.** Every
  conversation is scoped to one project, matching `Roadmap`'s own
  project-scoping. A learner's mentor history doesn't yet follow them
  across projects the way `user_concept_mastery` eventually will
  (`ARCHITECTURE.md` §7) — same explicit gap `curriculum-engine-v1.md`
  names for roadmap progress.
- **Automated post-hoc groundedness verification** (Section 5) — same
  deferred shape as `rag-engine-v1.md` Section 13.
