from __future__ import annotations
import json
import logging
from datetime import datetime, timezone

import aiosqlite

from core.models.state import URLState, URLStatus, ResumeMode

logger = logging.getLogger(__name__)

CREATE_SQL = """
CREATE TABLE IF NOT EXISTS urls (
    url TEXT NOT NULL,
    run_id TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    depth INTEGER NOT NULL DEFAULT 0,
    content_hash TEXT NOT NULL DEFAULT '',
    parent_url TEXT NOT NULL DEFAULT '',
    error TEXT NOT NULL DEFAULT '',
    fetched_at TEXT NOT NULL DEFAULT '',
    PRIMARY KEY (url, run_id)
);

CREATE INDEX IF NOT EXISTS idx_urls_run_id ON urls(run_id);
CREATE INDEX IF NOT EXISTS idx_urls_status ON urls(status);
"""


class SQLiteStore:
    def __init__(self, db_path: str, batch_size: int = 50):
        self._db_path = db_path
        self._batch_size = batch_size
        self._pending_ops = 0

    async def open(self):
        self._conn = await aiosqlite.connect(self._db_path)
        self._conn.row_factory = aiosqlite.Row
        await self._conn.executescript(CREATE_SQL)
        await self._conn.commit()

    async def _maybe_commit(self):
        self._pending_ops += 1
        if self._pending_ops >= self._batch_size:
            await self._conn.commit()
            self._pending_ops = 0

    async def close(self):
        if self._conn:
            await self._conn.commit()
            await self._conn.close()

    async def add_url(self, url: str, run_id: str, depth: int = 0, parent_url: str = ""):
        await self._conn.execute(
            "INSERT OR IGNORE INTO urls (url, run_id, depth, parent_url) VALUES (?, ?, ?, ?)",
            (url, run_id, depth, parent_url),
        )
        await self._maybe_commit()

    async def add_urls(self, urls: list[dict], run_id: str):
        await self._conn.executemany(
            "INSERT OR IGNORE INTO urls (url, run_id, depth, parent_url) VALUES (:url, :run_id, :depth, :parent_url)",
            [{"url": u["url"], "run_id": run_id, "depth": u.get("depth", 0), "parent_url": u.get("parent_url", "")} for u in urls],
        )
        await self._maybe_commit()

    async def mark_completed(self, url: str, run_id: str, content_hash: str = ""):
        now = datetime.now(timezone.utc).isoformat()
        await self._conn.execute(
            "UPDATE urls SET status = ?, content_hash = ?, fetched_at = ? WHERE url = ? AND run_id = ?",
            (URLStatus.completed.value, content_hash, now, url, run_id),
        )
        await self._maybe_commit()

    async def mark_failed(self, url: str, run_id: str, error: str = ""):
        await self._conn.execute(
            "UPDATE urls SET status = ?, error = ? WHERE url = ? AND run_id = ?",
            (URLStatus.failed.value, error, url, run_id),
        )
        await self._maybe_commit()

    async def get_pending(self, run_id: str, resume_mode: ResumeMode | None = None, limit: int = 0) -> list[URLState]:
        if resume_mode == ResumeMode.skip_completed:
            sql = "SELECT url, run_id, depth, parent_url, status, content_hash, error FROM urls WHERE run_id = ? AND status = ?"
            params: tuple = (run_id, URLStatus.pending.value)
        else:
            sql = "SELECT url, run_id, depth, parent_url, status, content_hash, error FROM urls WHERE run_id = ?"
            params = (run_id,)
        if limit > 0:
            sql += " LIMIT ?"
            params = (*params, limit)
        rows = await self._conn.execute_fetchall(sql, params)
        return [URLState(**dict(r)) for r in rows]

    async def clear_run(self, run_id: str):
        await self._conn.execute("DELETE FROM urls WHERE run_id = ?", (run_id,))
        await self._conn.commit()

    async def get_stats(self, run_id: str) -> dict:
        cursor = await self._conn.execute(
            """SELECT
                COUNT(*) as total,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
                SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending
               FROM urls WHERE run_id = ?""",
            (run_id,),
        )
        row = await cursor.fetchone()
        if row:
            return dict(row)
        return {"total": 0, "completed": 0, "failed": 0, "pending": 0}
