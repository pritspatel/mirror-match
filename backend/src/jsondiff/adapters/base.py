"""Adapter protocol: any source loader returns a JSON-compatible value and an id."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass
class LoadedSource:
    identifier: str
    data: Any


class SourceAdapter(Protocol):
    async def load(self) -> LoadedSource: ...
