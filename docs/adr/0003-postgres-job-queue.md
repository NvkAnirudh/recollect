# 0003. Postgres table as the job queue

Date: 2026-10-18 · Status: Accepted

## Context
Reel processing (fetch → Gemini → embed) takes 10–60s and must not block the API or Slack's
3-second acknowledgement window. The previous system used RabbitMQ.

## Decision
A `jobs` table, claimed with `SELECT … FOR UPDATE SKIP LOCKED`, with `attempts`, `run_after`
and `locked_at` columns for retries, backoff and recovering stuck jobs.

## Consequences
- There's one less service to run, secure and pay for. The job is inserted in the same
  transaction as the reel, so a reel can never be saved without its job.
- This is fine to roughly hundreds of jobs per minute. Revisit (e.g. pgmq, or a hosted queue) if throughput grows by orders of magnitude.
