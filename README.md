# Recollect

Instagram lets you save reels but not search them. Recollect does: share a reel to it, and
later ask *"that pasta recipe I saved last week"*. It searches what was said, what was shown
on screen, and the caption, and gives you the link back.

**Status:** early development. See the [v1 design](docs/superpowers/specs/2026-10-18-recollect-v1-design.md).

## Repository

| Path | |
|---|---|
| [`backend/`](backend/) | FastAPI API, background worker and Slack bot (Python 3.13, uv) |
| [`frontend/`](frontend/) | Web app (Next.js, TypeScript) |
| [`supabase/`](supabase/) | Database migrations and local Supabase config |
| [`docs/`](docs/) | Design specs, [architecture decisions](docs/adr/), [runbooks](docs/runbooks/) |

## Quick start

```bash
make setup   # install deps + git hooks
make db      # local Supabase
make api     # http://localhost:8000/docs
make web     # http://localhost:3000
```

Full instructions: [docs/runbooks/local-development.md](docs/runbooks/local-development.md).
Contributing: [CONTRIBUTING.md](CONTRIBUTING.md) · Security: [SECURITY.md](SECURITY.md)
