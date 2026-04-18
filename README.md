# MirrorMatch

Open-source, field-level JSON comparison tool with interactive web UI and CSV/HTML exports.

Ingests from:
- Raw JSON strings / files (v0.1)
- Elasticsearch indices (v0.2)
- HTTP/REST endpoints (v0.2)

Outputs:
- Side-by-side + unified diff UI
- CSV (`Field_Path, Change_Type, Value_in_Doc_A, Value_in_Doc_B`)
- Standalone HTML report (v0.2)

## Status

**v0.1 MVP** — raw JSON inputs, diff engine, FastAPI `/compare`, React UI, CSV export.

## Quickstart

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
uvicorn mirror_match.main:app --reload --port 8000
```

Open http://localhost:8000/docs for the interactive OpenAPI UI.

### Frontend

```bash
cd frontend
pnpm install   # or: npm install
pnpm dev       # http://localhost:5173
```

### Docker (one command)

```bash
docker compose up --build
```

Browse http://localhost:8000 (backend) and http://localhost:5173 (frontend).

## Example API call

```bash
curl -s -X POST localhost:8000/api/v1/compare \
  -H 'content-type: application/json' \
  -d '{
    "source_a": {"type": "raw", "data": {"x": 1, "y": 2}},
    "source_b": {"type": "raw", "data": {"x": 1, "y": 3, "z": 4}}
  }' | jq
```

Response:
```json
{
  "job_id": "…",
  "timestamp": "2026-04-18T14:22:00Z",
  "source_a_id": "raw",
  "source_b_id": "raw",
  "summary": {"added": 1, "removed": 0, "modified": 1, "total": 2},
  "changes": [
    {"path": "/y", "change_type": "MODIFIED", "value_a": 2, "value_b": 3},
    {"path": "/z", "change_type": "ADDED", "value_a": null, "value_b": 4}
  ]
}
```

CSV export:
```bash
curl -s -X POST localhost:8000/api/v1/compare.csv \
  -H 'content-type: application/json' \
  -d @payload.json -o diff.csv
```

## Architecture

See [docs/superpowers/plans](docs/) and the approved architectural doc. Core stages:

1. **Ingest adapters** load each source → canonical `dict`.
2. **Normalizer** applies optional transforms (ignore paths, array-as-set, null-drop).
3. **Diff engine** walks both trees, emits `List[FieldChange]` keyed by JSON Pointer path.
4. **Reporters** serialize to JSON / CSV / HTML.

## License

MIT — see [LICENSE](LICENSE).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) and [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).
