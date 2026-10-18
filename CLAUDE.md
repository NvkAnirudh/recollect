# CLAUDE.md

All project instructions live in `AGENTS.md` (shared with other AI agents), imported here:

@AGENTS.md

## Claude Code specifics

- `/ship [branch]`: run checks, commit, push, open a PR that follows `docs/process/sdlc.md`.
- `/new-work <description>`: place new work in the Epic → Feature → Story hierarchy and create the issues.
- `/new-migration <name> <purpose>`: create a migration that follows the schema rules.
- Before ending a session that changed code, confirm the CHANGELOG and the docs required by
  `docs/process/sdlc.md` §4 are updated, and that the issue and board are current.
