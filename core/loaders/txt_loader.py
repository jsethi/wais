from __future__ import annotations
from collections.abc import Iterator

from core.loaders.base import Loader
from core.models.input import URLInput


class TxtLoader(Loader):
    def __init__(self, path: str):
        self._path = path

    def load(self) -> Iterator[URLInput]:
        with open(self._path) as f:
            for line in f:
                url = line.strip()
                if url and not url.startswith("#"):
                    yield URLInput(source=url)
