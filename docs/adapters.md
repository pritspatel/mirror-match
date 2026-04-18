# Adapters

Every comparison takes a **source config** for `source_a` and `source_b`. The `type` field determines which adapter loads the document.

All adapters return a `LoadedSource` with two fields:

- `identifier` — a human-readable label shown in reports and API responses (e.g. `es://users/42`, `https://api.example.com/…`). Set `identifier` explicitly to override the auto-generated value.
- `data` — the decoded JSON document (`dict | list | scalar`).

---

## `raw` — inline JSON

Use for pastes, fixtures, or scripted comparisons where both documents are already in memory.

```json
{
  "type": "raw",
  "data": { "x": 1, "y": 2 },
  "identifier": "fixture-A"
}
```

`data` may be:

- A JSON object / array / scalar — used as-is.
- A JSON **string** containing a serialised document — the adapter parses it server-side. Useful when piping shell output through `curl`.

`identifier` defaults to `"raw"` when omitted.

---

## `http` — REST endpoint

Fetches a URL using `httpx` with async I/O. Supports GET, POST, PUT, and any other HTTP method.

```json
{
  "type": "http",
  "url": "https://api.example.com/v1/item/42",
  "method": "GET",
  "headers": {
    "Accept": "application/json",
    "X-Request-Source": "mirrormatch"
  },
  "auth": { "kind": "bearer", "token": "eyJh..." },
  "json_pointer": "/data/item",
  "identifier": "prod-item-42"
}
```

### Auth kinds

| Kind | Fields | Header emitted |
|------|--------|----------------|
| `none` | — | — |
| `bearer` | `token` | `Authorization: Bearer <token>` |
| `basic` | `username`, `password` | `Authorization: Basic <b64>` |
| `api_key` | `token`, `header_name` _(optional, default `X-API-Key`)_ | `<header_name>: <token>` |

### `json_pointer`

RFC 6901 pointer applied to the parsed response body before the diff. Use this to extract a sub-document when the endpoint wraps its payload:

```json
"json_pointer": "/data/results/0"
```

An extraction failure (missing key, index out of range) returns a `422` error with a descriptive message.

### Secrets and redaction

`token`, `api_key`, `password`, and `username` in the auth block — and any `Authorization`, `Proxy-Authorization`, `Cookie`, or `X-API-Key` request headers — are **redacted to `"***REDACTED***"`** before the request object is written to the job store. The live HTTP call uses the original values; only the persisted record is scrubbed.

### `identifier`

Defaults to the request URL.

---

## `elasticsearch` — ES cluster

Uses the official `elasticsearch-py` async client (v8+). Two fetch modes:

### By document id

Returns `_source` of the specified document.

```json
{
  "type": "elasticsearch",
  "hosts": ["https://es.prod:9200"],
  "index": "users",
  "mode": "by_id",
  "doc_id": "42",
  "auth": { "kind": "api_key", "api_key": "VnVhQ..." },
  "verify_certs": true,
  "identifier": "prod-users/42"
}
```

Default `identifier`: `es://<index>/<doc_id>`.

### By DSL query — first hit's `_source`

```json
{
  "type": "elasticsearch",
  "hosts": ["https://es.prod:9200"],
  "index": "users",
  "mode": "query",
  "query": { "query": { "term": { "email": "alice@example.com" } } },
  "auth": { "kind": "api_key", "api_key": "VnVhQ..." }
}
```

Default `identifier`: `es://<index>?query`.

### By DSL query — full hits array

Set `query_return: "hits"` to return the complete `hits.hits` array rather than just the first document's `_source`. This is useful when comparing full search-result pages between two cluster versions:

```json
{
  "type": "elasticsearch",
  "hosts": ["https://es-v1.prod:9200"],
  "index": "products",
  "mode": "query",
  "query_return": "hits",
  "query": { "query": { "match_all": {} }, "size": 100 }
}
```

### ES auth kinds

| Kind | Fields |
|------|--------|
| `none` | — |
| `api_key` | `api_key` (encoded key string) |
| `basic` | `username`, `password` |

### TLS

`verify_certs` defaults to `true`. Set it to `false` for self-signed clusters (dev/local only). The client is closed after each fetch; connections are not pooled across requests.

### Compatibility

Tested against Elasticsearch 8.x. The adapter calls `client.get()` (by-id mode) or `client.search()` (query mode) from the `elasticsearch-py` async API; `ObjectApiResponse.body` is accessed for version safety.
