from __future__ import annotations
import json
from collections.abc import Iterator

from core.loaders.base import Loader
from core.models.input import URLInput


class JSONLoader(Loader):
    def __init__(self, path: str):
        self._path = path

    def load(self) -> Iterator[URLInput]:
        with open(self._path) as f:
            data = json.load(f)
        if isinstance(data, list):
            for item in data:
                yield URLInput(
                    source=item["url"],
                    depth=item.get("params", {}).get("depth", 0),
                    tags=item.get("params", {}).get("tags", []),
                )
        elif isinstance(data, dict):
            yield URLInput(
                source=data["url"],
                depth=data.get("params", {}).get("depth", 0),
                tags=data.get("params", {}).get("tags", []),
            )
