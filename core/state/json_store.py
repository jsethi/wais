from __future__ import annotations
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from core.models.state import URLState, URLStatus, ResumeMode

logger = logging.getLogger(__name__)


class JSONStore:
    def __init__(self, path: str):
        self._path = Path(path)
        self._data: dict[str, list] = {"urls": []}

    async def open(self):
        if self._path.exists():
            with open(self._path) as f:
                self._data = json.load(f)

    async def close(self):
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._path, "w") as f:
            json.dump(self._data, f, indent=2)

    async def add_url(self, url: str, run_id: str, depth: int = 0, parent_url: str = ""):
        existing = [u for u in self._data["urls"] if u["url"] == url and u["run_id"] == run_id]
        if not existing:
            self._data["urls"].append({
                "url": url,
                "run_id": run_id,
                "status": URLStatus.pending.value,
                "depth": depth,
                "content_hash": "",
                "parent_url": parent_url,
                "error": "",
                "fetched_at": "",
            })

    async def add_urls(self, urls: list[dict], run_id: str):
        for u in urls:
            await self.add_url(u["url"], run_id, u.get("depth", 0), u.get("parent_url", ""))

    async def mark_completed(self, url: str, run_id: str, content_hash: str = ""):
        now = datetime.now(timezone.utc).isoformat()
        for u in self._data["urls"]:
            if u["url"] == url and u["run_id"] == run_id:
                u["status"] = URLStatus.completed.value
                u["content_hash"] = content_hash
                u["fetched_at"] = now

    async def mark_failed(self, url: str, run_id: str, error: str = ""):
        for u in self._data["urls"]:
            if u["url"] == url and u["run_id"] == run_id:
                u["status"] = URLStatus.failed.value
                u["error"] = error

    async def get_pending(self, run_id: str, resume_mode: ResumeMode | None = None) -> list[URLState]:
        if resume_mode == ResumeMode.skip_completed:
            return [
                URLState(**u) for u in self._data["urls"]
                if u["run_id"] == run_id and u["status"] == URLStatus.pending.value
            ]
        return [URLState(**u) for u in self._data["urls"] if u["run_id"] == run_id]

    async def get_stats(self, run_id: str) -> dict:
        urls = [u for u in self._data["urls"] if u["run_id"] == run_id]
        completed = sum(1 for u in urls if u["status"] == URLStatus.completed.value)
        failed = sum(1 for u in urls if u["status"] == URLStatus.failed.value)
        pending = sum(1 for u in urls if u["status"] == URLStatus.pending.value)
        return {"total": len(urls), "completed": completed, "failed": failed, "pending": pending}
