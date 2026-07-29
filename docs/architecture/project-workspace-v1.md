# Project Workspace — V1

**Status:** Implemented (see `apps/api/app/modules/projects/` and `apps/web/src/{app,components,hooks,lib}`).
Extends [`database-schema-v1.md`](./database-schema-v1.md) (which drafted a
minimal `projects` shell table but explicitly deferred settings, recency,
and soft delete) and [`ARCHITECTURE.md`](./ARCHITECTURE.md) Section 7's
data model. Depends on `auth-api-v1.md` for `get_current_user` — every
route here requires an authenticated caller.

**Scope:** `projects`, `project_settings`, `recent_projects` — the shell a
learner's actual project (roadmap, milestones, reviews) will attach to.
Curriculum/taxonomy/review tables from `ARCHITECTURE.md` Section 7 are
still out of scope; this pass only builds the workspace shell they'll
hang off of.

---

## 1. Why this shape (read before the schema)

`database-schema-v1.md` already decided the one thing that matters most:
**`projects` is a plain owned resource, single-owner, soft-deletable** —
matching the doc's own "team/collaboration is a later phase" scoping. Everything
below is that decision worked all the way through to a dashboard.

Three tables, not one wide `projects` table with a dozen nullable columns,
for the same reason `users` / `user_preferences` are already split that way:

| Table | Answers | Changes... | Read on... |
|---|---|---|---|
| `projects` | *What is this, who owns it, is it alive?* | Rarely (create, rename, archive, delete) | Every request that touches the project at all |
| `project_settings` | *How should it look/behave?* | Occasionally (settings page) | Every project-card render, workspace shell render |
| `recent_projects` | *When did this user last look at it?* | On (almost) every project open | Dashboard load only |

Collapsing these would mean either the identity row grows a write on every
single project view (`recent_projects`' job) or the settings blob is dragged
along on every list-projects query even though a project list card doesn't
need it. Splitting costs one extra join; keeping it flat costs a hot-row
problem on the one row that matters most.

**Why `recent_projects` is its own table and not just `projects.last_opened_at`:**
V1 has exactly one owner per project, so this looks redundant today — but
"who last looked at this" and "when was this last modified" are genuinely
different signals the moment a second person can ever see a project (a
future collaboration phase `ARCHITECTURE.md` explicitly reserves). Keyed by
`(user_id, project_id)` instead of just `project_id` means that phase is a
schema no-op: a second viewer just gets their own row. It also keeps
"viewed" cleanly separate from "modified" — a background job touching
`projects.updated_at` must never reorder the "recently viewed" dashboard rail.

**Why soft delete is `status` *and* `deleted_at`, unlike `users`:**
`users.status` alone (no `deleted_at`) was sufficient there because there's
no "restore my deleted account" product surface planned. Projects need one
(`DELETE` here is Undo-able) — `deleted_at` is what a restore window
("recoverable for 30 days") and a future purge job filter on, the same
pattern `sessions.revoked_at` already established for "when did this stop
being valid," not just "is it valid."

---

## 2. Database design

### 2.1 `projects`

| Column | Type | Notes |
|---|---|---|
| `id` | `UUID PK` | `gen_random_uuid()` |
| `owner_id` | `UUID NOT NULL FK → users(id) ON DELETE CASCADE` | Single owner, matches `database-schema-v1.md` |
| `name` | `TEXT NOT NULL` | 1–200 chars, enforced in `schemas.py`, not the DB — see below |
| `description` | `TEXT NULL` | Free text, shown on the project card |
| `status` | `TEXT NOT NULL DEFAULT 'active'` | `CHECK (status IN ('active','archived','deleted'))` |
| `archived_at` | `TIMESTAMPTZ NULL` | Set on archive, cleared on restore-to-active |
| `deleted_at` | `TIMESTAMPTZ NULL` | Set on soft delete, cleared on restore |
| `created_at` | `TIMESTAMPTZ NOT NULL DEFAULT now()` | |
| `updated_at` | `TIMESTAMPTZ NOT NULL DEFAULT now()` | via `set_updated_at()` trigger, same as every other table |

**Relationships:** `N:1 → users` (owner); `1:1 → project_settings`; `1:N → recent_projects`. Deferred (per `ARCHITECTURE.md` §7): `1:1 → repository_connections`, `1:N → roadmaps`.

**Indexes:**
- PK `id`.
- `ix_projects_owner_status_updated (owner_id, status, updated_at DESC)` — the dashboard's dominant query is "this owner's active (or archived) projects, most-recently-updated first"; indexing the triple avoids a sort at read time.
- No unique constraint on `(owner_id, name)` — two projects named "API redesign" is a real, harmless case (a scratch project and a real one); uniqueness would be a UX annoyance solving a problem nobody has.

**Constraints:** `FK owner_id ON DELETE CASCADE` (deleting a user's account — itself a soft delete today — cascades the FK relationship at the schema level regardless); `CHECK (status IN ('active','archived','deleted'))`.

**Why no DB-level length check on `name`:** matches `users.display_name`'s existing precedent — validation of user-facing string shape lives in Pydantic (`schemas.py`), not a `CHECK (length(...))` constraint. A constraint would 500-error on violation instead of a clean 422; Pydantic already owns this concern for every other table in the app.

### 2.2 `project_settings`

One row per project, created transactionally alongside the project (never a nullable "might not exist yet" join) — same 1:1 shape as `user_preferences`, including the same design call: **typed columns for the handful of settings every card/shell render actually needs, one JSONB catch-all for everything else**, promoted to a real column only once something needs to filter or index on it.

| Column | Type | Notes |
|---|---|---|
| `project_id` | `UUID PK FK → projects(id) ON DELETE CASCADE` | PK **is** the FK — true 1:1, no surrogate `id`, identical to `user_preferences.user_id` |
| `icon` | `TEXT NOT NULL DEFAULT '📁'` | Single emoji/short glyph — read on every card render, hence a real column |
| `color` | `TEXT NOT NULL DEFAULT 'slate'` | Named accent from a closed palette (`CHECK`ed, see below) — also read on every card render |
| `settings` | `JSONB NOT NULL DEFAULT '{}'` | Catch-all for anything not yet promoted (future: per-project notification prefs, editor prefs) |
| `updated_at` | `TIMESTAMPTZ NOT NULL DEFAULT now()` | trigger-maintained |

**Constraints:** `FK project_id ON DELETE CASCADE`; `CHECK (color IN ('slate','blue','green','amber','rose','violet'))` — a closed palette (not free text) because `color` drives a Tailwind class lookup on the frontend; free text would let a client submit a value that resolves to no class at all (silent, not a crash, so easy to ship and forget).

**Indexes:** none beyond the PK — every read is "this project's settings," which the PK already serves.

### 2.3 `recent_projects`

| Column | Type | Notes |
|---|---|---|
| `user_id` | `UUID NOT NULL FK → users(id) ON DELETE CASCADE` | |
| `project_id` | `UUID NOT NULL FK → projects(id) ON DELETE CASCADE` | |
| `last_viewed_at` | `TIMESTAMPTZ NOT NULL DEFAULT now()` | Upserted, not inserted-only — see below |

**PK:** composite `(user_id, project_id)` — no surrogate `id`. "Has this user viewed this project before" is a natural key, and a composite PK gets the dedupe for free instead of needing a separate unique constraint plus an `ON CONFLICT` target that duplicates it.

**Indexes:** PK `(user_id, project_id)` (also serves point lookups); `ix_recent_projects_user_viewed (user_id, last_viewed_at DESC)` — the dashboard's "recent projects" rail query.

**Write path:** every `GET /v1/projects/{id}` does `INSERT ... ON CONFLICT (user_id, project_id) DO UPDATE SET last_viewed_at = now()` — one row per (user, project) pair regardless of how many times it's opened, so this table's size is bounded by *distinct projects viewed*, never by *view count*. No reaper job needed, unlike `sessions`/`*_tokens` — this table doesn't grow unboundedly on its own.

### 2.4 ER diagram

```mermaid
erDiagram
    USERS ||--o{ PROJECTS : "owns"
    PROJECTS ||--|| PROJECT_SETTINGS : "has"
    USERS ||--o{ RECENT_PROJECTS : "views"
    PROJECTS ||--o{ RECENT_PROJECTS : "viewed via"

    PROJECTS {
        uuid id PK
        uuid owner_id FK
        text name
        text description
        text status
        timestamptz archived_at
        timestamptz deleted_at
        timestamptz created_at
        timestamptz updated_at
    }

    PROJECT_SETTINGS {
        uuid project_id PK_FK
        text icon
        text color
        jsonb settings
        timestamptz updated_at
    }

    RECENT_PROJECTS {
        uuid user_id PK_FK
        uuid project_id PK_FK
        timestamptz last_viewed_at
    }
```

---

## 3. Module design (`apps/api/app/modules/projects/`)

Same shape as `auth/` — the codebase's one established module template, followed exactly so a contributor who's read one module can navigate any other:

```
projects/
├── models.py        # Project, ProjectSettings, RecentProject (SQLAlchemy)
├── schemas.py        # Request/response Pydantic models — routes never take/return a bare dict
├── exceptions.py     # ProjectError subclasses + one registered handler (mirrors AuthError)
├── dependencies.py   # get_owned_project — the one enforcement point every project-scoped route depends on
├── service.py         # All business logic; routes call exactly one service function each
└── router.py           # Thin HTTP layer only
```

**`dependencies.get_owned_project`** is this module's equivalent of `auth.dependencies.get_current_user`: it loads `Project` by path param, and 404s (via `ProjectNotFoundError`) unless `project.owner_id == current_user.id` **and** `project.status != 'deleted'`. A caller who guesses another user's project ID, or their own already-deleted project's ID, gets the identical 404 either way — same enumeration-safety reasoning `auth`'s `InvalidCredentialsError`/`InvalidOrExpiredTokenError` already apply to logins and tokens, extended to "does this project exist and is it yours."

**Soft delete, restore, and archive are distinct operations, not one toggle:**
- *Archive* (`POST /archive`) — user-initiated "I'm done with this for now," fully reversible, not a step toward deletion. Archived projects are excluded from the default dashboard view but still listable.
- *Delete* (`DELETE`) — soft, sets `status='deleted'` + `deleted_at`. Excluded from every listing by default. Recoverable via `POST /restore` (no separate confirmation flow in V1 — a hard-delete/purge job is future scope, flagged below, not built here).
- *Restore* (`POST /restore`) — valid from either `archived` or `deleted`, always returns to `active`. One endpoint, not two, because "undo whichever non-active state this project is in" is the same operation from the caller's perspective.

---

## 4. API design

All routes under `/v1/projects`, all requiring `Depends(get_current_user)`.

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/v1/projects` | Create a project (+ its `project_settings` row, same transaction) |
| `GET` | `/v1/projects` | List the caller's projects — `?status=active\|archived` (default `active`), `?limit=&offset=` |
| `GET` | `/v1/projects/recent` | Recently-viewed projects for the dashboard rail — `?limit=` (default 5) |
| `GET` | `/v1/dashboard` | Single aggregate call the Dashboard page loads once: recent projects + active/archived counts |
| `GET` | `/v1/projects/{id}` | Fetch one project; records a view (upserts `recent_projects`) as a side effect |
| `PATCH` | `/v1/projects/{id}` | Partial update — `name`, `description` |
| `POST` | `/v1/projects/{id}/archive` | Archive |
| `POST` | `/v1/projects/{id}/restore` | Restore to active from archived or deleted |
| `DELETE` | `/v1/projects/{id}` | Soft delete |
| `GET` | `/v1/projects/{id}/settings` | Fetch project settings |
| `PATCH` | `/v1/projects/{id}/settings` | Partial update — `icon`, `color` |

**Why `GET /v1/dashboard` exists separately from `GET /v1/projects` and `GET /v1/projects/recent`, rather than making the frontend call both:** the Dashboard page's very first paint needs both pieces of data, and it's the one screen in this module where an extra round trip is directly visible as load-time jank. Every other screen (a single project's settings page, the project list) needs exactly one of these resources, so it gets its own plain, cacheable, independently-invalidatable endpoint instead of being folded into the aggregate.

**Why `ProjectRead` carries `icon`/`color` even though they live on `project_settings`:** every card-grid render (list, recent rail, dashboard) needs them, and a settings-per-card fetch would turn one list render into an N+1 — the exact "read on every card render, hence a real column" reasoning from Section 2.2, carried through to the API. `Project.settings` is loaded via SQLAlchemy's `lazy="joined"` (one SQL JOIN, every query of `Project`), and `ProjectRead.from_model()` flattens `project.settings.icon`/`.color` onto the response — the same explicit-adapter pattern `auth.schemas.UserRead.from_model` already uses for a shape FastAPI's automatic `from_attributes` conversion can't produce alone.

**Why `PATCH`, not `PUT`, for updates:** both project and settings updates are partial by design (rename without touching description; recolor without touching icon) — `schemas.py`'s update models make every field optional, so `PUT`'s "replace the whole resource" semantics would be actively misleading.

**Error shape:** identical contract to auth (`{"detail": ..., "error_code": ...}`), via the same one-handler-per-exception-base pattern:

| `error_code` | HTTP status |
|---|---|
| `project_not_found` | 404 |
| `project_validation_error` | 422 *(Pydantic's own handler covers this; listed for completeness)* |

---

## 5. Frontend design (`apps/web/src`)

```
app/
├── (app)/                       # route group: shared authenticated chrome
│   ├── layout.tsx                # Sidebar + top bar; the "Workspace Layout"
│   ├── dashboard/page.tsx         # Dashboard: recent projects, counts, create button, project grid
│   └── projects/[projectId]/
│       ├── layout.tsx              # Project-scoped header/tabs (Overview / Settings)
│       ├── page.tsx                 # Project overview (placeholder body — roadmap/milestones are a later step)
│       └── settings/page.tsx        # Project Settings Page: rename, describe, icon/color, danger zone
components/
├── projects/
│   ├── ProjectCard.tsx
│   ├── CreateProjectModal.tsx
│   └── EmptyState.tsx
└── layout/
    └── Sidebar.tsx
hooks/useProjects.ts               # React Query hooks — one per endpoint above
lib/projects-api.ts                # apiFetch wrappers — one per endpoint, mirrors lib/auth-api.ts
types/projects.ts                   # Mirrors schemas.py, same convention as types/auth.ts
```

**Why a `(app)` route group instead of repeating the sidebar in every page:** `apps/web` currently has exactly one protected page (`/dashboard`) with no shared chrome yet. Adding project pages is the second and third protected page — past the "three similar lines" threshold this codebase already uses to decide when an abstraction earns its keep (see `FormField.tsx`'s own comment). The route group's `layout.tsx` is that abstraction: one Sidebar, one auth-redirect effect, shared by every page under it instead of copy-pasted per page.

**State split (unchanged rule, just applied to a new domain):** every piece of project data — the project list, a single project, settings, recents — is server state and lives in React Query, keyed and invalidated per endpoint. `useSessionStore` (Zustand) continues to hold only `activeProjectId`/`currentMilestoneId` — genuinely client-only UI state — exactly the boundary its own comment already documents; this module adds no new Zustand state.

**Modal implementation:** no dialog/portal library is in `package.json` yet (no Radix, no shadcn) — `CreateProjectModal` is a plain fixed-overlay component (`role="dialog"`, `aria-modal`, Escape-to-close, click-outside-to-close, autofocus first field), matching the "don't add a dependency for one component" bar the rest of this app has held so far. Revisit if a second, more complex modal shows up and the hand-rolled version starts hurting.

**Middleware:** `middleware.ts`'s matcher gains `/projects/:path*` alongside the existing `/dashboard/:path*` — same presence-check-only reasoning already documented there (the real authorization boundary is `get_current_user` on the API, this only skips a pointless render-then-redirect for the no-cookie-at-all case).

---

## 6. Abuse resistance

Every other write endpoint in this app sits behind either the Effort
Evaluator (LLM-cost operations) or `auth`'s per-IP rate limiter
(pre-auth abuse). Plain CRUD on an already-authenticated account has
neither, so two narrow guards were added rather than left as gaps:

- **`max_active_projects_per_owner`** (`Settings`, default 200) —
  `create_project` 422s past this ceiling (`project_limit_exceeded`).
  A plain cap, not a full quota system — there's no per-operation cost
  ledger for CRUD the way there is for LLM calls, so this only bounds
  unlimited row growth from one account, nothing more.
- **`settings` JSON size cap** (10 KB, `schemas.ProjectSettingsUpdate`)
  — `name`/`description` already have `max_length`; the JSONB
  catch-all had no equivalent, so a client could otherwise PATCH an
  arbitrarily large blob repeatedly.

## 7. Explicitly out of scope for this pass

- Hard-delete / purge job for `deleted_at` projects past a retention window (mirrors the reaper-job notes already flagged for `sessions`/`*_tokens` in `database-schema-v1.md` — same category of future work, not yet needed at V1's scale).
- Project collaborators / shared ownership (`ARCHITECTURE.md` defers team features explicitly; `recent_projects`' `(user_id, project_id)` keying is the one piece of this schema already shaped for that day).
- `repository_connections`, `roadmaps`, `milestones` — still deferred per `ARCHITECTURE.md` §7, unchanged by this pass; `projects` is the parent they'll attach to.
