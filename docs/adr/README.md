# Architecture Decision Records

One file per significant decision: `NNNN-short-title.md`, never edited after acceptance;
a later ADR supersedes an earlier one. Template:

```markdown
# NNNN. Title
Date: YYYY-MM-DD · Status: Proposed | Accepted | Superseded by NNNN

## Context
## Decision
## Consequences
```

| ADR | Decision |
|---|---|
| [0001](0001-monorepo.md) | Monorepo for backend, frontend and database |
| [0002](0002-supabase-sql-migrations.md) | Supabase for Postgres/Auth/Storage, plain SQL migrations, psycopg |
| [0003](0003-postgres-job-queue.md) | Postgres table as the job queue (no RabbitMQ) |
| [0004](0004-public-repo-security-baseline.md) | Public repo and the security baseline it enables |
