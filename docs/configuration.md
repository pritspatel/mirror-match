# Configuration

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `JSONDIFF_CORS_ORIGINS` | `http://localhost:5173,http://127.0.0.1:5173` | Comma-separated list of CORS-allowed origins. |

## Compare options

Passed under `options` on `POST /api/v1/compare*`.

```jsonc
{
  "options": {
    "ignore_paths": ["/meta/ts", "/cache"],  // prefix match on JSON Pointer
    "array_as_set": false                    // treat arrays as unordered multi-sets
  }
}
```

- `ignore_paths` — any field whose path starts with one of these prefixes is stripped from the diff (useful for timestamps, request IDs, cache keys).
- `array_as_set` — when `true`, arrays are canonically sorted before diffing, so `[a,b,c]` vs `[c,a,b]` produces no changes.
