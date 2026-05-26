from __future__ import annotations
from collections.abc import Iterator

from core.loaders.base import Loader
from core.models.input import URLInput


class SingleURLLoader(Loader):
    def __init__(self, url: str, depth: int = 0):
        self._url = url
        self._depth = depth

    def load(self) -> Iterator[URLInput]:
        yield URLInput(source=self._url, depth=self._depth)
