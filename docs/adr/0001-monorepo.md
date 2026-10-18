# 0001. Monorepo for backend, frontend and database

Date: 2026-10-18 · Status: Accepted

## Context
The previous Recollect attempt was split across `recollect-backend`, `recollect-ui`,
`recollect-extension` and `recollect-ai`. API changes needed coordinated PRs across repos,
and the repos drifted (the extension and UI pointed at different service URLs).

## Decision
One repository: `backend/` (Python: API, worker, Slack bot), `frontend/` (Next.js),
`supabase/` (migrations, local stack config), `docs/`. Each app keeps its own native
tooling (uv, pnpm). There is no JS monorepo tool (Turborepo/Nx) until there's a second
JS package.

## Consequences
- One PR can change the API and its client together, and CI checks both.
- CI runs every job on every PR. It's simple and fast at this size; add path filters
  if CI exceeds ~10 minutes.
- Deploys are per-app (Railway for `backend/`, Vercel for `frontend/`), configured with root directories.
