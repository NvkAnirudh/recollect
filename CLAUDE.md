# CLAUDE.md

## Project

Recollect: save Instagram Reels (from the web app or a Slack DM) and find them later with
natural-language search over what was **said**, **shown on screen**, and **captioned**.
Single user today; built for multiple users from day one.

- Design spec: `docs/superpowers/specs/2026-10-18-recollect-v1-design.md` (source of truth for scope and phases)
- Decisions: `docs/adr/`. Read them before proposing architectural changes; add a new ADR for new decisions.
- Local setup: `docs/runbooks/local-development.md`

## Layout (monorepo)

| Path | What | Stack |
|---|---|---|
| `backend/` | API, worker, Slack bot (one package, `src/recollect/`) | Python 3.14, uv, FastAPI, psycopg 3, structlog, ruff, pyright (strict), pytest |
| `frontend/` | Web app | Next.js 16 (App Router), TypeScript strict, pnpm, Tailwind 4, vitest, Prettier |
| `supabase/` | SQL migrations, seed, local stack config | Supabase CLI, Postgres 17 + pgvector |
| `.github/` | CI, security scans, Dependabot, templates | |

`frontend/AGENTS.md` applies to the frontend: this Next.js version differs from training data,
so read `frontend/node_modules/next/dist/docs/` before using a Next API.

## Commands

`make help` lists everything. The common ones:

```bash
make setup         # once: deps + git hooks
make db            # local Supabase (Postgres/Auth/Storage)
make api           # backend on :8000 (docs at /docs)
make web           # frontend on :3000
make check         # what CI runs: format, lint, types, tests, build
make db-new name=x # new migration
```

Single tests: `cd backend && uv run pytest tests/unit/test_security.py -k expired` ·
`cd frontend && pnpm vitest run src/lib/api-client.test.ts`

## Workflow rules

- **Never commit to `main`.** Branch (`feat/…`, `fix/…`, `chore/…`), open a PR, squash-merge
  once `CI OK` passes. PR titles are Conventional Commits (`feat(backend): …`) because the
  squash commit uses the PR title.
- **TDD** for backend logic: write the failing test first. Coverage gate is 80% (both apps).
- Keep CI green: run `make check` before pushing.
- Schema changes are always a **new** migration in `supabase/migrations/`; never edit a merged one.

## Backend conventions

- App factory: `recollect.api.main:create_app(settings)`. Tests build their own app with test settings.
- Routes live under `/api/v1/`. Request and response bodies are Pydantic models; never return raw rows/dicts.
- Business logic goes in service modules, not route handlers. SQL lives only in the repository layer (`recollect/db/`).
- Errors: raise `AppError(status, code, message)`. Every error response is `{"error": {"code", "message"}}`.
- Config only via `recollect.core.config.Settings` (env vars). Deployed environments refuse localhost defaults.
- Logging: `get_logger(__name__)`, structured key/values. Never log request bodies, query strings, captions,
  transcripts, search queries, or tokens.
- Type hints everywhere; pyright strict must pass.

## Frontend conventions

- Talk to the backend only through `src/lib/api-client.ts`. Supabase in the browser is for auth only.
- Public env vars are validated in `src/lib/env.ts`. Add new ones there and to `.env.example`.
- Tests are colocated as `*.test.ts(x)`.

## Security rules (non-negotiable)

- **Every endpoint except `/health` depends on `AuthenticatedUser`**, and every query is scoped by `user_id`.
- **RLS enabled on every table**, with owner-only policies.
- **No secrets in the repo.** Only `.env.example` files are committed. The repo is public, so any
  committed secret is compromised: rotate it first, then clean up.
- CORS uses explicit origins only. Never `*`.
- New dependencies: prefer well-maintained ones; lockfiles are always committed.
