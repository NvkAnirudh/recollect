# Changelog

All notable changes to Recollect are recorded here, in the same PR as the change
(see [docs/process/sdlc.md §4](docs/process/sdlc.md)). Format:
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versions will follow
[Semantic Versioning](https://semver.org/) from the first release.

## [Unreleased]

### Added
- Recollect GitHub Project board (Status, Level, Phase, Priority, Size) with the full backlog; board usage and CLI cheatsheet in the SDLC guide ([#10](https://github.com/NvkAnirudh/recollect/issues/10))
- SDLC process: Epic → Feature → Story issues with sub-issues, a project board, docs-with-every-change rule, `AGENTS.md` for all AI agents, and a PR hygiene check requiring a linked issue and CHANGELOG entry ([#9](https://github.com/NvkAnirudh/recollect/issues/9))
- Documentation index, architecture overview, API and configuration references, and the CI and security runbook ([#9](https://github.com/NvkAnirudh/recollect/issues/9))
- Monorepo scaffold: FastAPI backend with Supabase JWT auth, `/health` and `/api/v1/me`; Next.js frontend with typed API client; Supabase baseline migration (pgvector, `profiles` with RLS); CI, security scanning, pre-commit hooks, Dependabot, ADRs 0001–0004 ([#2](https://github.com/NvkAnirudh/recollect/pull/2))
- v1 design spec ([#1](https://github.com/NvkAnirudh/recollect/pull/1))

### Changed
- Backend runs on Python 3.14 everywhere: Docker image, CI, tooling targets ([#3](https://github.com/NvkAnirudh/recollect/pull/3))

### Security
- Branch protection on `main`, secret scanning with push protection, Dependabot alerts and security updates, all GitHub Actions pinned to commit SHAs ([#2](https://github.com/NvkAnirudh/recollect/pull/2))
