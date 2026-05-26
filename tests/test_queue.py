from __future__ import annotations

from core.utils.queue import URLQueue


class TestURLQueue:
    def test_fifo(self):
        q = URLQueue()
        q.push("https://a.com")
        q.push("https://b.com")
        q.push("https://c.com")
        assert q.pop() == "https://a.com"
        assert q.pop() == "https://b.com"
        assert q.pop() == "https://c.com"
        assert q.pop() is None

    def test_priority(self):
        q = URLQueue(priority_mode=True)
        q.push("https://low.com", priority=10)
        q.push("https://high.com", priority=1)
        q.push("https://mid.com", priority=5)
        assert q.pop() == "https://high.com"
        assert q.pop() == "https://mid.com"
        assert q.pop() == "https://low.com"

    def test_len_and_is_empty(self):
        q = URLQueue()
        assert q.is_empty
        assert len(q) == 0
        q.push("https://a.com")
        assert not q.is_empty
        assert len(q) == 1
