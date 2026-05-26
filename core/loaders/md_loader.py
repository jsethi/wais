from __future__ import annotations
import re
from collections.abc import Iterator

from core.loaders.base import Loader
from core.models.input import URLInput


class MDLoader(Loader):
    def __init__(self, path: str):
        self._path = path

    def load(self) -> Iterator[URLInput]:
        LINK_RE = re.compile(r"\[([^\]]*)\]\((https?://[^)\s]+)\)")
        with open(self._path) as f:
            content = f.read()
        for match in LINK_RE.finditer(content):
            url = match.group(2).strip()
            if url:
                yield URLInput(source=url)
