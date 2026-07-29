# Database Schema — V1 (Auth, Sessions, Projects)

**Status:** `users`, `sessions`, `password_reset_tokens`, `email_verification_tokens` implemented — see
migration `apps/api/alembic/versions/202607291200_add_auth_identity_tables.py` and
[`auth-api-v1.md`](./auth-api-v1.md) for the API built on top. `sessions` ended up
scoped as the JWT hybrid's *refresh-token* store rather than a primary session
record (see auth-api-v1.md Section 1) — same table shape and revocation
rationale described below, different token in it. `projects` and
`user_preferences` were **not** implemented in this pass (out of scope for
"the auth system" specifically) and remain draft, described below for
whichever module builds them next.
**Scope:** `users`, `sessions`, `projects`, `user_preferences`, `password_reset_tokens`, `email_verification_tokens` only. See [ARCHITECTURE.md](./ARCHITECTURE.md) Section 7 for the full V1 data model this extends (taxonomy, mastery, reviews, etc. — not covered here).

**Auth model decision:** hybrid. `ARCHITECTURE.md` locked GitHub-OAuth-only login for V1; this schema adds email/password as a second, coexisting login method — exactly the "second login method... without an identity migration" path the doc reserved. `users` remains the stable identity anchor; GitHub identity (`github_identities`, `oauth_tokens`, already scaffolded in `apps/api/app/modules/auth/models.py`) stays a separate linked table, unchanged by this pass.

---

## Cross-cutting conventions (apply to every table below)

| Convention | Choice | Why |
|---|---|---|
| Primary keys | `UUID DEFAULT gen_random_uuid()` | Native to Postgres 13+, no extension needed. Avoids sequential-ID enumeration over the API (`/users/1`, `/users/2`). |
| Timestamps | `TIMESTAMPTZ`, never bare `TIMESTAMP` | Bare `TIMESTAMP` silently drops timezone info — a classic source of off-by-N-hours bugs the moment the app or a user isn't in UTC. |
| Email | `CITEXT`, not `TEXT` | Case-insensitive comparison and uniqueness at the DB level (`Foo@x.com` and `foo@x.com` are the same account) instead of relying on the app to remember to `.lower()` everywhere. Requires `CREATE EXTENSION citext` — one more hand-written migration, same category as the existing `vector` extension migration. |
| Enums (`status`, `theme`, …) | `TEXT` + `CHECK` constraint, not native Postgres `ENUM` | Native `ENUM` is marginally more compact, but adding a value later (`ALTER TYPE ... ADD VALUE`) has real operational friction inside transactional migration tools like Alembic. `TEXT` + `CHECK` is one ordinary `ALTER TABLE` to change. At this row-count scale, the storage savings from native `ENUM` don't matter; the migration friction does. |
| Deletion | Soft delete via `status`, not `DELETE FROM` | Users, projects, etc. are FK targets from many tables. Hard-deleting a row that other rows reference either cascades destructively or requires nulling everything out. A `status` column (`active` / `disabled` / `archived`) keeps history intact and is reversible. |
| Secrets (session tokens, reset tokens) | Store a **hash** of the token, never the raw value | Identical reasoning to why passwords are hashed: if this table is ever exposed (backup leak, replica misconfig, SQL injection), a raw session/reset token is an instant account takeover. The raw token exists only transiently — sent once to the client, hashed for every subsequent lookup. |
| `updated_at` | Maintained by a shared `BEFORE UPDATE` trigger (`set_updated_at()`), not app code | Relying on every code path to remember `updated_at = now()` fails the first time someone runs a raw `UPDATE`. One trigger function, attached to every table that has the column, makes it structurally impossible to forget. |

---

## 1. `users`

**Purpose:** The platform's stable identity anchor — every other table's `user_id` points here, never at a GitHub user ID or an email directly (the same "decouple identity from any one login method" principle `ARCHITECTURE.md` already applied to `github_identities`/`oauth_tokens`).

**Columns**

| Column | Type | Notes |
|---|---|---|
| `id` | `UUID PK` | `gen_random_uuid()` |
| `email` | `CITEXT NOT NULL` | |
| `email_verified_at` | `TIMESTAMPTZ NULL` | `NULL` = unverified. No separate boolean — a nullable timestamp *is* the boolean, and it also records *when*, for free. |
| `password_hash` | `TEXT NULL` | Full Argon2id-encoded string (`$argon2id$v=19$m=...,t=...,p=...$salt$hash`) — algorithm, salt, and cost parameters are embedded in the encoding itself, so no separate `salt` or `password_algo` column is needed. `NULL` for users who only ever used GitHub OAuth. |
| `password_updated_at` | `TIMESTAMPTZ NULL` | Drives future "force reset after N days" policy. |
| `display_name` | `TEXT NOT NULL` | |
| `status` | `TEXT NOT NULL DEFAULT 'active'` | `CHECK (status IN ('active','disabled','deleted'))` |
| `failed_login_attempts` | `SMALLINT NOT NULL DEFAULT 0` | Basic brute-force lockout. |
| `locked_until` | `TIMESTAMPTZ NULL` | |
| `created_at` | `TIMESTAMPTZ NOT NULL DEFAULT now()` | |
| `updated_at` | `TIMESTAMPTZ NOT NULL DEFAULT now()` | |

**Relationships:** `1:N` → `sessions`, `1:N` → `projects` (as owner), `1:1` → `user_preferences`, `1:N` → `password_reset_tokens`, `1:N` → `email_verification_tokens`. Deferred: `1:1` → `github_identities`, `1:1` → `oauth_tokens` (already scaffolded, out of scope this pass).

**Indexes:** PK on `id`; `UNIQUE` on `email` (CITEXT makes this case-insensitive automatically).

**Constraints:** `email UNIQUE NOT NULL`; `CHECK (failed_login_attempts >= 0)`; `CHECK (status IN ('active','disabled','deleted'))`.

**A deliberate inconsistency, explained:** `oauth_tokens` is a *separate, decoupled* table specifically because a raw OAuth bearer token is plaintext-equivalent — reversible, usable as-is against GitHub. A password hash is the opposite: it's already the safe-at-rest form, one-way by construction. Splitting it into its own table would buy nothing security-wise and would just add a join to every login check. That's why `password_hash` lives directly on `users` while OAuth tokens don't.

**Future scalability:**
- `failed_login_attempts` gets incremented on *every* login attempt — a hot, frequently-updated column on an otherwise slow-changing row. At real scale this causes MVCC bloat (`users` rows rewritten on every failed login). If login volume becomes significant, move failed-attempt counting into Redis (rate-limit-shaped data, and the stack already has Redis for exactly this) and only touch Postgres on account lockout, not on every attempt.
- No enforced "must have at least one login method" constraint yet — can't be, since `github_identities` isn't in this pass. Once it exists, this becomes an application-layer invariant (or a `CHECK`-via-trigger) rather than a plain column constraint.

---

## 2. `sessions`

**Purpose:** Server-authoritative session store — every authenticated request looks up its session row here. This is what makes "log out everywhere" and immediate revocation possible, which matters once password auth exists (a leaked password now needs a hard, instant revocation path).

**Columns**

| Column | Type | Notes |
|---|---|---|
| `id` | `UUID PK` | |
| `user_id` | `UUID NOT NULL FK → users(id)` | |
| `session_token_hash` | `TEXT NOT NULL UNIQUE` | SHA-256 of the raw session token (the raw token lives only in an `httpOnly` cookie on the client). |
| `user_agent` | `TEXT NULL` | |
| `ip_address` | `INET NULL` | Native Postgres type — validated on write, supports range/subnet queries later, cheaper than storing as `TEXT`. |
| `created_at` | `TIMESTAMPTZ NOT NULL DEFAULT now()` | |
| `last_seen_at` | `TIMESTAMPTZ NOT NULL DEFAULT now()` | |
| `expires_at` | `TIMESTAMPTZ NOT NULL` | |
| `revoked_at` | `TIMESTAMPTZ NULL` | Explicit logout / admin action / "log out everywhere". |

**Relationships:** `N:1` → `users`.

**Indexes:** PK `id`; `UNIQUE` on `session_token_hash` (this *is* the per-request lookup path); index on `user_id` (list/revoke all sessions for a user); index on `expires_at` (cleanup job, below).

**Constraints:** `FK user_id ON DELETE CASCADE`; `CHECK (expires_at > created_at)`.

**Future scalability:**
- `last_seen_at` updated on every request is a genuine hot-row problem at real traffic — every API call becomes an `UPDATE`. Standard fix: only write if the existing value is more than ~5 minutes stale, or move `last_seen_at` into Redis entirely and treat Postgres as the durable-but-coarser record.
- This table grows forever without a reaper. Needs a periodic job (the `ingestion_worker`'s arq cron pattern already established in the scaffold is the natural home) deleting rows where `expires_at < now() - retention_window`.
- If session volume gets large, this is a good candidate for monthly range-partitioning by `created_at` — old sessions become cheap to bulk-drop (drop a partition) instead of row-by-row `DELETE`.

---

## 3. `projects`

**Purpose:** Minimal shell for "the thing a learner is working on" — the parent that `repository_connections`, `roadmaps`, and `milestones` (per `ARCHITECTURE.md` Section 7, out of scope this pass) will attach to via FK later, without this table needing to change shape when they do.

**Columns**

| Column | Type | Notes |
|---|---|---|
| `id` | `UUID PK` | |
| `owner_id` | `UUID NOT NULL FK → users(id)` | Single owner — matches the doc's own scoping (team/collaboration features are explicitly a later phase). |
| `name` | `TEXT NOT NULL` | |
| `status` | `TEXT NOT NULL DEFAULT 'active'` | `CHECK (status IN ('active','archived'))` |
| `created_at` | `TIMESTAMPTZ NOT NULL DEFAULT now()` | |
| `updated_at` | `TIMESTAMPTZ NOT NULL DEFAULT now()` | |

**Relationships:** `N:1` → `users` (owner). Deferred: `1:1` → `repository_connections`, `1:N` → `roadmaps`.

**Indexes:** PK `id`; composite index on `(owner_id, status)` — "list my active projects" is the overwhelmingly dominant query pattern, so index the pair rather than `owner_id` alone.

**Constraints:** `FK owner_id ON DELETE CASCADE`; `CHECK (status IN ('active','archived'))`.

**Future scalability:**
- This table itself will always be small (one row per project, not per event) — it will never need partitioning on its own. The scaling question is entirely about what attaches to it via FK.
- When `repository_connections`/`roadmaps` land, revisit delete semantics carefully: archiving a project (status flip) probably shouldn't cascade-delete review/milestone history if that history has standalone value ("look back at old reviews"). Decide cascade vs. restrict per child table then, not now.

---

## 4. `user_preferences`

**Purpose:** One row per user for settings that are neither identity (`users`) nor ephemeral session state (`sessions`) — a classic "account settings page" table.

**Design call:** not EAV (`user_id, key, value` rows), not pure JSONB either. A handful of well-known, frequently-read/filtered preferences get real typed columns; everything else goes in one `settings JSONB` catch-all. Pure EAV loses type safety and makes even a simple query awkward; pure JSONB loses indexability/`CHECK` constraints for the things you *do* query on. The rule going forward: **promote a JSONB key to a real column only once something actually needs to filter or index on it** — don't pre-guess.

**Columns**

| Column | Type | Notes |
|---|---|---|
| `user_id` | `UUID PK FK → users(id)` | PK **is** the FK — true 1:1, no surrogate `id`. |
| `theme` | `TEXT NOT NULL DEFAULT 'system'` | `CHECK (theme IN ('system','light','dark'))` |
| `timezone` | `TEXT NOT NULL DEFAULT 'UTC'` | IANA name, e.g. `America/New_York`. |
| `email_notifications_enabled` | `BOOLEAN NOT NULL DEFAULT true` | |
| `product_updates_opt_in` | `BOOLEAN NOT NULL DEFAULT true` | |
| `settings` | `JSONB NOT NULL DEFAULT '{}'` | Catch-all for anything not yet promoted. |
| `updated_at` | `TIMESTAMPTZ NOT NULL DEFAULT now()` | |

**Relationships:** `1:1` → `users`.

**Indexes:** none beyond the PK — every real lookup is "my preferences" by `user_id`, which the PK already serves.

**Constraints:** `FK user_id ON DELETE CASCADE`; `CHECK (theme IN (...))`.

**Future scalability:** if a specific `settings` key needs to be queried/filtered across users (e.g., "find everyone who opted into X"), add a GIN index on `settings` *then* — not preemptively. Row count is always exactly 1-per-user; never a growth concern on its own.

---

## 5. `password_reset_tokens`

**Purpose:** One-time, short-lived, hashed tokens issued for "forgot password"; consumed exactly once to authorize a new password.

**Columns**

| Column | Type | Notes |
|---|---|---|
| `id` | `UUID PK` | |
| `user_id` | `UUID NOT NULL FK → users(id)` | |
| `token_hash` | `TEXT NOT NULL UNIQUE` | SHA-256 of the raw token (raw token only ever exists in the emailed link). |
| `created_at` | `TIMESTAMPTZ NOT NULL DEFAULT now()` | |
| `expires_at` | `TIMESTAMPTZ NOT NULL` | App sets a short TTL (30–60 min is typical). |
| `consumed_at` | `TIMESTAMPTZ NULL` | `NULL` = still valid/unused. |
| `requested_ip` | `INET NULL` | Abuse/audit trail. |

**Relationships:** `N:1` → `users`.

**Indexes:** PK `id`; `UNIQUE token_hash` (the lookup path); index on `user_id`; **partial** index `ON (user_id) WHERE consumed_at IS NULL` — the overwhelming majority of rows become dead weight within the hour, so index only the ones still relevant.

**Constraints:** `FK user_id ON DELETE CASCADE`; `CHECK (expires_at > created_at)`.

**Note on "only one active token per user":** can't be a true partial-unique index, because `now()` isn't allowed in an index predicate (not immutable) — `expires_at > now()` can't go in a `WHERE` clause on an index. In practice: when issuing a new reset token, the app invalidates (`consumed_at = now()`) any prior unconsumed token for that user in the same transaction. This is an application-layer invariant, not a DB one — worth stating explicitly so it isn't assumed to be enforced somewhere it isn't.

**Future scalability:** high-churn, low-retention table — needs the same reaper-job treatment as `sessions` (purge rows past `expires_at` + a retention buffer, e.g. 30 days for audit purposes). Rate-limiting the "forgot password" endpoint itself (per email/IP) is a Redis/app concern, not a schema one — flagging so it isn't forgotten at implementation time.

---

## 6. `email_verification_tokens`

**Purpose:** Structurally identical to `password_reset_tokens`, different job — proves the user controls an email address (at signup, and later for email-change flows). Successful verification sets `users.email_verified_at`.

**Columns**

| Column | Type | Notes |
|---|---|---|
| `id` | `UUID PK` | |
| `user_id` | `UUID NOT NULL FK → users(id)` | |
| `token_hash` | `TEXT NOT NULL UNIQUE` | |
| `email` | `TEXT NOT NULL` | The address *being verified* — see below for why this isn't just read off `users.email`. |
| `created_at` | `TIMESTAMPTZ NOT NULL DEFAULT now()` | |
| `expires_at` | `TIMESTAMPTZ NOT NULL` | |
| `consumed_at` | `TIMESTAMPTZ NULL` | |

**Relationships:** `N:1` → `users`.

**Indexes:** same shape as `password_reset_tokens` — PK `id`, `UNIQUE token_hash`, index on `user_id`, partial index `WHERE consumed_at IS NULL`.

**Constraints:** `FK user_id ON DELETE CASCADE`; `CHECK (expires_at > created_at)`.

**Why store `email` on the token instead of just checking `users.email`:** a future "change your email" flow needs to verify a *new, not-yet-committed* address before writing it to `users.email`. If verification only ever checked the current `users.email`, an in-flight email change would be ambiguous — which email is actually being proven? Storing the target email on the token itself removes that ambiguity for free, at signup *and* later.

**Why separate from `password_reset_tokens` rather than one polymorphic `auth_tokens(purpose, ...)` table:** considered and rejected for V1 — the two token types already have (or will plausibly grow) different TTL policies and different consumption side-effects (one authorizes a password change, the other flips `email_verified_at` and possibly updates `email`). Keeping them as separate tables keeps each one's invariants and indexes simple; unifying saves a small amount of DDL at the cost of a `purpose` branch showing up in every query against the table.

**Future scalability:** identical reaper-job note as `password_reset_tokens`.

---

## ER Diagram

```mermaid
erDiagram
    USERS ||--o{ SESSIONS : "has"
    USERS ||--o{ PROJECTS : "owns"
    USERS ||--|| USER_PREFERENCES : "has"
    USERS ||--o{ PASSWORD_RESET_TOKENS : "requests"
    USERS ||--o{ EMAIL_VERIFICATION_TOKENS : "requests"

    USERS {
        uuid id PK
        citext email UK
        timestamptz email_verified_at
        text password_hash
        timestamptz password_updated_at
        text display_name
        text status
        smallint failed_login_attempts
        timestamptz locked_until
        timestamptz created_at
        timestamptz updated_at
    }

    SESSIONS {
        uuid id PK
        uuid user_id FK
        text session_token_hash UK
        text user_agent
        inet ip_address
        timestamptz created_at
        timestamptz last_seen_at
        timestamptz expires_at
        timestamptz revoked_at
    }

    PROJECTS {
        uuid id PK
        uuid owner_id FK
        text name
        text status
        timestamptz created_at
        timestamptz updated_at
    }

    USER_PREFERENCES {
        uuid user_id PK_FK
        text theme
        text timezone
        boolean email_notifications_enabled
        boolean product_updates_opt_in
        jsonb settings
        timestamptz updated_at
    }

    PASSWORD_RESET_TOKENS {
        uuid id PK
        uuid user_id FK
        text token_hash UK
        timestamptz created_at
        timestamptz expires_at
        timestamptz consumed_at
        inet requested_ip
    }

    EMAIL_VERIFICATION_TOKENS {
        uuid id PK
        uuid user_id FK
        text token_hash UK
        text email
        timestamptz created_at
        timestamptz expires_at
        timestamptz consumed_at
    }
```

---

## Explicitly out of scope for this pass

`github_identities`, `oauth_tokens` (already scaffolded in `apps/api/app/modules/auth/models.py` — will need reconciling with this design at implementation time, e.g. `users.email` moving to `CITEXT`), `repository_connections`, `roadmaps`, `milestones`, `concepts`, `user_concept_mastery`, `reviews` — all deferred per `ARCHITECTURE.md` Section 7, unchanged by this pass.
