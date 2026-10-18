---
description: Commit current work on a branch, push, and open a PR that follows the SDLC process (never on main)
argument-hint: "[branch-name, e.g. feat/reel-save]"
---

Ship the current changes as a pull request, following `docs/process/sdlc.md`.

1. Identify the issue this work belongs to (ask, or search with `gh issue list`). If none exists,
   create it first with `/new-work`. Never ship unlinked work.
2. If on `main`, create and switch to the branch `$ARGUMENTS` (ask for a name if none given).
3. Check documentation per sdlc.md §4. `CHANGELOG.md` must have a line under `[Unreleased]`
   linking the issue/PR, and any API/config/architecture/ADR/spec/runbook doc the change
   affects must be updated. Make the doc updates now if they're missing.
4. Run `make check`. If anything fails, stop and report; do not commit failing work.
5. Review `git status`/`git diff`. Stage only related files, and never `.env*` other than `.env.example`.
6. Commit with a Conventional Commit message (`type(scope): summary`, at most 72 chars, plus a body explaining why).
7. `git push -u origin HEAD`, then `gh pr create --base main` with a Conventional Commit title and the
   PR template filled in, starting with `Closes #<issue>`.
8. Move the issue to **In review** on the Recollect board.
9. Watch CI with `gh pr checks --watch` and report the result and the PR URL.
