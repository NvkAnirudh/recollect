# Contributing

1. **Branch from `main`:** `feat/<short-name>`, `fix/<short-name>`, `chore/<short-name>`.
2. **Write the test first** for any backend logic, then make it pass.
3. **Run `make check`** before pushing. It runs the same checks as CI.
4. **Open a PR** using the template. Give it a [Conventional Commit](https://www.conventionalcommits.org) title,
   e.g. `feat(backend): add reel save endpoint`. Scopes: `backend`, `frontend`, `db`, `slack`, `infra`, `deps`, `docs`.
5. **Merge** by squash once `CI OK` is green. The PR title becomes the commit on `main`.

Commits on branches should also follow Conventional Commits; the `commit-msg` hook checks this.

## Definition of done

- Tests cover the change; coverage stays ≥80%.
- No new lint/type warnings, and no `# type: ignore` or `eslint-disable` without a comment explaining why.
- Docs updated: README/runbook for workflow changes, an ADR for architectural decisions,
  the spec for scope changes.
- The security checklist in the PR template is satisfied.
