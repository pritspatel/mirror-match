"""Redaction of sensitive fields before persisting a compare request.

The job store is durable and shareable by design — anyone with the job_id can
replay the diff. We therefore scrub credentials from the persisted request so
they never leak via permalink, CSV/HTML export, or a leaked DB file.

Scope:
- `auth.token`, `auth.api_key`, `auth.password` on HTTP and ES sources
- `auth.username` on HTTP Basic (to avoid leaking the account identity)
- Any header whose name equals Authorization / Proxy-Authorization /
  Cookie / X-API-Key (case-insensitive).
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

REDACTED = "***REDACTED***"

_SENSITIVE_AUTH_FIELDS = frozenset({"token", "api_key", "password", "username"})
_SENSITIVE_HEADER_NAMES = frozenset(
    {"authorization", "proxy-authorization", "cookie", "x-api-key"}
)


def redact_request(request: dict[str, Any]) -> dict[str, Any]:
    scrubbed = deepcopy(request)
    for key in ("source_a", "source_b"):
        source = scrubbed.get(key)
        if isinstance(source, dict):
            _scrub_source(source)
    return scrubbed


def _scrub_source(source: dict[str, Any]) -> None:
    auth = source.get("auth")
    if isinstance(auth, dict):
        for field in _SENSITIVE_AUTH_FIELDS:
            if auth.get(field):
                auth[field] = REDACTED
    headers = source.get("headers")
    if isinstance(headers, dict):
        for name in list(headers):
            if name.lower() in _SENSITIVE_HEADER_NAMES:
                headers[name] = REDACTED
