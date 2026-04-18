"""Optional bearer-token auth.

Enforced only when `MIRROR_MATCH_AUTH_TOKEN` is set. `/healthz`, `/metrics`,
and docs are always open so liveness checks and scrapers don't need creds.
"""

from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse

from ..config import get_auth_token

_OPEN_PREFIXES: tuple[str, ...] = (
    "/api/v1/healthz",
    "/metrics",
    "/docs",
    "/openapi.json",
    "/redoc",
)


async def auth_middleware(request: Request, call_next):
    token = get_auth_token()
    if token and not _is_open(request.url.path):
        header = request.headers.get("authorization", "")
        if not header.startswith("Bearer ") or header[7:] != token:
            return JSONResponse(
                status_code=401,
                content={"detail": "invalid or missing bearer token"},
            )
    return await call_next(request)


def _is_open(path: str) -> bool:
    return any(path.startswith(p) for p in _OPEN_PREFIXES)
