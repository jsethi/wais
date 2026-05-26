from __future__ import annotations
from abc import ABC, abstractmethod

from core.models.metadata import FileMeta


class FetchResult:
    def __init__(
        self,
        content: bytes,
        content_type: str,
        status_code: int,
        headers: dict[str, str],
        final_url: str,
        metadata: FileMeta | None = None,
    ):
        self.content = content
        self.content_type = content_type
        self.status_code = status_code
        self.headers = headers
        self.final_url = final_url
        self.metadata = metadata


class Fetcher(ABC):
    @abstractmethod
    async def fetch(self, url: str, depth: int = 0, parent_url: str = "") -> FetchResult:
        ...
