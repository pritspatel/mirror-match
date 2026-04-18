# MirrorMatch

Open-source, field-level JSON comparison tool with an interactive web UI, CLI, and CSV / HTML exports.

## Why

Teams comparing payloads across environments (staging vs prod), across Elasticsearch index versions, or across API revisions usually stitch together `jq`, `diff`, and ad-hoc scripts. MirrorMatch replaces that with a single tool: three input modes, deterministic JSON-Pointer-keyed diffs, shareable reports, and a reproducible CLI.

## Features (v1.0)

- **Sources:** raw JSON · HTTP endpoints (Bearer / Basic / API-Key auth) · Elasticsearch (by id or DSL query)
- **Diff engine:** RFC 6901 paths, positional arrays, keyed arrays (`array_keys`), `array_as_set`, numeric tolerance, case-insensitive strings, ignore-paths filter
- **Exports:** JSON (API), CSV, standalone HTML report (inline CSS, no external deps)
- **Permalinks:** every diff persists to SQLite; share `/api/v1/jobs/{id}` or the hash-route UI
- **Ops:** optional bearer-token auth, Prometheus `/metrics`
- **CLI:** `mirror-match compare a.json b.json [--csv|--html|--json]`
- **License:** MIT

See [Quickstart](quickstart.md) to run locally, [Configuration](configuration.md) for env vars and options, or the [API reference](api.md).
