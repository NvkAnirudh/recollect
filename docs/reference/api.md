# API reference

Base URL: `http://localhost:8000` locally. Interactive docs at `/docs` (disabled in staging and production).
Update this file in any PR that adds or changes an endpoint.

## Conventions

- Every path except `/health` is under `/api/v1` and requires `Authorization: Bearer <Supabase access token>`.
- Optional `X-Timezone: <IANA tz>` header (e.g. `Asia/Kolkata`), sent by the web app and used for date phrases in search.
- Every response carries `X-Request-ID`. Quote it in bug reports.
- Errors always look like this:
  ```json
  {"error": {"code": "unauthorized", "message": "Token expired"}}
  ```
  Codes: `bad_request` 400, `unauthorized` 401, `forbidden` 403, `not_found` 404,
  `method_not_allowed` 405, `conflict` 409, `validation_error` 422 (names fields, never echoes values),
  `rate_limited` 429, `internal_error` 500, plus endpoint-specific codes from `AppError`.

## Endpoints

| Method | Path | Auth | Response |
|---|---|---|---|
| GET | `/health` | none | `200 {"status": "ok"}` |
| GET | `/api/v1/me` | bearer | `200 {"id": "<uuid>", "email": "<string or null>"}`: the caller, so the web app can check its session |

Planned endpoints (reels, search, Slack) are specified in the
[v1 spec §6](../superpowers/specs/2026-10-18-recollect-v1-design.md); each moves here when it ships.
