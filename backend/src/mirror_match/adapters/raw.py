"""Raw JSON adapter: payload already in-memory (dict, list, scalar) or JSON string."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from .base import LoadedSource


@dataclass
class RawAdapter:
    data: Any
    identifier: str = "raw"

    async def load(self) -> LoadedSource:
        value = self.data
        if isinstance(value, str):
            value = json.loads(value)
        return LoadedSource(identifier=self.identifier, data=value)
