# JSONDiff

Open-source, field-level JSON comparison tool with an interactive web UI and CSV / HTML exports.

## Why

Teams comparing payloads across environments (staging vs prod), across Elasticsearch index versions, or across API revisions usually stitch together `jq`, `diff`, and ad-hoc scripts. JSONDiff replaces that with a single tool: three input modes, deterministic JSON-Pointer-keyed diffs, and sharable reports.

## Features (v0.2)

- **Sources:** raw JSON · HTTP endpoints (Bearer/Basic/API-Key auth) · Elasticsearch (by id or DSL query)
- **Diff engine:** RFC 6901 paths, positional arrays (default), `array-as-set` mode, ignore-paths filter
- **Exports:** JSON (API), CSV, standalone HTML report (inline CSS, no external deps)
- **UI:** flat list + collapsible tree view, color-coded changes
- **License:** MIT

See [Quickstart](quickstart.md) to run locally, or jump to the [API reference](api.md).
