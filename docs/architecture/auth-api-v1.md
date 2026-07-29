# Auth API — V1

**Status:** Implemented (see `apps/api/app/modules/auth/`). Extends
[`database-schema-v1.md`](./database-schema-v1.md) (the data model) and
[`ARCHITECTURE.md`](./ARCHITECTURE.md) Section 3's "Auth & Identity"
module with the concrete HTTP contract and token design.

Full request/response schemas are auto-generated from the Pydantic
models and always up to date at `/docs` (Swagger UI) and `/redoc` when
the API is running — this document covers the parts that live *between*
the routes: the token model, the cookie contract, and the error shape,
none of which OpenAPI captures well on its own.

---

## 1. Token model: JWT access token + opaque refresh token

A hybrid, not a pure choice of one or the other:

- **Access token** — a short-lived (`ACCESS_TOKEN_TTL_MINUTES`, default 15
  min), signed JWT (HS256, `api_secret_key`). Stateless: verifying it
  never touches the database, which is what keeps per-request auth
  cheap. Carries only `sub` (user id), `type: "access"`, `iat`, `exp` —
  no roles/claims that could go stale before the token expires.
- **Refresh token** — a long-lived (`REFRESH_TOKEN_TTL_DAYS`, default 30
  days), opaque, high-entropy random string. Only its SHA-256 hash is
  ever persisted, in the `sessions` table (`apps/api/app/modules/auth/models.py`).
  This is what makes logout, "logout everywhere," and password-reset-
  triggered revocation real and instant, rather than "wait for the JWT
  to expire" — the exact capability `database-schema-v1.md` designed the
  `sessions` table around.
- **Rotation on use** — every `POST /v1/auth/refresh` call issues a new
  refresh token and invalidates the old one's hash on the same session
  row. A stolen-but-unused refresh token stops working the moment the
  legitimate client refreshes.

Why not one or the other alone: a pure session-cookie model (looked up
in Postgres on every request) is simpler but puts a DB round-trip on
every single API call. A pure stateless JWT (no `sessions` table at all)
can't be revoked early without a separate blocklist — a leaked
credential would remain valid until it expires. The hybrid gets cheap
per-request checks *and* real revocation, at the cost of one extra
table and a refresh endpoint.

## 2. Cookie contract

Both tokens are set as `httpOnly` cookies by every endpoint that issues
them (`register`, `login`, `refresh`) — never returned to JS-readable
storage. `access_token` is additionally returned in the JSON response
body (`AccessTokenResponse.access_token`) for non-browser callers
(mobile, CLI, server-to-server) that can't rely on a cookie jar; the
refresh token is **cookie-only, always** — it's the long-lived
credential, so it never appears in a response body.

| Cookie | Path | Lifetime | Sent to |
|---|---|---|---|
| `access_token` | `/` | `ACCESS_TOKEN_TTL_MINUTES` | Every API request |
| `refresh_token` | `/v1/auth` | `REFRESH_TOKEN_TTL_DAYS` | Only `/v1/auth/*` routes — it's never needed anywhere else |

`Secure` is derived from `ENVIRONMENT` (`Settings.cookie_secure`) —
on in production, off in dev so cookies still work over plain
`http://localhost`. `SameSite=Lax`. `Domain` is unset (host-only) by
default; set `COOKIE_DOMAIN` if web and api ever live on different
subdomains in production.

## 3. Endpoints

All routes are under `/v1/auth`.

| Method | Path | Auth required | Purpose |
|---|---|---|---|
| POST | `/register` | No | Create account, send verification email, log in immediately |
| POST | `/login` | No | Authenticate, issue tokens |
| POST | `/refresh` | Refresh cookie | Rotate refresh token, issue new access token |
| POST | `/logout` | Refresh cookie | Revoke the current session |
| POST | `/logout-all` | Access token | Revoke every session for the user |
| GET | `/me` | Access token | Current user |
| POST | `/forgot-password` | No | Issue a password-reset token, email it (always 200) |
| POST | `/reset-password` | No (token in body) | Consume the token, set new password, revoke all sessions |
| POST | `/verify-email` | No (token in body) | Consume the token, set `email_verified_at` |
| POST | `/resend-verification` | No | Re-issue a verification token if unverified |

`register` and `login` auto-log-in the user (tokens issued immediately)
— email verification is informational (`UserRead.email_verified`), not
a gate on using the product.

## 4. Error shape

Every auth failure returns:

```json
{ "detail": "human-readable message", "error_code": "machine_readable_code" }
```

via a single handler registered against the `AuthError` base class
(`app/modules/auth/exceptions.py: register_auth_exception_handlers`) —
every subclass maps to one HTTP status:

| `error_code` | HTTP status | Notes |
|---|---|---|
| `email_already_registered` | 409 | |
| `invalid_credentials` | 401 | Same message/code whether the email doesn't exist or the password is wrong — never distinguish, that's an account-enumeration leak |
| `account_locked` | 423 | After `MAX_FAILED_LOGIN_ATTEMPTS` (default 5) failed logins; clears after `LOCKOUT_DURATION_MINUTES` (default 15) |
| `account_disabled` | 403 | `users.status != 'active'` |
| `invalid_or_expired_token` | 400 | Shared by refresh/reset/verification token validation — same "don't distinguish why" reasoning |
| `not_authenticated` | 401 | Missing/invalid/expired access token |

`forgot-password` and `resend-verification` are deliberately **not** in
this table for the "email not found" case — they return the same 200
`MessageResponse` regardless of whether the account exists, by design
(see `service.request_password_reset`).

## 5. Password & account-security rules

- Argon2id hashing (`argon2-cffi`, library-tuned default cost
  parameters), opportunistic rehash-on-login if the library's defaults
  change (`needs_rehash`).
- Length-only password policy (8–128 chars), per NIST 800-63B — no
  forced composition rules that push users toward predictable
  substitutions.
- Lockout: 5 failed attempts locks the account for 15 minutes
  (`Settings.max_failed_login_attempts` / `lockout_duration_minutes`).
- Timing-safe "no such user": a login attempt against an unregistered
  email still runs a full Argon2 verify against a fixed dummy hash, so
  "no such user" and "wrong password" cost the same wall-clock time.
- A successful password reset revokes every existing session — the
  strongest available signal that the account may have been
  compromised, so no stolen session should outlive the recovery.

## 6. What's deliberately out of scope for this pass

- Rate limiting `login` / `forgot-password` / `resend-verification` by
  IP or email — the stack already has Redis for this (per
  `ARCHITECTURE.md`'s Cost & Abuse Control module), but it isn't wired
  up here; the lockout mechanism above is the only current brute-force
  defense.
- A real transactional email provider — `app/modules/auth/email.py`'s
  `ConsoleEmailSender` logs the reset/verification link instead of
  sending it; swap `get_email_sender()`'s branch for a real provider
  (SES/Postmark/Resend) once one is actually configured.
- `projects` / `user_preferences` tables from `database-schema-v1.md` —
  not part of the auth surface itself; left for whichever module
  actually needs them first.
- GitHub OAuth login itself — `github_identities`/`oauth_tokens` models
  and their migration already exist as scaffolding; wiring the actual
  OAuth flow is separate work.
