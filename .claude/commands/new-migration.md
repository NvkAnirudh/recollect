---
description: Create a new Supabase SQL migration following project rules
argument-hint: "<snake_case_name> <what it should do>"
---

Create a migration for: $ARGUMENTS

1. `supabase migration new <snake_case_name>`. Never edit an existing migration that is already on `main`.
2. Write idempotent-where-possible SQL. Every new table must:
   - have a `uuid` primary key (`gen_random_uuid()`) unless it's a join/queue table with a documented reason,
   - include `user_id uuid not null references auth.users on delete cascade` if it holds user data,
   - `enable row level security` with owner-only policies using `(select auth.uid()) = user_id`,
   - add indexes for the queries the spec describes.
3. `make db-reset`, then `supabase db lint --local --level warning --fail-on warning`.
4. Add or extend integration tests that exercise the new schema.
