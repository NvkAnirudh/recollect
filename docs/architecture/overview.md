# Architecture overview (as built)

This describes the system **as it exists on `main` today**. The target design is in the
[v1 spec](../superpowers/specs/2026-10-18-recollect-v1-design.md). Update this file in any PR
that adds or changes a component, data flow or table.

_Last updated: 2026-10-18 (scaffold, [#2](https://github.com/NvkAnirudh/recollect/pull/2))._

## Components

| Component | Path | Status | Runs on (planned) |
|---|---|---|---|
| API | `backend/src/recollect/api/` | `/health`, `/api/v1/me` | Railway |
| Worker | `backend/src/recollect/worker/` | not started ([#33](https://github.com/NvkAnirudh/recollect/issues/33)) | Railway |
| Slack bot | inside the API | not started ([#43](https://github.com/NvkAnirudh/recollect/issues/43)) | Railway |
| Web app | `frontend/` | placeholder home page, API client | Vercel |
| Database/Auth/Storage | `supabase/` | baseline migration | Supabase |

## Backend request pipeline

Middleware, outermost first (`recollect/api/main.py`):

1. `RequestIDMiddleware`: a fresh UUID per request, bound to every log line and returned as `X-Request-ID`.
2. `RequestLoggingMiddleware`: one `request_completed` log per request (method, path, status, duration). Never bodies or query strings.
3. `SecurityHeadersMiddleware`: `nosniff`, `DENY` framing, `no-referrer`, a restrictive CSP, and HSTS in deployed environments.
4. `CORSMiddleware`: explicit origins from `CORS_ORIGINS`, no credentials (bearer tokens only).
5. Rate limiting: `slowapi`, per client IP, `RATE_LIMIT` (default `100/minute`).

Errors (`recollect/core/errors.py`): every failure returns `{"error": {"code", "message"}}`.
Unhandled exceptions are logged with a traceback and returned as a generic 500.

## Authentication

- Users sign in with **Supabase Auth** in the web app; the app sends the access token as `Authorization: Bearer`.
- The API verifies tokens **locally** (`recollect/core/security.py`): signature, `exp`, `iss`
  (`{SUPABASE_URL}/auth/v1`) and `aud` (`authenticated`). Hosted projects use asymmetric keys
  from the project's JWKS (cached 1h). The local stack uses the HS256 secret from `supabase status`.
- Routes declare `user: AuthenticatedUser`; `/health` is the only unauthenticated route.

## Data model

| Table | Purpose | RLS |
|---|---|---|
| `public.profiles` | One row per auth user (timezone). Created by the `on_auth_user_created` trigger; deleted with the user | Owner can select/update |

Extensions: `vector` (pgvector) in the `extensions` schema.

## Configuration

All backend configuration comes from environment variables via `recollect.core.config.Settings`.
See [reference/configuration.md](../reference/configuration.md). In `staging`/`production` the API
refuses to start with localhost URLs, a shared JWT secret, wildcard/localhost CORS, or non-JSON logs.

## Build and deploy artefacts

- Backend: one Docker image (`backend/Dockerfile`), multi-stage, non-root user `app`, no pip/setuptools at runtime, a healthcheck on `/health`.
- Frontend: a Next.js build. Security headers are set in `next.config.ts`.
