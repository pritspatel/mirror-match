"""HTTP adapter: fetch JSON from a REST endpoint.

Supports GET/POST, custom headers, and three auth modes: bearer, basic, api_key.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

import httpx

AuthKind = Literal["none", "bearer", "basic", "api_key"]


@dataclass
class HttpAuth:
    kind: AuthKind = "none"
    token: str | None = None
    username: str | None = None
    password: str | None = None
    header_name: str = "X-API-Key"


@dataclass
class HttpAdapter:
    url: str
    method: str = "GET"
    headers: dict[str, str] = field(default_factory=dict)
    body: Any = None
    auth: HttpAuth = field(default_factory=HttpAuth)
    timeout: float = 10.0
    json_pointer: str | None = None
    identifier: str | None = None

    async def load(self) -> Any:
        from .base import LoadedSource

        merged_headers = dict(self.headers)
        httpx_auth = None
        if self.auth.kind == "bearer" and self.auth.token:
            merged_headers["Authorization"] = f"Bearer {self.auth.token}"
        elif self.auth.kind == "api_key" and self.auth.token:
            merged_headers[self.auth.header_name] = self.auth.token
        elif self.auth.kind == "basic" and self.auth.username is not None:
            httpx_auth = httpx.BasicAuth(self.auth.username, self.auth.password or "")

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.request(
                self.method.upper(),
                self.url,
                headers=merged_headers,
                json=self.body if self.body is not None else None,
                auth=httpx_auth,
            )
            response.raise_for_status()
            data = response.json()

        if self.json_pointer:
            data = _resolve_pointer(data, self.json_pointer)

        identifier = self.identifier or f"{self.method.upper()} {self.url}"
        return LoadedSource(identifier=identifier, data=data)


def _resolve_pointer(value: Any, pointer: str) -> Any:
    """RFC 6901 pointer resolution."""
    if pointer in ("", "/"):
        return value
    tokens = pointer.lstrip("/").split("/")
    current = value
    for token in tokens:
        token = token.replace("~1", "/").replace("~0", "~")
        if isinstance(current, list):
            current = current[int(token)]
        elif isinstance(current, dict):
            current = current[token]
        else:
            raise KeyError(f"cannot traverse into {type(current).__name__} at token {token!r}")
    return current
