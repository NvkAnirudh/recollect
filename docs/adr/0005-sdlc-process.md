# 0005. SDLC process: issue hierarchy, docs with every change, rules for all agents

Date: 2026-10-18 · Status: Accepted

## Context
Work on Recollect is done by the owner and by several AI agents across many sessions. Agents
lose conversation context between sessions, so process rules agreed in one conversation are
forgotten unless they live in the repo and are enforced.

## Decision
- **Tracking:** GitHub issues in an Epic → Feature → Story hierarchy using native sub-issues
  and `type:*`/`area:*` labels, on a GitHub Project board. One story = one PR.
- **Documentation:** every PR updates `CHANGELOG.md` plus the docs its change type requires
  (`docs/process/sdlc.md` §4).
- **Agent instructions:** the mandatory rules live in `AGENTS.md`, read by most AI agents.
  `CLAUDE.md` imports it, and `.github/copilot-instructions.md` points to it. The full process is in `docs/process/sdlc.md`.
- **Enforcement:** a required `PR hygiene` check fails PRs with no linked issue, or with
  code/config changes but no CHANGELOG entry (unless labelled `no-changelog`).

## Consequences
- Rules survive across sessions and agents because they're in the repo and checked by CI, not in chat history.
- Small overhead per PR (an issue link and a CHANGELOG line). Dependabot PRs are exempt.
- The board needs upkeep; closing issues via `Closes #n` keeps it mostly automatic.
