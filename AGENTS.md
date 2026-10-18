# AGENTS.md

Instructions for every contributor, **human or AI agent** (Claude Code, Codex, Cursor, Copilot,
Gemini, …), in every session. `CLAUDE.md` imports this file. Read it fully before doing any work.

## Mandatory workflow (do not skip, in any session)

These rules come from the project owner and apply to all work unless the owner explicitly says otherwise.

1. **Every piece of work is a GitHub issue** in the Epic → Feature → Story hierarchy (native
   sub-issues), on the **Recollect** GitHub Project board. Before starting work, find the
   issue. If there isn't one, create it at the right level and link it to its parent (see
   [`docs/process/sdlc.md` §1](docs/process/sdlc.md)). Use your judgement on the level; one
   story = one PR.
2. **Every change is documented in the same PR.** At minimum a `CHANGELOG.md` line under
   `## [Unreleased]`, plus the docs the change type requires
   ([`docs/process/sdlc.md` §4](docs/process/sdlc.md)): API reference, configuration
   reference, architecture overview, ADRs, spec, runbooks.
3. **Never commit to `main`.** Branch → PR with a Conventional Commit title and
   `Closes #<issue>` → all required checks green → squash-merge.
4. **Keep the board current:** move items to In progress/In review, and close parents when all children are done.
5. **When a mandatory rule changes**, update `docs/process/sdlc.md` and this section in the same PR.

## Project

Recollect: save Instagram Reels (from the web app or a Slack DM) and find them later with
natural-language search over what was **said**, **shown on screen**, and **captioned**.
Single user today; built for multiple users from day one.

| Doc | Purpose |
|---|---|
| [`docs/README.md`](docs/README.md) | Index of all documentation |
| [`docs/process/sdlc.md`](docs/process/sdlc.md) | Full SDLC process (issues, board, PRs, docs, definition of done) |
| [`docs/superpowers/specs/2026-10-18-recollect-v1-design.md`](docs/superpowers/specs/2026-10-18-recollect-v1-design.md) | v1 design spec: source of truth for scope and phases |
| [`docs/architecture/overview.md`](docs/architecture/overview.md) | How the system is built today |
| [`docs/adr/`](docs/adr/) | Architecture decisions. Read before proposing architectural changes; add an ADR for new ones |
| [`docs/runbooks/local-development.md`](docs/runbooks/local-development.md) | Local setup |

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

## Engineering rules

- **TDD** for backend logic: write the failing test first. The coverage gate is 80% for both apps.
- Schema changes are always a **new** migration in `supabase/migrations/`; never edit a merged one.

### Backend
- App factory: `recollect.api.main:create_app(settings)`. Tests build their own app with test settings.
- Routes live under `/api/v1/`. Request and response bodies are Pydantic models; never return raw rows/dicts.
- Business logic goes in service modules, not route handlers. SQL lives only in the repository layer (`recollect/db/`).
- Errors: raise `AppError(status, code, message)`. Every error response is `{"error": {"code", "message"}}`.
- Config only via `recollect.core.config.Settings` (env vars). Deployed environments refuse localhost defaults.
- Logging: `get_logger(__name__)`, structured key/values. Never log request bodies, query strings,
  captions, transcripts, search queries, or tokens.
- Type hints everywhere; pyright strict must pass.

### Frontend
- Talk to the backend only through `src/lib/api-client.ts`. Supabase in the browser is for auth only.
- Public env vars are validated in `src/lib/env.ts`. Add new ones there and to `.env.example`.
- Tests are colocated as `*.test.ts(x)`.

### Security (non-negotiable)
- **Every endpoint except `/health` depends on `AuthenticatedUser`**, and every query is scoped by `user_id`.
- **RLS enabled on every table**, with owner-only policies.
- **No secrets in the repo.** Only `.env.example` files are committed. The repo is public, so any
  committed secret is compromised: rotate it first, then clean up (see `SECURITY.md`).
- CORS uses explicit origins only. Never `*`.
- Version bumps (Python, Node, base images) change every pin together: Dockerfile, `.python-version`/`.nvmrc`, tool targets, docs.
