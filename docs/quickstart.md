# Quickstart

## Docker (recommended)

```bash
git clone https://github.com/pritspatel/mirror-match mirror-match
cd mirror-match
docker compose up --build
```

- Backend → http://localhost:8000 (interactive OpenAPI docs at `/docs`)
- Frontend → http://localhost:8080

Both images are also published to GitHub Container Registry on every release tag:

```bash
docker pull ghcr.io/pritspatel/mirror-match-backend:latest
docker pull ghcr.io/pritspatel/mirror-match-frontend:latest
```

## Local dev

### Backend

```bash
cd backend
python3.12 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
uvicorn mirror_match.main:app --reload --port 8000
```

Run the test suite:

```bash
pytest -q                         # unit tests (fast, no Docker)
pytest tests/integration/ -v      # ES adapter tests (requires Docker)
```

Run linters:

```bash
ruff check .
mypy src
```

### Frontend

```bash
cd frontend
pnpm install
pnpm dev          # http://localhost:5173 (proxied to backend at :8000)
pnpm build        # production build in dist/
pnpm test         # vitest
```

## Minimal API example

```bash
curl -s -X POST localhost:8000/api/v1/compare \
  -H 'content-type: application/json' \
  -d '{
    "source_a": {"type": "raw", "data": {"x": 1, "y": 2}, "identifier": "A"},
    "source_b": {"type": "raw", "data": {"x": 1, "y": 3, "z": 4}, "identifier": "B"}
  }' | jq
```

Expected response:

```json
{
  "job_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "timestamp": "2026-04-18T14:56:47+00:00",
  "source_a_id": "A",
  "source_b_id": "B",
  "summary": {"added": 1, "removed": 0, "modified": 1, "total": 2},
  "changes": [
    {"path": "/y", "change_type": "MODIFIED", "value_a": 2, "value_b": 3},
    {"path": "/z", "change_type": "ADDED",    "value_a": null, "value_b": 4}
  ]
}
```

## Export formats

```bash
# CSV — columns: Field_Path, Change_Type, Value_in_Doc_A, Value_in_Doc_B
curl -s -X POST localhost:8000/api/v1/compare.csv \
  -H 'content-type: application/json' -d @payload.json -o diff.csv

# Standalone HTML (no external deps, openable offline)
curl -s -X POST localhost:8000/api/v1/compare.html \
  -H 'content-type: application/json' -d @payload.json -o diff.html
```

## Permalinks and sharing

Every `POST /api/v1/compare` persists the result. Replay it by job ID:

```bash
JOB_ID="3fa85f64-5717-4562-b3fc-2c963f66afa6"

# JSON replay
curl -s localhost:8000/api/v1/jobs/$JOB_ID | jq

# Download exports for a stored job
curl -s localhost:8000/api/v1/jobs/$JOB_ID/csv  -o diff.csv
curl -s localhost:8000/api/v1/jobs/$JOB_ID/html -o diff.html
```

In the frontend, click **Share** to copy a `#/jobs/<id>` hash URL — the UI replays the stored result without re-running the comparison.

## Auth-protected deployment

```bash
export MIRROR_MATCH_AUTH_TOKEN="$(openssl rand -hex 32)"
uvicorn mirror_match.main:app --port 8000

# All API calls (except /healthz and /metrics) require the token
curl -H "Authorization: Bearer $MIRROR_MATCH_AUTH_TOKEN" \
     localhost:8000/api/v1/jobs/$JOB_ID | jq
```

## CLI

```bash
# Install
pip install mirror-match

# Compare two local files; exit 1 if any differences found
mirror-match compare before.json after.json

# Write all three report formats
mirror-match compare before.json after.json \
  --json diff.json --csv diff.csv --html diff.html

# Keyed-array diff: match /items elements by their "id" field
mirror-match compare a.json b.json --array-key /items=id

# Ignore floating-point rounding noise
mirror-match compare a.json b.json --numeric-tolerance 1e-9

# Case-insensitive string comparison
mirror-match compare a.json b.json --case-insensitive
```

The CLI exits `0` when the diff is empty and `1` otherwise — use it as a CI gate:

```yaml
- run: mirror-match compare baseline.json current.json --csv report.csv
```

## Postgres job store

```bash
pip install 'mirror-match[postgres]'
export MIRROR_MATCH_DB_URL="postgresql://user:pass@db:5432/mirormatch"
uvicorn mirror_match.main:app
```

When `MIRROR_MATCH_DB_URL` starts with `postgres://` or `postgresql://`, the Postgres store is selected automatically. The `psycopg` (v3) driver handles async connection management.
