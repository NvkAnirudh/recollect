# Contributing

The full process is in **[docs/process/sdlc.md](docs/process/sdlc.md)**, and the mandatory rules
are summarised in [AGENTS.md](AGENTS.md). In short:

1. **Start from an issue** in the Epic → Feature → Story hierarchy on the Recollect project
   board. Create one at the right level if it doesn't exist.
2. **Branch from `main`:** `feat/<slug>`, `fix/<slug>`, `docs/<slug>`, `chore/<slug>`.
3. **Write the test first** for backend logic, then make it pass.
4. **Document the change in the same PR:** a `CHANGELOG.md` line plus the docs your change type requires.
5. **Run `make check`**, then open a PR with a Conventional Commit title and `Closes #<issue>`.
6. **Squash-merge** once all required checks are green.

Commits on branches also follow [Conventional Commits](https://www.conventionalcommits.org);
the `commit-msg` hook checks this. See the definition of done in sdlc.md §5.
