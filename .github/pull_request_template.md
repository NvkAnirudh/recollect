## What & why

<!-- One or two sentences. Link the issue: Closes #123 -->

## How it was tested

- [ ] Unit/integration tests added or updated
- [ ] Ran `make check` locally

## Checklist

- [ ] PR title is a Conventional Commit (`feat(backend): …`, `fix(frontend): …`)
- [ ] No secrets, tokens, or personal data in code, logs, fixtures, or screenshots
- [ ] New endpoints require auth and scope every query to the caller's `user_id`
- [ ] Schema changes are a new migration in `supabase/migrations/` (never edit an applied one) with RLS enabled
- [ ] Docs/ADR updated if behaviour or architecture changed
