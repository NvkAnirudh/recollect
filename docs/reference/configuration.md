# Configuration reference

Every setting, per app. Update this file and the matching `.env.example` in any PR that adds or
changes a setting. Secrets are never committed: locally they live in git-ignored `.env` files,
and in deployed environments in the platform's secret settings (Railway, Vercel, GitHub).

## Backend (`backend/.env`, read by `recollect.core.config.Settings`)

| Variable | Default (local) | Notes |
|---|---|---|
| `ENVIRONMENT` | `development` | `development`, `test`, `staging` or `production`. Staging and production are validated strictly |
| `DATABASE_URL` | `postgresql://postgres:postgres@127.0.0.1:54322/postgres` | Local Supabase DB. Deployed: must not be localhost. **Secret** |
| `SUPABASE_URL` | `http://127.0.0.1:54321` | Deployed: must be `https://`. Used to derive the JWT issuer and JWKS URL |
| `SUPABASE_JWT_SECRET` | unset | **Local only**: the JWT secret from `supabase status`. Must be unset when deployed (JWKS is used). **Secret** |
| `SUPABASE_JWT_AUDIENCE` | `authenticated` | |
| `LOG_LEVEL` | `INFO` | |
| `LOG_FORMAT` | `console` | Must be `json` when deployed |
| `CORS_ORIGINS` | `["http://localhost:3000"]` | JSON list. Deployed: real origins only, no `*` or localhost |
| `RATE_LIMIT` | `100/minute` | slowapi syntax, per client IP |
| `API_V1_PREFIX` | `/api/v1` | |

## Frontend (`frontend/.env.local`, validated in `src/lib/env.ts`)

`NEXT_PUBLIC_*` values are embedded in the browser bundle, so **never put secrets in them**.

| Variable | Local value | Notes |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Backend base URL |
| `NEXT_PUBLIC_SUPABASE_URL` | `http://127.0.0.1:54321` | |
| `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY` | from `supabase status` | Publishable (anon) key, safe for browsers |

## Supabase (`supabase/config.toml`)

Local stack settings, hardened from the defaults: `site_url` is `http://localhost:3000`, the
password minimum is 10 characters with lower/upper/digits, email confirmation is required, and
password changes need recent sign-in. Mirror these in the hosted project ([#12](https://github.com/NvkAnirudh/recollect/issues/12)).

## CI / GitHub

No repository secrets are needed yet. Workflows use only the built-in `GITHUB_TOKEN`, with
least-privilege `permissions:` per job.
