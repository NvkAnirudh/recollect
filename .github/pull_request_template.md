Closes #<!-- story/bug number: required (or "Refs #n" if this PR doesn't finish it) -->

## What & why

<!-- One or two sentences. -->

## How it was tested

- [ ] Unit/integration tests added or updated
- [ ] Ran `make check` locally

## Docs (docs/process/sdlc.md §4)

- [ ] `CHANGELOG.md` line under `[Unreleased]`
- [ ] Other docs this change type requires (API, configuration, architecture, ADR, spec, runbook), or n/a

## Checklist

- [ ] PR title is a Conventional Commit (`feat(backend): …`, `fix(frontend): …`)
- [ ] No secrets, tokens, or personal data in code, logs, fixtures, or screenshots
- [ ] New endpoints require auth and scope every query to the caller's `user_id`
- [ ] Schema changes are a new migration in `supabase/migrations/` (never edit an applied one) with RLS enabled
- [ ] Issue acceptance criteria checked off; board item updated
