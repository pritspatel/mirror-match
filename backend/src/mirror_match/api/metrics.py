"""Tiny Prometheus-compatible metrics.

Avoids the `prometheus_client` dep to keep the core install light. Exposes
request counts and a histogram-lite (count + sum) for compare latency.
"""

from __future__ import annotations

import time
from threading import Lock

from fastapi import APIRouter, Request, Response

router = APIRouter(tags=["metrics"])

_lock = Lock()
_counters: dict[tuple[str, str, int], int] = {}
_compare_count = 0
_compare_sum_seconds = 0.0


def _inc_request(method: str, path: str, status_code: int) -> None:
    global _counters
    key = (method, path, status_code)
    with _lock:
        _counters[key] = _counters.get(key, 0) + 1


def observe_compare(duration_s: float) -> None:
    global _compare_count, _compare_sum_seconds
    with _lock:
        _compare_count += 1
        _compare_sum_seconds += duration_s


async def metrics_middleware(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    path = request.url.path
    if path.startswith("/api/v1/compare"):
        observe_compare(time.perf_counter() - start)
    _inc_request(request.method, _bucket(path), response.status_code)
    return response


def _bucket(path: str) -> str:
    # Collapse job UUIDs so metric cardinality stays bounded.
    if path.startswith("/api/v1/jobs/"):
        rest = path[len("/api/v1/jobs/") :]
        tail = rest.split("/", 1)
        suffix = f"/{tail[1]}" if len(tail) > 1 else ""
        return f"/api/v1/jobs/{{id}}{suffix}"
    return path


@router.get("/metrics")
def metrics() -> Response:
    lines: list[str] = []
    lines.append("# HELP mirror_match_http_requests_total Total HTTP requests")
    lines.append("# TYPE mirror_match_http_requests_total counter")
    with _lock:
        items = list(_counters.items())
        count = _compare_count
        total = _compare_sum_seconds
    for (method, path, status_code), n in sorted(items):
        lines.append(
            f'mirror_match_http_requests_total{{method="{method}",path="{path}",'
            f'status="{status_code}"}} {n}'
        )
    lines.append("# HELP mirror_match_compare_seconds Cumulative compare duration")
    lines.append("# TYPE mirror_match_compare_seconds summary")
    lines.append(f"mirror_match_compare_seconds_count {count}")
    lines.append(f"mirror_match_compare_seconds_sum {total:.6f}")
    body = "\n".join(lines) + "\n"
    return Response(content=body, media_type="text/plain; version=0.0.4")


def reset_metrics() -> None:
    global _counters, _compare_count, _compare_sum_seconds
    with _lock:
        _counters = {}
        _compare_count = 0
        _compare_sum_seconds = 0.0
