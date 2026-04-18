"""/api/v1/compare route."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Response

from ..adapters.raw import RawAdapter
from ..diff.engine import compare, summarize
from ..diff.models import DiffSummary, FieldChange
from ..reporters.csv import to_csv
from .schemas import CompareRequest, CompareResponse, SourceConfig

router = APIRouter(prefix="/api/v1", tags=["compare"])


def _build_adapter(src: SourceConfig) -> RawAdapter:
    # v0.1: raw only. Extend in v0.2 (ES, HTTP) by dispatching on src.type.
    return RawAdapter(data=src.data, identifier=src.identifier or "raw")


def _filter_ignored(changes: list[FieldChange], ignore: list[str]) -> list[FieldChange]:
    if not ignore:
        return changes
    return [c for c in changes if not any(c.path.startswith(p) for p in ignore)]


async def _run_compare(req: CompareRequest) -> tuple[str, str, str, list[FieldChange]]:
    adapter_a = _build_adapter(req.source_a)
    adapter_b = _build_adapter(req.source_b)
    loaded_a = await adapter_a.load()
    loaded_b = await adapter_b.load()
    raw_changes = compare(loaded_a.data, loaded_b.data)
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
    filename = f"jsondiff-{timestamp}.csv"
    return Response(
        content=body,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
