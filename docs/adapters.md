# Adapters

Every comparison takes a **source config** for `source_a` and `source_b`. The `type` field determines which adapter runs.

## `raw` — inline JSON

```json
{ "type": "raw", "data": { "x": 1 }, "identifier": "fixture-A" }
```

`data` may also be a JSON string (it will be parsed server-side).

## `http` — REST endpoint

```json
{
  "type": "http",
  "url": "https://api.example.com/v1/item/42",
  "method": "GET",
  "headers": { "Accept": "application/json" },
  "auth": { "kind": "bearer", "token": "..." },
  "json_pointer": "/data/item",
  "identifier": "prod-item-42"
}
```

Auth `kind` options:

| Kind | Required fields |
|------|-----------------|
| `none` | — |
| `bearer` | `token` |
| `basic` | `username`, `password` |
| `api_key` | `token`, optional `header_name` (default `X-API-Key`) |

`json_pointer` (optional) extracts a sub-document from the response using RFC 6901 syntax.

## `elasticsearch` — ES cluster

**By document id:**
```json
{
  "type": "elasticsearch",
  "hosts": ["https://es.prod:9200"],
  "index": "users",
  "mode": "by_id",
  "doc_id": "42",
  "auth": { "kind": "api_key", "api_key": "..." }
}
```

**By DSL query (first hit's `_source`):**
```json
{
  "type": "elasticsearch",
  "hosts": ["https://es.prod:9200"],
  "index": "users",
  "mode": "query",
  "query": { "query": { "term": { "email": "u@example.com" } } }
}
```

Set `query_return: "hits"` to return the full hits array instead of the first source.
