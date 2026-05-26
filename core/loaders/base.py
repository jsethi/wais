from __future__ import annotations
from abc import ABC, abstractmethod
from collections.abc import Iterator

from core.models.input import URLInput


class Loader(ABC):
    @abstractmethod
    def load(self) -> Iterator[URLInput]:
        ...
