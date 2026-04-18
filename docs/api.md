# API reference

The canonical machine-readable spec is always `GET /docs` (FastAPI-generated OpenAPI) when the backend is running. The summary below reflects v0.2.

## `POST /api/v1/compare`

Request:
```jsonc
{
  "source_a": { /* adapter-specific, see Adapters */ },
  "source_b": { /* adapter-specific, see Adapters */ },
  "options":  { "ignore_paths": [], "array_as_set": false }
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

## `POST /api/v1/compare.csv`

Same request body. Returns `text/csv` with columns `Field_Path,Change_Type,Value_in_Doc_A,Value_in_Doc_B`, preceded by `# Generated`, `# Source A`, `# Source B` comment rows.

## `POST /api/v1/compare.html`

Same request body. Returns a standalone HTML report (inline CSS, no CDN). Openable offline.

## `GET /api/v1/healthz`

Liveness probe. Returns `{"status":"ok","version":"0.2.0"}`.
