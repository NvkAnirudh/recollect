# CI and security checks

What runs on every PR, what each check protects against, and what to do when one fails.
Update this file when a check, threshold or exception changes.

## Required checks on `main`

| Check | Workflow | What it does | If it fails |
|---|---|---|---|
| **CI OK** | `ci.yml` | Passes only if all CI jobs below pass | Open the failing job |
| Backend | `ci.yml` | `uv sync --locked`, ruff format/lint, pyright strict, pytest with an 80% coverage gate | Run `make check-backend` locally |
| Frontend | `ci.yml` | `--frozen-lockfile` install, Prettier, ESLint (0 warnings), `next typegen` + tsc, vitest with an 80% gate, `next build` | Run `make check-frontend` |
| Database | `ci.yml` | `supabase db start` applies every migration; `supabase db lint` fails on warnings | `make db-reset`, then `supabase db lint --local` |
| Backend image | `ci.yml` | Builds the Docker image; Trivy fails on fixable HIGH/CRITICAL CVEs | Bump the dependency or base image; see "Exceptions" |
| Workflow lint | `ci.yml` | actionlint on `.github/workflows` | Run `actionlint` |
| **Secret scan (gitleaks)** | `security.yml` | Scans the full git history for secrets | **Rotate the secret first** (SECURITY.md), then remove it |
| **Dependency review** | `security.yml` | Blocks PRs that add dependencies with HIGH+ advisories | Upgrade, or add a documented exception |
| **Conventional Commit title** | `pr-title.yml` | PR title must be `type(scope): summary` | Edit the PR title |
| **PR hygiene** | `pr-hygiene.yml` | PR body links an issue (`Closes #n`/`Fixes #n`/`Refs #n`), and `CHANGELOG.md` is updated when code/config changed | Add the link or the CHANGELOG line, or the `no-changelog` label if justified (docs-only) |

Not required, but run on every PR and on a weekly schedule:

| Check | What it does |
|---|---|
| CodeQL (Python, TS, Actions) | Static security analysis (`security-extended` queries). Findings appear under Security → Code scanning |
| Dependency audit | `pip-audit` on backend runtime deps, `pnpm audit --prod` (high+) |

Dependabot opens grouped weekly update PRs (uv, npm, Docker, Actions) and immediate security PRs.
Review them like any PR. Runtime version bumps (Python, Node) must update every pin together
(see AGENTS.md).

## Exceptions (allowlisted advisories)

An advisory may be allowlisted only when there is no fix and it can't affect production. Each
exception lives next to its check with a comment giving the reason and the condition for removing
it, and gets a tracking issue.

| Advisory | Where | Reason | Tracking |
|---|---|---|---|
| GHSA-vfj7-8cjw-p6xm (`braces` ≤3.0.3) | `security.yml` → dependency-review `allow-ghsas` | No patched version; dev-only, via `eslint-config-next` → `fast-glob` | [#15](https://github.com/NvkAnirudh/recollect/issues/15) |

## Local equivalents

`pre-commit` (installed by `make setup`) runs gitleaks, private-key detection, ruff, Prettier,
ESLint, actionlint and the Conventional Commit message check on each commit, and blocks commits
to `main`. `make check` runs the CI jobs except Database and Backend image.
