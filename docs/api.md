# API reference

The canonical machine-readable spec is always `GET /docs` (FastAPI-generated OpenAPI) when the backend is running. The summary below reflects v1.0.

## `POST /api/v1/compare`

Request:
```jsonc
{
  "source_a": { /* adapter-specific, see Adapters */ },
  "source_b": { /* adapter-specific, see Adapters */ },
  "options":  {
    "ignore_paths": [],
    "array_as_set": false,
    "array_keys": {},
    "numeric_tolerance": 0.0,
    "case_insensitive": false
  }
}
```

Response `200`:
```json
{
  "job_id": "…uuid…",
  "timestamp": "2026-04-18T14:56:47+00:00",
  "source_a_id": "raw",
  "source_b_id": "raw",
  "summary": {"added": 1, "removed": 0, "modified": 1, "total": 2},
  "changes": [
    {"path": "/y", "change_type": "MODIFIED", "value_a": 2, "value_b": 3},
    {"path": "/z", "change_type": "ADDED",    "value_a": null, "value_b": 4}
  ]
}
```

The returned `job_id` is persistent. Use the permalink routes below to replay it.

## `POST /api/v1/compare.csv`

Same request body. Returns `text/csv` with columns `Field_Path,Change_Type,Value_in_Doc_A,Value_in_Doc_B`, preceded by `# Generated`, `# Source A`, `# Source B` comment rows.

## `POST /api/v1/compare.html`

Same request body. Returns a standalone HTML report (inline CSS, no CDN). Openable offline.

## `GET /api/v1/jobs/{job_id}`

Replay a stored diff as JSON. Returns `404` if the job is unknown.

## `GET /api/v1/jobs/{job_id}/csv`

CSV export for a stored job.

## `GET /api/v1/jobs/{job_id}/html`

HTML export for a stored job.

## `GET /api/v1/healthz`

Liveness probe. Returns `{"status":"ok","version":"1.0.0"}`. Always open, even when `MIRROR_MATCH_AUTH_TOKEN` is set.

## `GET /metrics`

Prometheus exposition in `text/plain; version=0.0.4`. Emits:

- `mirror_match_http_requests_total{method,path,status}` — request counter, with job UUIDs bucketed as `/api/v1/jobs/{id}` so cardinality stays bounded.
- `mirror_match_compare_seconds_{count,sum}` — running summary of compare-endpoint duration.

Always open.

## Authentication

When `MIRROR_MATCH_AUTH_TOKEN` is set, every route except `/api/v1/healthz`, `/metrics`, `/docs`, `/openapi.json`, and `/redoc` requires `Authorization: Bearer <token>`. Missing or invalid tokens return `401`.
