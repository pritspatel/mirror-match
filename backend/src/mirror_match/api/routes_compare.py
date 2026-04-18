"""/api/v1/compare routes."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import cast

from fastapi import APIRouter, Response

from ..adapters.base import SourceAdapter
from ..adapters.elasticsearch import EsAdapter, EsAuth
from ..adapters.http import HttpAdapter, HttpAuth
from ..adapters.raw import RawAdapter
from ..diff.engine import compare, summarize
from ..diff.models import DiffSummary, FieldChange
from ..diff.normalize import as_set
from ..reporters.csv import to_csv
from ..reporters.html import to_html
from .schemas import (
    CompareRequest,
    CompareResponse,
    EsSource,
    HttpSource,
    RawSource,
    SourceConfig,
)

router = APIRouter(prefix="/api/v1", tags=["compare"])


def _build_adapter(src: SourceConfig) -> SourceAdapter:
    if isinstance(src, RawSource):
        return RawAdapter(data=src.data, identifier=src.identifier or "raw")
    if isinstance(src, HttpSource):
        return HttpAdapter(
            url=src.url,
            method=src.method,
            headers=src.headers,
            body=src.body,
            auth=HttpAuth(
                kind=src.auth.kind,
                token=src.auth.token,
                username=src.auth.username,
                password=src.auth.password,
                header_name=src.auth.header_name,
            ),
            timeout=src.timeout,
            json_pointer=src.json_pointer,
            identifier=src.identifier,
        )
    if isinstance(src, EsSource):
        return EsAdapter(
            hosts=src.hosts,
            index=src.index,
            mode=src.mode,
            doc_id=src.doc_id,
            query=src.query,
            query_return=src.query_return,
            auth=EsAuth(
                kind=src.auth.kind,
                api_key=src.auth.api_key,
                username=src.auth.username,
                password=src.auth.password,
            ),
            verify_certs=src.verify_certs,
            identifier=src.identifier,
        )
    raise ValueError(f"unsupported source type: {src}")  # pragma: no cover


def _filter_ignored(changes: list[FieldChange], ignore: list[str]) -> list[FieldChange]:
    if not ignore:
        return changes
    return [c for c in changes if not any(c.path.startswith(p) for p in ignore)]


async def _run_compare(req: CompareRequest) -> tuple[str, str, str, list[FieldChange]]:
    loaded_a = await _build_adapter(req.source_a).load()
    loaded_b = await _build_adapter(req.source_b).load()
    data_a, data_b = loaded_a.data, loaded_b.data
    if req.options.array_as_set:
        data_a, data_b = as_set(data_a), as_set(data_b)
    raw_changes = compare(data_a, data_b)
    changes = _filter_ignored(raw_changes, req.options.ignore_paths)
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    return timestamp, loaded_a.identifier, loaded_b.identifier, changes


@router.post("/compare", response_model=CompareResponse)
async def compare_endpoint(req: CompareRequest) -> CompareResponse:
    timestamp, a_id, b_id, changes = await _run_compare(req)
    return CompareResponse(
        job_id=str(uuid.uuid4()),
        timestamp=timestamp,
        source_a_id=a_id,
        source_b_id=b_id,
        summary=DiffSummary(**summarize(changes)),
        changes=changes,
    )


@router.post("/compare.csv")
async def compare_csv_endpoint(req: CompareRequest) -> Response:
    timestamp, a_id, b_id, changes = await _run_compare(req)
    body = to_csv(changes, source_a_id=a_id, source_b_id=b_id, timestamp=timestamp)
    filename = f"mirror-match-{timestamp}.csv"
    return Response(
        content=body,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/compare.html")
async def compare_html_endpoint(req: CompareRequest) -> Response:
    timestamp, a_id, b_id, changes = await _run_compare(req)
    summary = summarize(changes)
    body = to_html(
        cast(list[FieldChange], changes),
        source_a_id=a_id,
        source_b_id=b_id,
        timestamp=timestamp,
        summary=summary,
    )
    filename = f"mirror-match-{timestamp}.html"
    return Response(
        content=body,
        media_type="text/html",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
