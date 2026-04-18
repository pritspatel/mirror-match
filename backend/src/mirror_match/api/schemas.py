"""API request/response schemas."""

from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field

from ..diff.models import DiffSummary, FieldChange


class RawSource(BaseModel):
    type: Literal["raw"]
    data: Any
    identifier: str | None = None


class HttpAuthConfig(BaseModel):
    kind: Literal["none", "bearer", "basic", "api_key"] = "none"
    token: str | None = None
    username: str | None = None
    password: str | None = None
    header_name: str = "X-API-Key"


class HttpSource(BaseModel):
    type: Literal["http"]
    url: str
    method: Literal["GET", "POST"] = "GET"
    headers: dict[str, str] = Field(default_factory=dict)
    body: Any = None
    auth: HttpAuthConfig = Field(default_factory=HttpAuthConfig)
    timeout: float = 10.0
    json_pointer: str | None = None
    identifier: str | None = None


class EsAuthConfig(BaseModel):
    kind: Literal["none", "api_key", "basic"] = "none"
    api_key: str | None = None
    username: str | None = None
    password: str | None = None


class EsSource(BaseModel):
    type: Literal["elasticsearch"]
    hosts: list[str]
    index: str
    mode: Literal["by_id", "query"] = "by_id"
    doc_id: str | None = None
    query: dict[str, Any] | None = None
    query_return: Literal["first_source", "hits"] = "first_source"
    auth: EsAuthConfig = Field(default_factory=EsAuthConfig)
    verify_certs: bool = True
    identifier: str | None = None


SourceConfig = Annotated[
    RawSource | HttpSource | EsSource,
    Field(discriminator="type"),
]


class CompareOptions(BaseModel):
    ignore_paths: list[str] = Field(default_factory=list)
    array_as_set: bool = False
    array_keys: dict[str, str] = Field(default_factory=dict)
    numeric_tolerance: float = 0.0
    case_insensitive: bool = False


class CompareRequest(BaseModel):
    source_a: SourceConfig
    source_b: SourceConfig
    options: CompareOptions = Field(default_factory=CompareOptions)


class CompareResponse(BaseModel):
    job_id: str
    timestamp: str
    source_a_id: str
    source_b_id: str
    summary: DiffSummary
    changes: list[FieldChange]
