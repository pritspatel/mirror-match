"""/api/v1/compare routes."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import cast

from fastapi import APIRouter, HTTPException, Response

from ..adapters.base import SourceAdapter
from ..adapters.elasticsearch import EsAdapter, EsAuth
from ..adapters.http import HttpAdapter, HttpAuth
from ..adapters.raw import RawAdapter
from ..config import get_job_store
from ..diff.engine import compare, summarize
from ..diff.models import CompareConfig, DiffSummary, FieldChange
from ..diff.normalize import as_set
from ..reporters.csv import to_csv
from ..reporters.html import to_html
from ..store.base import JobRecord
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


async def _run_compare(
    req: CompareRequest,
) -> tuple[str, str, str, str, list[FieldChange]]:
    loaded_a = await _build_adapter(req.source_a).load()
    loaded_b = await _build_adapter(req.source_b).load()
    data_a, data_b = loaded_a.data, loaded_b.data
    if req.options.array_as_set:
        data_a, data_b = as_set(data_a), as_set(data_b)
    cfg = CompareConfig(
        array_keys=req.options.array_keys,
        numeric_tolerance=req.options.numeric_tolerance,
        case_insensitive=req.options.case_insensitive,
    )
    raw_changes = compare(data_a, data_b, config=cfg)
    changes = _filter_ignored(raw_changes, req.options.ignore_paths)
    timestamp = datetime.now(UTC).isoformat(timespec="seconds")
    job_id = str(uuid.uuid4())
    record = JobRecord(
        job_id=job_id,
        timestamp=timestamp,
        source_a_id=loaded_a.identifier,
        source_b_id=loaded_b.identifier,
        summary=summarize(changes),
        changes=changes,
        request=req.model_dump(mode="json"),
    )
    get_job_store().put(record)
    return job_id, timestamp, loaded_a.identifier, loaded_b.identifier, changes


@router.post("/compare", response_model=CompareResponse)
async def compare_endpoint(req: CompareRequest) -> CompareResponse:
    job_id, timestamp, a_id, b_id, changes = await _run_compare(req)
    return CompareResponse(
        job_id=job_id,
        timestamp=timestamp,
        source_a_id=a_id,
        source_b_id=b_id,
        summary=DiffSummary(**summarize(changes)),
        changes=changes,
    )


@router.post("/compare.csv")
async def compare_csv_endpoint(req: CompareRequest) -> Response:
    _, timestamp, a_id, b_id, changes = await _run_compare(req)
    body = to_csv(changes, source_a_id=a_id, source_b_id=b_id, timestamp=timestamp)
    filename = f"mirror-match-{timestamp}.csv"
    return Response(
        content=body,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/compare.html")
async def compare_html_endpoint(req: CompareRequest) -> Response:
    _, timestamp, a_id, b_id, changes = await _run_compare(req)
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


def _load_job_or_404(job_id: str) -> JobRecord:
    record = get_job_store().get(job_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"job not found: {job_id}")
    return record


@router.get("/jobs/{job_id}", response_model=CompareResponse)
def get_job(job_id: str) -> CompareResponse:
    r = _load_job_or_404(job_id)
    return CompareResponse(
        job_id=r.job_id,
        timestamp=r.timestamp,
        source_a_id=r.source_a_id,
        source_b_id=r.source_b_id,
        summary=DiffSummary(**r.summary),
        changes=r.changes,
    )


@router.get("/jobs/{job_id}/csv")
def get_job_csv(job_id: str) -> Response:
    r = _load_job_or_404(job_id)
    body = to_csv(
        r.changes,
        source_a_id=r.source_a_id,
        source_b_id=r.source_b_id,
        timestamp=r.timestamp,
    )
    filename = f"mirror-match-{r.job_id}.csv"
    return Response(
        content=body,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/jobs/{job_id}/html")
def get_job_html(job_id: str) -> Response:
    r = _load_job_or_404(job_id)
    body = to_html(
        r.changes,
        source_a_id=r.source_a_id,
        source_b_id=r.source_b_id,
        timestamp=r.timestamp,
        summary=r.summary,
    )
    filename = f"mirror-match-{r.job_id}.html"
    return Response(
        content=body,
        media_type="text/html",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
