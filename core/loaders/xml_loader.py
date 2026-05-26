from __future__ import annotations
from collections.abc import Iterator
from xml.etree.ElementTree import XMLParser, parse

from core.loaders.base import Loader
from core.models.input import URLInput


class XMLLoader(Loader):
    def __init__(self, path: str):
        self._path = path

    def load(self) -> Iterator[URLInput]:
        try:
            parser = XMLParser(resolve_entities=False)
        except TypeError:
            parser = XMLParser()
        tree = parse(self._path, parser)
        root = tree.getroot()
        for elem in root.iter("url"):
            url = (elem.text or "").strip()
            if url:
                depth = int(elem.get("depth", 0))
                tags = [t.strip() for t in elem.get("tags", "").split(",") if t.strip()]
                yield URLInput(source=url, depth=depth, tags=tags)
