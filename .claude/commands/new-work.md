---
description: Place new work in the Epic -> Feature -> Story hierarchy and create the GitHub issues
argument-hint: "<what needs to be done>"
---

Create tracked work for: $ARGUMENTS

Follow `docs/process/sdlc.md` §1–2:

1. Read the current hierarchy: `gh issue list --state open --label type:epic` and
   `--label type:feature`, then the sub-issues of the likely parent
   (`gh api repos/NvkAnirudh/recollect/issues/<n>/sub_issues`).
2. Choose the level (decision list in sdlc.md §1). Prefer extending an existing feature over a new
   one. One story = one PR. Use `type:task`/`type:bug`/`type:spike` where they fit better.
3. Draft the issue(s) using the matching template's sections (What/Outcome, Acceptance criteria,
   Reference, Docs to update), with `type:*` and `area:*` labels. Show the plan to the user
   before creating more than 3 issues.
4. Create them with `gh issue create`, then link each to its parent:
   `gh api -X POST repos/NvkAnirudh/recollect/issues/<parent>/sub_issues -F sub_issue_id=$(gh api repos/NvkAnirudh/recollect/issues/<child> --jq .id)`.
5. Add each to the Recollect board (project 4) and set Level, Phase and Priority (Size for stories),
   using the CLI cheatsheet in sdlc.md §2.
6. Report the created issue numbers and where they sit in the hierarchy.
