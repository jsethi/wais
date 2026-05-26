from __future__ import annotations
import tempfile
from pathlib import Path

import pytest
import pytest_asyncio

from core.state.sqlite_store import SQLiteStore


@pytest.mark.asyncio
class TestSQLiteStore:
    @pytest_asyncio.fixture
    async def store(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        store = SQLiteStore(db_path)
        await store.open()
        yield store
        await store.close()
        Path(db_path).unlink(missing_ok=True)

    async def test_add_and_get_pending(self, store):
        await store.add_url("https://example.com", "run_001", depth=0)
        pending = await store.get_pending("run_001")
        assert len(pending) == 1
        assert pending[0].url == "https://example.com"
        assert pending[0].status.value == "pending"

    async def test_mark_completed(self, store):
        await store.add_url("https://example.com", "run_001")
        await store.mark_completed("https://example.com", "run_001", "abc123")
        rows = await store.get_pending("run_001")
        assert len(rows) == 1
        assert rows[0].status.value == "completed"
        assert rows[0].content_hash == "abc123"

    async def test_mark_failed(self, store):
        await store.add_url("https://example.com", "run_001")
        await store.mark_failed("https://example.com", "run_001", "connection error")
        rows = await store.get_pending("run_001")
        assert rows[0].status.value == "failed"
        assert rows[0].error == "connection error"

    async def test_skip_completed_mode(self, store):
        await store.add_url("https://a.com", "run_001")
        await store.add_url("https://b.com", "run_001")
        await store.mark_completed("https://a.com", "run_001", "abc")
        from core.models.state import ResumeMode
        pending = await store.get_pending("run_001", ResumeMode.skip_completed)
        assert len(pending) == 1
        assert pending[0].url == "https://b.com"

    async def test_stats(self, store):
        await store.add_url("https://a.com", "run_001")
        await store.add_url("https://b.com", "run_001")
        await store.add_url("https://c.com", "run_001")
        await store.mark_completed("https://a.com", "run_001", "a")
        await store.mark_failed("https://b.com", "run_001", "err")
        stats = await store.get_stats("run_001")
        assert stats["total"] == 3
        assert stats["completed"] == 1
        assert stats["failed"] == 1
        assert stats["pending"] == 1
