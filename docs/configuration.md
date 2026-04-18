# Configuration

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MIRROR_MATCH_CORS_ORIGINS` | `http://localhost:5173,http://127.0.0.1:5173` | Comma-separated list of CORS-allowed origins. |
| `MIRROR_MATCH_DB_PATH` | `mirror-match.db` | SQLite file for the persistent job store. Parent directories are created on startup. |
| `MIRROR_MATCH_AUTH_TOKEN` | _(unset)_ | When set, every route except `/api/v1/healthz`, `/metrics`, and `/docs` requires `Authorization: Bearer <token>`. |

## Compare options

Passed under `options` on `POST /api/v1/compare*`.

```jsonc
{
  "options": {
    "ignore_paths": ["/meta/ts", "/cache"],  // prefix match on JSON Pointer
    "array_as_set": false,                   // treat arrays as unordered multi-sets
    "array_keys": { "/items": "id" },        // diff arrays by field identity, not position
    "numeric_tolerance": 0.0,                // absolute delta below which numbers are equal
    "case_insensitive": false                // fold string values via str.casefold() before comparing
  }
}
```

- `ignore_paths` — any field whose path starts with one of these prefixes is stripped from the diff (useful for timestamps, request IDs, cache keys).
- `array_as_set` — when `true`, arrays are canonically sorted before diffing, so `[a,b,c]` vs `[c,a,b]` produces no changes.
- `array_keys` — maps a JSON-Pointer path to a field name. Elements at that path are matched across A and B by the value of that field instead of by list index. Elements lacking the key fall back to a positional diff under a synthetic `~` sub-path so pointers stay unique.
- `numeric_tolerance` — `abs(a - b) <= tolerance` counts as equal. Bools are deliberately excluded.
- `case_insensitive` — only affects string-vs-string comparisons.

## CLI flags

`mirror-match compare A B` supports the same options:

| Flag | Maps to |
|------|---------|
| `--array-key POINTER=FIELD` (repeatable) | `array_keys` |
| `--numeric-tolerance N` | `numeric_tolerance` |
| `--case-insensitive` | `case_insensitive` |
| `--csv PATH` / `--html PATH` / `--json PATH` | Writes the corresponding report to disk. |

The CLI exits `0` when the diff is empty and `1` otherwise — handy for CI gates.
