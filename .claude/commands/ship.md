---
description: Commit current work on a branch, push, and open a PR (never on main)
argument-hint: "[branch-name, e.g. feat/reel-save]"
---

Ship the current changes as a pull request, following CONTRIBUTING.md.

1. If on `main`, create and switch to the branch `$ARGUMENTS` (ask for a name if none given). Never commit to `main`.
2. Run `make check`. If anything fails, stop and report; do not commit failing work.
3. Review `git status` and `git diff`. Stage only files related to this change, never `.env*` files
   other than `.env.example`. Ask if unrelated changes are present.
4. Commit with a Conventional Commit message (`type(scope): summary` ≤72 chars, with a body explaining why).
5. `git push -u origin HEAD`.
6. `gh pr create --base main` with a Conventional Commit title and the PR template filled in
   (what/why, how tested, checklist).
7. Print the PR URL, then watch CI with `gh pr checks --watch` and report the result.
