# 0004. Public repository and security baseline

Date: 2026-10-18 · Status: Accepted

## Context
On GitHub's free plan, branch protection, CodeQL and secret-scanning push protection are
only available for public repositories.

## Decision
The repo is public. Secrets never live in the repo, only in Railway/Vercel/GitHub
environment settings. The security baseline:

| Layer | Control |
|---|---|
| Commit | pre-commit: gitleaks, private-key detection, no direct commits to `main` |
| PR | CI: lint, strict types, tests with ≥80% coverage gate, migration lint, image build + Trivy |
| PR | Security: gitleaks (full history), CodeQL (Python, TS, Actions), pip-audit, pnpm audit, dependency review |
| Repo | Branch protection on `main`: PR required, `CI OK` must pass, linear history, no force-push |
| Repo | Secret scanning + push protection, Dependabot alerts and weekly grouped update PRs |
| Supply chain | Every GitHub Action pinned to a commit SHA; lockfiles enforced (`uv sync --locked`, `--frozen-lockfile`) |
| Runtime | Supabase JWT verification on every route but `/health`; RLS on every table; security headers; explicit CORS; rate limiting; non-root container; no request bodies or query strings in logs |

## Consequences
The code is visible to anyone, so any secret that is committed by mistake must be treated
as compromised and rotated, even if it's removed straight away. See SECURITY.md.
