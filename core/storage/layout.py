from __future__ import annotations
import re
from abc import ABC, abstractmethod
from pathlib import Path
from urllib.parse import urlparse

_FORBIDDEN_RE = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def _sanitize_segment(segment: str) -> str:
    s = _FORBIDDEN_RE.sub("_", segment)
    if s in (".", "..", ""):
        s = "_"
    if len(s.encode("utf-8")) > 200:
        s = s[:80]
    return s


class StorageLayout(ABC):
    @abstractmethod
    def resolve_path(self, url: str, base_dir: Path) -> Path:
        ...


class DomainHierarchyLayout(StorageLayout):
    def resolve_path(self, url: str, base_dir: Path) -> Path:
        parsed = urlparse(url)
        netloc = _sanitize_segment((parsed.netloc or "unknown").split("/")[0])
        parts = [_sanitize_segment(p) for p in parsed.path.strip("/").split("/") if p and p != ".."]
        if not parts:
            return base_dir / netloc / "index.html"
        name = parts[-1]
        if "." in name:
            stem = name.rsplit(".", 1)[0]
            return base_dir / netloc / "/".join(parts[:-1]) / f"{stem}.html"
        return base_dir / netloc / "/".join(parts) / "index.html"


class FlatLayout(StorageLayout):
    def resolve_path(self, url: str, base_dir: Path) -> Path:
        from core.hashing.utils import hash_bytes
        url_hash = hash_bytes(url.encode(), "sha256")[:16]
        return base_dir / f"{url_hash}.html"
