# Local development

## Prerequisites
Docker, [uv](https://docs.astral.sh/uv/), Node 24 + pnpm, and the Supabase CLI.
On macOS: `brew install uv pnpm supabase/tap/supabase pre-commit gitleaks actionlint`.

## First run
```bash
make setup          # deps + git hooks
make db             # starts local Supabase and prints its URL and keys
```
Copy the values `supabase status` prints:
- `backend/.env`: `SUPABASE_JWT_SECRET` (JWT secret). Everything else defaults to the local stack.
- `frontend/.env.local`: `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY` (publishable key). See `frontend/.env.example`.

Then, in two terminals:
```bash
make api            # http://localhost:8000/docs
make web            # http://localhost:3000
```
Supabase Studio: http://127.0.0.1:54323 · Local email inbox (sign-up confirmations): http://127.0.0.1:54324

## Database changes
```bash
make db-new name=add_reels     # creates supabase/migrations/<timestamp>_add_reels.sql
make db-reset                  # re-applies all migrations + seed locally
```
Never edit a migration that has been merged; add a new one.

## Before pushing
`make check` runs what CI runs (except the database and image jobs).
