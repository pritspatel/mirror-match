# MirrorMatch

Open-source, field-level JSON comparison tool with an interactive web UI, CLI, and CSV / HTML exports.

## Why

Teams comparing payloads across environments (staging vs prod), across Elasticsearch index versions, or across API revisions usually stitch together `jq`, `diff`, and ad-hoc scripts. MirrorMatch replaces that with a single tool: three input modes, deterministic JSON-Pointer-keyed diffs, shareable reports, and a reproducible CLI.

## Features (v1.0)

- **Sources:** raw JSON · HTTP endpoints (Bearer / Basic / API-Key auth) · Elasticsearch (by id or DSL query)
- **Diff engine:** RFC 6901 paths, positional arrays, keyed arrays (`array_keys`), `array_as_set`, numeric tolerance, case-insensitive strings, ignore-paths filter
- **Exports:** JSON (API), CSV, standalone HTML report (inline CSS, no external deps)
- **Permalinks:** every diff persists to SQLite (or Postgres); share `/api/v1/jobs/{id}` or the hash-route UI link
- **Ops:** optional bearer-token auth, Prometheus `/metrics`, structured liveness probe
- **CLI:** `mirror-match compare a.json b.json [--csv|--html|--json]`
- **License:** MIT

## Architecture

```
┌────────────────────────────────────────────────────┐
│                   Browser (SPA)                    │
│  React + TS · Tailwind · Monaco editor             │
└────────────▲────────────────────────┬──────────────┘
             │ REST /api/v1           │ hash-route replay
┌────────────┴────────────────────────┴──────────────┐
│            Backend (FastAPI, Python 3.12)           │
│                                                    │
│  ┌──────────┐  ┌────────────┐  ┌───────────────┐  │
│  │ Ingest   │→ │ Diff       │→ │ Reporter      │  │
│  │ Adapters │  │ Engine     │  │ CSV·HTML·JSON │  │
│  └──────────┘  └────────────┘  └───────────────┘  │
│       │             │                  │           │
│  ES|HTTP|Raw   JSON Pointers      Job Store        │
│                                 SQLite / Postgres  │
└────────────────────────────────────────────────────┘
```

### Component overview

| Component | Source | Responsibility |
|-----------|--------|----------------|
| **Ingest Adapters** | `adapters/` | Load a document from ES, HTTP, or raw JSON. Each returns a `LoadedSource(identifier, data)`. |
| **Diff Engine** | `diff/engine.py` | Recursive traversal producing `List[FieldChange]`. JSON Pointer paths (RFC 6901). Supports positional, keyed, and set array strategies. |
| **Normalizer** | `diff/normalize.py` | Pre-diff transforms: ignore-path stripping, null-absent equivalence, type coercions. |
| **Reporters** | `reporters/` | Convert `List[FieldChange]` to CSV, standalone HTML (Jinja2), or JSON. |
| **Job Store** | `store/` | Persist every diff result for later replay. SQLite (default, zero-config) or Postgres (production). Secrets are redacted before persistence. |
| **Auth middleware** | `api/auth.py` | Optional bearer-token gate. Open paths: `/api/v1/healthz`, `/metrics`, `/docs`, `/openapi.json`, `/redoc`. |
| **Metrics middleware** | `api/metrics.py` | Prometheus counters + timing. UUID path segments are bucketed to prevent cardinality explosion. |

## Quick links

- [Quickstart](quickstart.md) — Docker and local dev setup
- [Adapters](adapters.md) — source config reference
- [Configuration](configuration.md) — env vars, compare options, CLI flags
- [API reference](api.md) — endpoints, request/response shapes, error codes
