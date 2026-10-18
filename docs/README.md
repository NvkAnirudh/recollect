# Documentation

Start with [`AGENTS.md`](../AGENTS.md) (rules for every contributor) and the
[SDLC process](process/sdlc.md). Every PR updates the docs its change type requires
([sdlc.md §4](process/sdlc.md)); add any new document to this index.

| Area | Document | What's in it |
|---|---|---|
| Process | [process/sdlc.md](process/sdlc.md) | Issues (Epic → Feature → Story), board, branching, PRs, documentation rules, definition of done |
| Product | [superpowers/specs/2026-10-18-recollect-v1-design.md](superpowers/specs/2026-10-18-recollect-v1-design.md) | v1 scope, design, phases |
| Architecture | [architecture/overview.md](architecture/overview.md) | Components, request flow, auth, data model, as built today |
| Decisions | [adr/](adr/) | Architecture Decision Records (0001–0006) |
| Spikes | [spikes/](spikes/) | Time-boxed investigations: method, results, findings ([Gemini understanding](spikes/2026-10-19-gemini-understanding.md)) |
| Reference | [reference/api.md](reference/api.md) | HTTP endpoints, auth, error shape |
| Reference | [reference/configuration.md](reference/configuration.md) | Every environment variable, per app |
| Runbooks | [runbooks/local-development.md](runbooks/local-development.md) | Set up and run everything locally |
| Runbooks | [runbooks/ci-and-security.md](runbooks/ci-and-security.md) | What each CI/security check does and how to fix failures |
| History | [../CHANGELOG.md](../CHANGELOG.md) | Every change, per PR |
| Security | [../SECURITY.md](../SECURITY.md) | Reporting, leaked-secret procedure, known gaps |
