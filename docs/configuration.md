# Configuration

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MIRROR_MATCH_CORS_ORIGINS` | `http://localhost:5173,http://127.0.0.1:5173` | Comma-separated list of CORS-allowed origins. Set to your frontend origin in production. |
| `MIRROR_MATCH_DB_PATH` | `mirror-match.db` | Path to the SQLite job-store file. Parent directories are created automatically on startup. Ignored when `MIRROR_MATCH_DB_URL` is set to a Postgres DSN. |
| `MIRROR_MATCH_DB_URL` | _(unset)_ | Postgres DSN (`postgresql://user:pw@host:5432/db`). When this starts with `postgres://` or `postgresql://`, the Postgres store is selected and `MIRROR_MATCH_DB_PATH` is ignored. Requires installing the `postgres` extra: `pip install 'mirror-match[postgres]'`. |
| `MIRROR_MATCH_AUTH_TOKEN` | _(unset)_ | When set, every route except `/api/v1/healthz`, `/metrics`, `/docs`, `/openapi.json`, and `/redoc` requires `Authorization: Bearer <token>`. |

### Job store selection logic

```
MIRROR_MATCH_DB_URL set?
├── starts with "postgres://" or "postgresql://"  →  PostgresJobStore(dsn)
└── empty / other scheme                           →  SqliteJobStore(MIRROR_MATCH_DB_PATH)
```

The store is initialised lazily on first request and cached for the lifetime of the process. In tests, call `config.reset_job_store_cache()` before monkeypatching env vars.

---

## Compare options

Passed under `options` on any `POST /api/v1/compare*` request.

```jsonc
{
  "options": {
    "ignore_paths":      ["/meta/ts", "/cache"],
    "array_as_set":      false,
    "array_keys":        { "/items": "id" },
    "numeric_tolerance": 0.0,
    "case_insensitive":  false
  }
}
```

### `ignore_paths`

List of JSON Pointer prefixes. Any field whose path **starts with** one of these values is stripped before diffing.

```jsonc
"ignore_paths": ["/meta/updated_at", "/request_id", "/_cache"]
```

Useful for volatile fields (timestamps, UUIDs, cache keys) that always differ between environments but aren't semantically meaningful.

### `array_as_set`

When `true`, arrays are canonically sorted before diffing, so `[a, b, c]` vs `[c, a, b]` produces no changes. Elements must be JSON-serialisable for sorting; mixed-type arrays fall back to string sort.

### `array_keys`

Maps a JSON Pointer path to a field name. Elements at that path are matched across A and B by the value of that field instead of by list index.

```jsonc
"array_keys": {
  "/items":           "id",
  "/users/0/orders":  "order_id"
}
```

Elements that **lack the key field** fall back to positional diffing under a synthetic `~` sub-path (e.g. `/items/~/0`), so JSON Pointer uniqueness is preserved even with orphans.

Example: if A has `[{id:1, name:"x"}, {id:2, name:"y"}]` and B has `[{id:2, name:"Y"}, {id:1, name:"x"}]`, without keying you get two MODIFIEDs (index 0 and 1). With `array_keys: {"/": "id"}` you get one MODIFIED on `/1/name` (id=2 changed).

### `numeric_tolerance`

`abs(a - b) <= tolerance` is treated as equal. Applies to any numeric pair. Booleans are excluded deliberately (to avoid `true == 1`).

```jsonc
"numeric_tolerance": 1e-9   // ignore floating-point rounding noise
```

### `case_insensitive`

When `true`, string values are folded via Python's `str.casefold()` before comparison. Applies only to string-vs-string comparisons; mixed-type pairs (e.g. `"Alice"` vs `42`) still report a MODIFIED.

---

## CLI flags

`mirror-match compare A B` accepts the same options as the API:

| Flag | Maps to `options.` | Notes |
|------|--------------------|-------|
| `--array-key POINTER=FIELD` | `array_keys` | Repeatable. E.g. `--array-key /items=id --array-key /tags=name`. |
| `--numeric-tolerance N` | `numeric_tolerance` | Float. E.g. `1e-9`. |
| `--case-insensitive` | `case_insensitive` | Boolean flag. |
| `--ignore-path POINTER` | `ignore_paths` | Repeatable. |
| `--csv PATH` | — | Write CSV report to `PATH`. |
| `--html PATH` | — | Write HTML report to `PATH`. |
| `--json PATH` | — | Write JSON report to `PATH`. |

Multiple output formats may be requested in a single invocation:

```bash
mirror-match compare before.json after.json \
  --csv diff.csv --html diff.html --json diff.json
```

**Exit codes:**

| Code | Meaning |
|------|---------|
| `0` | Diff is empty (documents are equivalent under the given options). |
| `1` | One or more differences found. |
| `2` | Invocation error (bad arguments, file not found, etc.). |

The non-zero exit on differences makes the CLI suitable as a CI gate:

```yaml
- name: Assert API contract unchanged
  run: mirror-match compare baseline.json current.json --csv report.csv
```
