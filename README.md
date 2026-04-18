# MirrorMatch

Open-source, field-level JSON comparison tool with an interactive web UI, CLI, and CSV/HTML exports.

**Ingests from:**
- Raw JSON strings / files
- HTTP/REST endpoints (Bearer, Basic, and API-Key auth)
- Elasticsearch indices (by document id or DSL query)

**Outputs:**
- Flat-list and collapsible-tree UI with color-coded changes
- CSV (`Field_Path, Change_Type, Value_in_Doc_A, Value_in_Doc_B`)
- Standalone HTML report (inline CSS, no CDN)
- Shareable permalinks (`/api/v1/jobs/{id}` + hash-route frontend replay)

## Status

**v1.0.0** — production-ready. See [CHANGELOG.md](CHANGELOG.md) for the full release history.

Highlights since v0.2:
- Keyed-array diff (`array_keys`), numeric tolerance, case-insensitive strings
- SQLite-backed job persistence and shareable permalinks
- Optional bearer-token auth (`MIRROR_MATCH_AUTH_TOKEN`)
- Prometheus `/metrics` endpoint
- `mirror-match` CLI for offline diffs

## Quickstart

### Docker (one command)

```bash
docker compose up --build
```

- Backend → http://localhost:8000 (interactive docs at `/docs`)
- Frontend → http://localhost:8080

### Backend (local dev)

```bash
cd backend
python3.12 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
uvicorn mirror_match.main:app --reload --port 8000
```

### Frontend (local dev)

```bash
cd frontend
pnpm install
pnpm dev          # http://localhost:5173
```

### CLI

```bash
pip install -e ./backend
mirror-match compare a.json b.json --csv diff.csv --html diff.html \
  --array-key /items=id --numeric-tolerance 1e-3 --case-insensitive
```

Exit code is `0` when documents match, `1` when they differ.

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
  "timestamp": "2026-04-18T14:22:00+00:00",
  "source_a_id": "raw",
  "source_b_id": "raw",
  "summary": {"added": 1, "removed": 0, "modified": 1, "total": 2},
  "changes": [
    {"path": "/y", "change_type": "MODIFIED", "value_a": 2, "value_b": 3},
    {"path": "/z", "change_type": "ADDED", "value_a": null, "value_b": 4}
  ]
}
```

Replay a past diff:
```bash
curl -s localhost:8000/api/v1/jobs/<job_id>            # JSON
curl -s localhost:8000/api/v1/jobs/<job_id>/csv        # CSV
curl -s localhost:8000/api/v1/jobs/<job_id>/html       # HTML
```

## Architecture

1. **Ingest adapters** ([backend/src/mirror_match/adapters](backend/src/mirror_match/adapters)) load each source → canonical `dict`.
2. **Normalizer** applies optional transforms (ignore paths, array-as-set).
3. **Diff engine** ([backend/src/mirror_match/diff/engine.py](backend/src/mirror_match/diff/engine.py)) walks both trees, emits `List[FieldChange]` keyed by JSON Pointer.
4. **Reporters** serialize to JSON / CSV / HTML.
5. **Job store** persists every diff so permalinks can replay it.

## Documentation

- [Quickstart](docs/quickstart.md)
- [Configuration](docs/configuration.md) — env vars + compare options
- [Adapters](docs/adapters.md) — raw, HTTP, Elasticsearch
- [API reference](docs/api.md)

## Security

See [SECURITY.md](SECURITY.md) for the disclosure process and notes on credential handling in the job store.

## License

MIT — see [LICENSE](LICENSE).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) and [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).
