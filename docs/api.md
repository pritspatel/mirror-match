# API reference

The canonical machine-readable spec is always `GET /docs` (FastAPI-generated OpenAPI) when the backend is running. This page reflects v1.0.

## Base URL

All endpoints are relative to the backend origin (default `http://localhost:8000`).

---

## `POST /api/v1/compare`

Runs a comparison and returns the diff as JSON. The result is persisted automatically; use the returned `job_id` for exports and sharing.

### Request body

```jsonc
{
  "source_a": { /* adapter config — see Adapters */ },
  "source_b": { /* adapter config — see Adapters */ },
  "options": {
    "ignore_paths":      [],    // list of JSON Pointer prefixes to strip
    "array_as_set":      false, // sort arrays before diffing
    "array_keys":        {},    // map of JSON Pointer → identity field
    "numeric_tolerance": 0.0,   // abs(a-b) ≤ tolerance → equal
    "case_insensitive":  false  // casefold() strings before comparing
  }
}
```

All `options` fields are optional and default to the values shown.

### Response `200 OK`

```json
{
  "job_id":      "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "timestamp":   "2026-04-18T14:56:47+00:00",
  "source_a_id": "prod-item-42",
  "source_b_id": "stg-item-42",
  "summary": {
    "added":    1,
    "removed":  0,
    "modified": 1,
    "total":    2
  },
  "changes": [
    {
      "path":        "/price",
      "change_type": "MODIFIED",
      "value_a":     9.99,
      "value_b":     10.49
    },
    {
      "path":        "/tags/2",
      "change_type": "ADDED",
      "value_a":     null,
      "value_b":     "sale"
    }
  ]
}
```

`change_type` is one of `"ADDED"`, `"REMOVED"`, or `"MODIFIED"`. `value_a` is `null` for `ADDED`; `value_b` is `null` for `REMOVED`.

`path` uses RFC 6901 JSON Pointer syntax. Array elements appear as `/items/0`, `/items/1`, etc. When keyed-array diffing is used, orphan elements (no matching key) fall back to positional under a synthetic `~` sub-path (e.g. `/items/~/0`).

### Error responses

| Status | When |
|--------|------|
| `401 Unauthorized` | `MIRROR_MATCH_AUTH_TOKEN` is set and the `Authorization: Bearer` header is missing or wrong. |
| `422 Unprocessable Entity` | Request body fails Pydantic validation (malformed source config, unknown adapter `type`, etc.). Body contains a `detail` array from FastAPI. |
| `502 Bad Gateway` | The adapter could not reach the upstream (connection refused, DNS failure, ES error). Body: `{"detail": "<message>"}`. |

---

## `POST /api/v1/compare.csv`

Same request body as `/compare`. Returns the diff as `text/csv`.

### CSV format

```
# Generated: 2026-04-18T14:56:47+00:00
# Source A: prod-item-42
# Source B: stg-item-42
Field_Path,Change_Type,Value_in_Doc_A,Value_in_Doc_B
/price,MODIFIED,9.99,10.49
/tags/2,ADDED,,sale
```

Comment rows (`#`) are present for human readability and are skipped by most CSV parsers.

---

## `POST /api/v1/compare.html`

Same request body. Returns a self-contained `text/html` report with inline CSS. No CDN, no external requests — openable offline. Suitable for attaching to bug reports or archiving.

---

## `GET /api/v1/jobs/{job_id}`

Replay a stored diff as JSON. Response schema is identical to `POST /api/v1/compare`.

### Path parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `job_id` | UUID string | Returned by a prior `POST /api/v1/compare`. |

### Responses

| Status | Description |
|--------|-------------|
| `200 OK` | Stored diff as JSON. |
| `404 Not Found` | No job with that ID. Body: `{"detail": "job not found"}`. |
| `401 Unauthorized` | Auth token required (same as `/compare`). |

---

## `GET /api/v1/jobs/{job_id}/csv`

CSV export for a stored job. Same format as `POST /api/v1/compare.csv`.

---

## `GET /api/v1/jobs/{job_id}/html`

HTML export for a stored job. Same format as `POST /api/v1/compare.html`.

---

## `POST /api/v1/sources/test`

Validates that a source config is reachable before running a full comparison. Useful for checking credentials and connectivity.

```json
{ "source": { "type": "http", "url": "https://api.example.com/v1/item/1", "auth": {"kind": "bearer", "token": "…"} } }
```

Returns `{"ok": true, "identifier": "https://api.example.com/v1/item/1"}` on success, or `{"ok": false, "error": "<message>"}` on failure. Never returns a non-2xx status for connectivity failures — check the `ok` field.

---

## `GET /api/v1/healthz`

Liveness probe. Always returns `200` even when `MIRROR_MATCH_AUTH_TOKEN` is set.

```json
{ "status": "ok", "version": "1.0.0" }
```

Use this as the Docker / Kubernetes health check endpoint.

---

## `GET /metrics`

Prometheus text exposition (`text/plain; version=0.0.4`). Always open — no auth required.

### Metrics emitted

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `mirror_match_http_requests_total` | Counter | `method`, `path`, `status` | Incremented after every response. |
| `mirror_match_compare_seconds_count` | Counter | — | Number of `/compare*` calls completed. |
| `mirror_match_compare_seconds_sum` | Counter | — | Cumulative wall-clock seconds spent in compare handlers. |

**Cardinality note:** UUIDs in URL paths are bucketed:

- `/api/v1/jobs/3fa85f64-…` → `path="/api/v1/jobs/{id}"`
- `/api/v1/jobs/3fa85f64-…/csv` → `path="/api/v1/jobs/{id}/csv"`

This prevents label cardinality explosion without losing per-route visibility.

---

## Authentication

When `MIRROR_MATCH_AUTH_TOKEN` is set, all routes except the ones below require `Authorization: Bearer <token>`.

**Always open (no auth):**

- `GET /api/v1/healthz`
- `GET /metrics`
- `GET /docs`
- `GET /openapi.json`
- `GET /redoc`

**Missing or invalid token response:**

```http
HTTP/1.1 401 Unauthorized
content-type: application/json

{"detail": "invalid or missing bearer token"}
```

---

## Job store and secret redaction

Every `POST /api/v1/compare` persists the result (changes, summary, timestamp, source identifiers, and the original request). Before the request is written to the store, MirrorMatch redacts:

- Auth fields: `token`, `api_key`, `password`, `username` → `"***REDACTED***"`
- Sensitive headers: `Authorization`, `Proxy-Authorization`, `Cookie`, `X-API-Key` (case-insensitive) → `"***REDACTED***"`

The live HTTP/ES calls use the original credentials; only the stored record is scrubbed.

The store backend is selected by environment variable:

| Condition | Store used |
|-----------|------------|
| `MIRROR_MATCH_DB_URL` starts with `postgres://` or `postgresql://` | `PostgresJobStore` (requires `[postgres]` extra) |
| `MIRROR_MATCH_DB_URL` unset or empty | `SqliteJobStore` at `MIRROR_MATCH_DB_PATH` |
