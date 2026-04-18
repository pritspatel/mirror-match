"""Elasticsearch adapter.

Two fetch modes:
    - Get a single doc by index + id (returns `_source`).
    - Execute a DSL query against an index and return either the first hit's
      `_source` (default) or the full hits array.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from elasticsearch import AsyncElasticsearch

from .base import LoadedSource

FetchMode = Literal["by_id", "query"]
QueryReturn = Literal["first_source", "hits"]


@dataclass
class EsAuth:
    kind: Literal["none", "api_key", "basic"] = "none"
    api_key: str | None = None
    username: str | None = None
    password: str | None = None


@dataclass
class EsAdapter:
    hosts: list[str]
    index: str
    mode: FetchMode = "by_id"
    doc_id: str | None = None
    query: dict[str, Any] | None = None
    query_return: QueryReturn = "first_source"
    auth: EsAuth = field(default_factory=EsAuth)
    verify_certs: bool = True
    identifier: str | None = None
    _client_factory: Any = None  # injected in tests

    async def load(self) -> LoadedSource:
        client = self._build_client()
        try:
            data = await self._fetch(client)
        finally:
            await client.close()
        identifier = self.identifier or self._default_identifier()
        return LoadedSource(identifier=identifier, data=data)

    def _build_client(self) -> AsyncElasticsearch:
        if self._client_factory is not None:
            return self._client_factory()
        kwargs: dict[str, Any] = {"hosts": self.hosts, "verify_certs": self.verify_certs}
        if self.auth.kind == "api_key" and self.auth.api_key:
            kwargs["api_key"] = self.auth.api_key
        elif self.auth.kind == "basic" and self.auth.username is not None:
            kwargs["basic_auth"] = (self.auth.username, self.auth.password or "")
        return AsyncElasticsearch(**kwargs)

    async def _fetch(self, client: AsyncElasticsearch) -> Any:
        if self.mode == "by_id":
            if not self.doc_id:
                raise ValueError("doc_id is required when mode='by_id'")
            resp = await client.get(index=self.index, id=self.doc_id)
            return _body(resp).get("_source")

        if self.mode == "query":
            query = self.query or {"query": {"match_all": {}}}
            resp = await client.search(index=self.index, body=query)
            body = _body(resp)
            hits = body.get("hits", {}).get("hits", [])
            if self.query_return == "hits":
                return hits
            if not hits:
                return None
            return hits[0].get("_source")

        raise ValueError(f"unknown mode: {self.mode}")

    def _default_identifier(self) -> str:
        if self.mode == "by_id":
            return f"es://{self.index}/{self.doc_id}"
        return f"es://{self.index}?query"


def _body(resp: Any) -> dict[str, Any]:
    """elasticsearch-py 8.x returns an ObjectApiResponse; `.body` is the dict."""
    return resp.body if hasattr(resp, "body") else resp
