# Quickstart

## Docker (recommended)

```bash
git clone <repo-url> jsondiff && cd jsondiff
docker compose up --build
```

- Backend → http://localhost:8000 (interactive docs at `/docs`)
- Frontend → http://localhost:8080

## Local dev

### Backend

```bash
cd backend
python3.12 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
uvicorn jsondiff.main:app --reload --port 8000
pytest -q
```

### Frontend

```bash
cd frontend
pnpm install
pnpm dev          # http://localhost:5173
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

## Export formats

```bash
# CSV
curl -s -X POST localhost:8000/api/v1/compare.csv \
  -H 'content-type: application/json' -d @payload.json -o diff.csv

# HTML (standalone, openable offline)
curl -s -X POST localhost:8000/api/v1/compare.html \
  -H 'content-type: application/json' -d @payload.json -o diff.html
```
