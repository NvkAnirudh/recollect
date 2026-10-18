# Recollect v1 — Simplified Backend Design

**Date:** 2026-10-18
**Status:** Draft, awaiting review
**Repo:** `recollect-server` (new). The old `recollect-backend` repo is kept read-only for reference; usable parts are copied over as listed in section 9.

## 1. Goal

Save an Instagram Reel link from your phone, and later find it again with a
natural-language search such as "pasta recipe reel I saved last week". The
search must cover what is **said**, what is **shown on screen**, and the
**caption**, and it returns the reel link.

Single user for now, but built so others can use it later: every row is owned
by a user, every query is scoped to that user, and nothing assumes a single
user.

### Success criteria

- Sharing a reel to the Slack bot from a phone gets an acknowledgement within
  3 seconds, and the reel is searchable within 2 minutes.
- On a fixed evaluation set (≥20 saved reels, ≥30 queries), the correct reel
  appears in the top 5 for ≥90% of queries. This includes queries with time
  phrases ("last week", "yesterday", "in September").
- A reel whose content is only on-screen text over music (no speech) can be
  found by words in that text.

### Non-goals for v1

WhatsApp, the browser extension, platforms other than Instagram, the chat
agent, tags and collections, the waitlist, billing, Slack app distribution to
other workspaces, and migrating old data.

## 2. Decisions already made

| Decision | Choice |
|---|---|
| Hosting | Fully cloud: Railway (Python services), Supabase (Postgres + Auth + Storage) |
| Saving from phone | Slack bot in v1 (share reel → DM the bot) |
| Content understanding | Gemini, one multimodal call per reel (transcript + on-screen text + visuals). No separate OCR unless the Phase 1 spike shows it's needed |
| Reel fetcher | Keep Bright Data, behind a `Fetcher` interface |
| Existing data | Start fresh (new Supabase project) |
| Platforms | Instagram only |
| Web UI | New minimal repo (`recollect-web`) with its own spec; this spec defines the API it uses |

## 3. Architecture

```
 Phone: Instagram → Share → Slack DM ─┐
 Web app (recollect-web) ─────────────┤
                                      ▼
                            ┌──────────────────┐
                            │  api  (FastAPI)  │── Gemini (query parsing, query embedding)
                            │  REST + /slack/* │
                            └────────┬─────────┘
                                     │ insert reel + job
                                     ▼
                     ┌───────────────────────────────┐
                     │ Supabase Postgres (+pgvector) │◀── Supabase Auth (JWT)
                     │ reels · jobs · slack_links    │
                     └───────────────┬───────────────┘
                                     │ claim job (FOR UPDATE SKIP LOCKED)
                                     ▼
                            ┌──────────────────┐
                            │ worker (Python)  │── Bright Data (metadata + video URL)
                            │                  │── Gemini (video understanding, embedding)
                            └──────────────────┘── Supabase Storage (thumbnail)
                                                ── Slack (post "saved ✓" reply)
```

There are two deployables, built from **one Docker image** with different start
commands: `api` and `worker`. There is no RabbitMQ, Redis, Qdrant or gateway.

## 4. Components

The code is one package, `recollect/`. Each module has a single job and a small
interface.

| Module | Responsibility | Depends on |
|---|---|---|
| `config.py` | Typed settings from env (pydantic-settings) | — |
| `db/` | Connection pool (psycopg 3, async) and repository functions (`create_reel`, `claim_job`, `mark_ready`, `search`…). No SQL elsewhere | Postgres |
| `auth.py` | Verify Supabase JWT locally via the project's JWKS and return `user_id`. FastAPI dependency | Supabase JWKS |
| `instagram.py` | Validate and normalise reel URLs, and extract the shortcode (taken from the current `url_parser.py`) | — |
| `fetchers/base.py` | `Fetcher` protocol: `fetch(url) -> FetchedReel(caption, author, posted_at, video_url, thumbnail_url, duration)` | — |
| `fetchers/brightdata.py` | Bright Data implementation (taken from the current scraper, Instagram only) | Bright Data API |
| `understanding/gemini.py` | `understand(video_path, caption) -> ReelUnderstanding` with structured output | Gemini API |
| `embeddings.py` | `embed_document(text)`, `embed_query(text)`. Gemini embedding model, fixed dimension (768) | Gemini API |
| `search/query_parser.py` | `parse(query, now, tz) -> ParsedQuery(text, saved_from, saved_to)` | Gemini API |
| `search/service.py` | Parse → embed → call the `search_reels` SQL function → shape results | db, embeddings, parser |
| `pipeline.py` | The per-reel processing steps (section 5.2) | fetcher, understanding, embeddings, db, storage |
| `worker/main.py` | Loop: claim job → run pipeline → retry/fail. Graceful shutdown | db, pipeline |
| `api/main.py`, `api/routes.py` | REST endpoints (section 6) | auth, db, search |
| `slack/` | Events + slash command handlers, signature verification, account linking, replies | db, search, Slack Web API |

`ReelUnderstanding` (the Gemini structured output):

```
transcript: str            # spoken words, verbatim-ish; "" if none
on_screen_text: str        # all legible overlay text, in order
visual_description: str    # what is shown: setting, objects, actions, people
summary: str               # 1–2 sentences
topics: list[str]          # 3–8 short keywords ("pasta", "carbonara", "recipe")
language: str              # ISO code of the main language
```

## 5. Data flow

### 5.1 Save

1. A user saves through `POST /reels {url}` (web) or a Slack DM containing a
   reel URL.
2. The API validates and normalises the URL. If `(user_id, shortcode)` already
   exists, it returns the existing reel. Saving the same reel twice is not an
   error.
3. Otherwise it inserts a `reels` row (`status=pending`, `saved_at=now()`) and a
   `jobs` row in one transaction, then returns `202` with the reel. Slack gets
   "Got it, processing…" within 3 seconds.

### 5.2 Process (worker)

1. Claim the oldest due job with `SELECT … FOR UPDATE SKIP LOCKED` and set the
   reel to `processing`.
2. **Fetch:** Bright Data → caption, author, posted_at, video URL, thumbnail
   URL. Instagram CDN URLs expire, so steps 3–4 run straight away.
3. **Thumbnail:** download it and upload to Supabase Storage at
   `thumbnails/{user_id}/{reel_id}.jpg`.
4. **Understand:** download the video to a temp file, upload it to the Gemini
   Files API, call the model with the caption as context, parse the structured
   output, then delete the temp file and the Gemini file.
5. **Index:** build `search_text` = caption + transcript + on-screen text +
   visual description + summary + topics. Embed it and store the vector plus
   the `tsvector`.
6. Set the reel to `ready`. If it was saved from Slack, reply in the thread:
   "Saved: <summary>".

**Failure handling:** each job has `attempts` and `run_after`. A failed step
retries with backoff (1 min, 5 min, 30 min); after 3 attempts the reel is
`failed` with a short `error` message, and the Slack user is told. Errors are
classified: a deleted or private reel fails at once (no retries), while
timeouts and 5xx responses are retried. A job stuck in `processing` for more
than 15 minutes (worker crashed) becomes claimable again.

### 5.3 Search

1. `GET /search?q=pasta recipe I saved last week`, or the `/recollect pasta
   recipe last week` slash command.
2. **Parse:** Gemini Flash gets the query, the current time and the user's
   timezone, and returns `{text: "pasta recipe", saved_from, saved_to}`. Dates
   are resolved in the user's timezone: "last week" is the previous Mon–Sun and
   "yesterday" is the previous calendar day. If parsing fails or times out
   (2 s), the whole query is used as text with no date filter.
3. **Retrieve:** the SQL function `search_reels(user_id, query_embedding,
   query_text, saved_from, saved_to, k)` runs vector cosine search (pgvector
   HNSW) and Postgres full-text search (`websearch_to_tsquery`), both filtered
   by user and date, and merges them with reciprocal rank fusion (k=60). It
   returns the top `k` (default 10).
4. **Shape:** each result has the reel URL, thumbnail URL, author, saved_at,
   summary, and a **match snippet**: the transcript or on-screen-text passage
   with the most query-term hits, or the summary if none.
5. **Empty result with a date filter:** run once more without the date filter
   and mark the results `date_relaxed: true`, so the UI can say "Nothing from
   last week; here are the closest matches."

Times are stored in UTC (`timestamptz`). The user's timezone comes from the
`X-Timezone` header on web requests and from Slack's `users.info` for Slack
requests, and is saved on the profile.

## 6. API (contract for `recollect-web`)

All endpoints except `/health` and `/slack/*` need `Authorization: Bearer
<supabase access token>`.

| Method | Path | Body / query | Response |
|---|---|---|---|
| GET | `/health` | — | `{ok: true}` |
| POST | `/reels` | `{url}` | `202 Reel` (or `200 Reel` if it already exists) |
| GET | `/reels` | `?status=&cursor=&limit=` | `{items: Reel[], next_cursor}`, newest saved first |
| GET | `/reels/{id}` | — | `Reel` (includes the full understanding) |
| DELETE | `/reels/{id}` | — | `204` |
| POST | `/reels/{id}/retry` | — | `202` (failed reels only) |
| GET | `/search` | `?q=&limit=` | `{query: ParsedQuery, date_relaxed: bool, results: SearchResult[]}` |
| POST | `/slack/link-code` | — | `{code, expires_at}` (for linking a Slack account) |
| POST | `/slack/events` | Slack Events API | Slack-signed |
| POST | `/slack/commands` | Slack slash command | Slack-signed |

`Reel`: `id, url, shortcode, status, error, author, caption, thumbnail_url,
posted_at, saved_at, summary, topics`.

Errors use one shape: `{error: {code, message}}`. Every query includes
`user_id = <caller>`. Postgres row-level security is turned on as a backstop,
even though the services connect with a server role.

## 7. Slack bot

- **One Slack app** in your workspace (single-workspace install for v1, using a
  bot token from env). Scopes: `chat:write`, `im:history`, `users:read`, plus
  the `/recollect` command.
- **Account linking:** the web app shows a 6-digit code from
  `POST /slack/link-code`, valid for 10 minutes. You DM the bot `link 123456`,
  which saves `(team_id, slack_user_id) → user_id` in `slack_links`. Messages
  from Slack users who aren't linked get a "link your account" reply.
- **Save:** any DM containing an Instagram reel URL saves it (several URLs mean
  several saves). The bot replies in a thread, then posts "Saved: …" or the
  failure reason.
- **Search:** `/recollect <query>`, or a DM that contains no URL, returns the
  top 5 results as Block Kit: thumbnail, summary, snippet and link. Only you can
  see slash-command results.
- **Security:** every request's Slack signature is verified (signing secret,
  5-minute timestamp window). Slack event retries are de-duplicated by
  `event_id`.

Multi-workspace OAuth install is out of scope, but `slack_links` stores
`team_id` so it can be added later without a migration.

## 8. Data model (fresh migrations in `supabase/migrations/`)

```sql
create extension if not exists vector;

create table profiles (
  user_id uuid primary key references auth.users on delete cascade,
  timezone text not null default 'UTC',
  created_at timestamptz not null default now()
);

create table reels (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users on delete cascade,
  url text not null,
  shortcode text not null,
  status text not null default 'pending'
    check (status in ('pending','processing','ready','failed')),
  error text,
  author text, caption text, posted_at timestamptz, duration_s int,
  thumbnail_path text,
  understanding jsonb,                 -- ReelUnderstanding
  summary text, topics text[],
  search_text text,
  search_tsv tsvector generated always as (to_tsvector('simple', coalesce(search_text,''))) stored,
  embedding vector(768),
  source text not null check (source in ('web','slack')),
  slack_channel text, slack_thread_ts text,   -- where to reply when done
  saved_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (user_id, shortcode)
);
create index on reels (user_id, saved_at desc);
create index on reels using gin (search_tsv);
create index on reels using hnsw (embedding vector_cosine_ops);

create table jobs (
  id bigint generated always as identity primary key,
  reel_id uuid not null references reels on delete cascade,
  attempts int not null default 0,
  run_after timestamptz not null default now(),
  locked_at timestamptz,
  last_error text
);
create index on jobs (run_after) where locked_at is null;

create table slack_links (
  team_id text not null, slack_user_id text not null,
  user_id uuid not null references auth.users on delete cascade,
  created_at timestamptz not null default now(),
  primary key (team_id, slack_user_id)
);
create table slack_link_codes (
  code text primary key, user_id uuid not null references auth.users on delete cascade,
  expires_at timestamptz not null
);
create table slack_events_seen (event_id text primary key, seen_at timestamptz not null default now());
```

The `'simple'` text config is used instead of `'english'` so non-English and
mixed-language reels still match. The `search_reels` SQL function lives in the
same migration set.

## 9. Repo layout, and what to copy from `recollect-backend`

This is a fresh repo. The old repo has 7 services, RabbitMQ, Qdrant, Redis,
LinkedIn processing, the chat agent, waitlist and WhatsApp; it is left as it is
for reference. Nothing is moved wholesale. The parts below are copied and
adapted where they save time:

| From `recollect-backend` | To | Adaptation |
|---|---|---|
| `services/video-ingest/url_parser.py` | `recollect/instagram.py` | Instagram only |
| `services/video-ingest/bright_data_scraper.py` | `recollect/fetchers/brightdata.py` | Instagram only; implement the `Fetcher` protocol; drop LinkedIn/TikTok |
| `shared/auth/dependencies.py` | `recollect/auth.py` | Verify JWTs locally via JWKS instead of calling `getUser()`; remove the `X-User-ID` header path |
| `services/*/railway.toml`, `Dockerfile` | root `Dockerfile`, `railway.toml` | One image, two start commands |

Layout:

```
recollect-server/
  recollect/            # package (section 4)
  supabase/migrations/  # fresh schema (section 8)
  tests/
    unit/               # fetcher/gemini/slack mocked
    integration/        # real Postgres+pgvector (docker), mocked externals
    eval/               # search quality set: reels fixtures + queries + expected
  scripts/              # spike + eval runners
  Dockerfile            # one image; CMD chosen per Railway service
  pyproject.toml        # uv-managed, proper package (no sys.path hacks)
  .github/workflows/ci.yml
```

**Secrets:** nothing is copied from the old repo's tests or scripts, which
contain hard-coded credentials. The old Supabase project's test user password
and the RabbitMQ password must still be rotated, or those services shut down,
because they stay in the old repo's git history. `.env.example` lists every
variable and contains no values.

## 10. Phases

| # | Phase | Done when |
|---|---|---|
| 0 | **Skeleton:** package layout, CI (lint + tests), new Supabase project, migrations applied, `.env.example` | CI green on an empty skeleton; schema applied |
| 1 | **Spike** (throwaway scripts): (a) Gemini on ~10 real reels including ≥4 text-heavy, music-only ones, comparing 1 fps vs a higher fps; (b) Bright Data fetch from a Railway container | On-screen text captured well enough (or OCR is added to scope); chosen Gemini model and fps recorded in this spec |
| 2 | **Saving pipeline:** API save endpoints, job queue, worker, fetcher, Gemini understanding, thumbnail, indexing, retries | Saving a real reel through the API reaches `ready`; failure paths tested |
| 3 | **Search:** query parser, `search_reels`, `/search`, eval set | Eval reaches ≥90% top-5 |
| 4 | **Slack bot:** linking, save from DM, `/recollect` search, completion replies | Share from the phone → found by `/recollect` |
| 5 | **Deploy:** Railway `api` + `worker`, env, health checks | Phase 4 check passes against production |
| — | `recollect-web` (separate spec), started after Phase 3 against this API | — |

## 11. Testing

- **Unit:** URL parsing, the query parser's date resolution (with a fixed clock
  and timezone: "last week" on a Monday, a Sunday, and across a year
  boundary), Slack signature verification, retry classification, and snippet
  selection. External APIs are mocked.
- **Integration:** a real Postgres with pgvector in docker (CI service
  container). Covers save → job → pipeline (fetcher and Gemini stubbed with
  recorded fixtures) → `ready` → `search_reels` returns it. Also covers user
  isolation: user B never sees user A's reels.
- **Search eval:** `tests/eval/` stores recorded `ReelUnderstanding` fixtures
  for ≥20 real reels and ≥30 labelled queries. `scripts/eval_search.py` reports
  top-1/top-5 hit rate. It runs on demand, not in CI, because it calls
  embeddings.
- TDD is used for the pipeline, the parser and the SQL function.

## 12. Risks

| Risk | Mitigation |
|---|---|
| Bright Data breaks or gets expensive | `Fetcher` interface; Apify or yt-dlp+proxy can be dropped in |
| Gemini misses brief on-screen text | Phase 1 spike; raise fps or add an OCR pass |
| Instagram CDN URLs expire before processing | Fetch and process in the same job step, and re-fetch on retry |
| Gemini model names or prices change | Model IDs in config, pinned after the spike |
| Slack requires a 3 s ack | Handlers only write to the DB and enqueue; all slow work happens in the worker |
