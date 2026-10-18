# SDLC process

This is how all work on Recollect is planned, built, documented and shipped. It applies to
every contributor, human or AI agent, in every session. `AGENTS.md` (which `CLAUDE.md` imports)
summarises the mandatory parts; this document is the full version.

## 1. Plan: every change starts as an issue

Work is tracked as GitHub issues in a three-level hierarchy, linked with GitHub's native
**sub-issues**, and shown on the **Recollect** GitHub Project board.

| Level | Label | Size | Is | Example |
|---|---|---|---|---|
| **Epic** | `type:epic` | weeks | A large outcome, usually one spec phase | Natural-language search |
| **Feature** | `type:feature` | days | A capability inside an epic | Query parsing |
| **Story** | `type:story` | ≤1 day, **one PR** | The smallest shippable slice | Parser fallback on timeout |

Also used:
- `type:task`: chores with no user-facing behaviour (upkeep, tooling). Parent it under the closest feature, or leave it standalone if none fits.
- `type:bug`: something broken. Standalone, or under the feature it breaks.
- `type:spike`: a time-boxed investigation whose output is a decision (ADR/spec update), not production code.

Every issue also gets one or more `area:*` labels (`backend`, `frontend`, `db`, `slack`, `infra`, `docs`). Add `security` when relevant.

### Choosing the level for new work

1. **Does it fit an existing story?** Then use that story.
2. **Does it belong to an existing feature?** Then create a story under it.
3. **Is it a new capability inside an existing epic?** Then create a feature with its stories.
4. **Is it a new large outcome?** Then create an epic. Usually a spec change comes first.
5. **Is it a one-off chore or bug?** Then create a `type:task` or `type:bug`, with a parent if one fits.

Keep stories small enough for one reviewable PR. If a story needs two PRs, split it.
Later features may have no stories until they are planned; create stories when the feature is
about to start (e.g. after its spec is approved), not months ahead.

### Issue content

Use the issue templates (Epic, Feature, Story, Bug). Every issue needs:
- **What/Outcome:** one or two sentences.
- **Acceptance criteria:** checkboxes that are testable.
- **Reference:** the spec section, ADR or parent issue.
- **Docs to update** (stories): which docs this change must touch (see §4).

### Linking a sub-issue

In the GitHub UI, open the parent issue and use **Create sub-issue** or **Add existing issue**. With the CLI:

```bash
child_id=$(gh api repos/NvkAnirudh/recollect/issues/<child> --jq .id)
gh api -X POST repos/NvkAnirudh/recollect/issues/<parent>/sub_issues -F sub_issue_id=$child_id
```

## 2. Track: the project board

**[Recollect project](https://github.com/users/NvkAnirudh/projects/4)** (user project #4, owner
`NvkAnirudh`, linked to the repo, public) is the single view of all work.

| Field | Values |
|---|---|
| Status | Backlog → Ready → In progress → In review → Done |
| Level | Epic, Feature, Story, Task, Bug, Spike (mirrors the `type:*` label; GitHub reserves the name "Type") |
| Phase | 0 Foundation · 1 Spike · 2 Ingestion · 3 Search · 4 Slack · 5 Deploy · Web |
| Priority | P0 (now) · P1 (next) · P2 (later) |
| Size | XS · S · M · L (stories should be S or smaller) |

Rules:
- Every issue is on the board, with Level, Phase and Priority set (Size too for stories).
- Move an item to **In progress** when work starts and to **In review** when its PR opens. Closing the issue (via the merged PR) moves it to **Done**.
- A parent is closed when all its children are closed.

### CLI cheatsheet

```bash
# add an issue (prints the item id)
gh project item-add 4 --owner NvkAnirudh --url https://github.com/NvkAnirudh/recollect/issues/<n> --format json --jq .id

# field and option ids (Status, Level, Phase, Priority, Size)
gh project field-list 4 --owner NvkAnirudh --format json

# set a single-select field on an item
gh project item-edit --project-id PVT_kwHOAcOg8M4Bnn-D --id <item-id> \
  --field-id <field-id> --single-select-option-id <option-id>
```

The `gh` token needs the `project` scope (`gh auth refresh -h github.com -s project`).

### Set in the GitHub UI (not available through the API)

- **Workflows** (project ⋯ → Workflows): *Auto-add to project* for `repo:NvkAnirudh/recollect is:issue`;
  *Item closed* → Done and *Pull request merged* → Done (on by default).
- **Views:** *Board* (layout Board, columns = Status, filter `-level:Epic`), *Roadmap*
  (Table grouped by Phase, sorted by Priority), *Hierarchy* (Table grouped by Level, with the
  "Parent issue" and "Sub-issues progress" fields shown).

## 3. Build: branch → PR → merge

1. Branch from `main`: `feat/<slug>`, `fix/<slug>`, `docs/<slug>`, `chore/<slug>`.
2. TDD for backend logic: write the failing test first, then make it pass.
3. Run `make check` locally. It runs what CI runs.
4. Open a PR:
   - **Title:** a Conventional Commit (`feat(backend): …`). It becomes the squash commit.
   - **Body:** `Closes #<story>` (or `Fixes #<bug>`). Use `Refs #<n>` when the PR doesn't finish the issue.
   - Fill in the template checklist.
5. Squash-merge once all required checks pass. `main` is protected: no direct pushes, no
   force-pushes, no bypass (admins included).

Required checks on `main`: **CI OK**, **Secret scan (gitleaks)**, **Dependency review**,
**Conventional Commit title**, **PR hygiene** (linked issue + CHANGELOG).

## 4. Document: every change updates the docs in the same PR

Documentation is part of the change, not a follow-up. A PR that changes behaviour without
updating the docs below is incomplete.

| Change | Must update |
|---|---|
| **Any** change to code, config, CI or schema | `CHANGELOG.md` → `## [Unreleased]`, one line per change, linking the PR or issue |
| New/changed API endpoint | `docs/reference/api.md` |
| New/changed env var or setting | `docs/reference/configuration.md` and the relevant `.env.example` |
| New/changed component, data flow or table | `docs/architecture/overview.md` |
| Architectural or technology decision | New ADR in `docs/adr/` (never edit an accepted one; supersede it) |
| Scope, phase or requirement change | The design spec in `docs/superpowers/specs/` |
| New/changed dev workflow, command or deploy step | `docs/runbooks/` and/or `README.md`/`Makefile` help |
| CI, security check or exception change | `docs/runbooks/ci-and-security.md` (and ADR 0004 if the baseline changes) |
| Process change | This file, then `AGENTS.md` if a mandatory rule changed |

`docs/README.md` is the index; add any new doc there.

Exceptions: purely internal refactors and test-only changes still get a CHANGELOG line under
`### Changed`. PRs that are themselves only docs, or dependency bumps by Dependabot, may skip the
CHANGELOG by adding the `no-changelog` label. The PR hygiene check enforces this.

### CHANGELOG format

[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) sections under `## [Unreleased]`:
`Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, `Security`. One line each, written for a reader
of the product, ending with the PR/issue link, e.g.
`- Save a reel from a Slack DM ([#48](https://github.com/NvkAnirudh/recollect/issues/48))`.
When we cut a release, `[Unreleased]` becomes a version heading.

## 5. Definition of done (story)

- [ ] Acceptance criteria met and checked off in the issue
- [ ] Tests added; coverage ≥80%; `make check` green
- [ ] Docs updated per §4, including the CHANGELOG
- [ ] PR merged with `Closes #<story>`; board item is Done
- [ ] No secrets, PII or user content in code, logs, fixtures or screenshots
