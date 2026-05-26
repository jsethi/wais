from __future__ import annotations
import csv
from collections.abc import Iterator

from core.loaders.base import Loader
from core.models.input import URLInput


class CSVLoader(Loader):
    def __init__(self, path: str):
        self._path = path

    def load(self) -> Iterator[URLInput]:
        with open(self._path, newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                url = row.get("url", "").strip()
                if not url:
                    continue
                yield URLInput(
                    source=url,
                    depth=int(row.get("depth", 0)),
                    tags=[t.strip() for t in row.get("tags", "").split(",") if t.strip()],
                )
