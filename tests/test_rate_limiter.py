from __future__ import annotations
import time

import pytest

from core.utils.rate_limiter import RateLimiter


class TestRateLimiter:
    @pytest.mark.asyncio
    async def test_per_domain_delay(self):
        limiter = RateLimiter(per_domain_delay=0.05, jitter=0)
        start = time.monotonic()
        await limiter.wait("example.com")
        await limiter.wait("example.com")
        elapsed = time.monotonic() - start
        assert elapsed >= 0.05

    @pytest.mark.asyncio
    async def test_different_domains_no_delay(self):
        limiter = RateLimiter(per_domain_delay=0.5, jitter=0)
        start = time.monotonic()
        await limiter.wait("a.com")
        await limiter.wait("b.com")
        elapsed = time.monotonic() - start
        assert elapsed < 0.5

    @pytest.mark.asyncio
    async def test_global_throttle(self):
        limiter = RateLimiter(per_domain_delay=0, global_throttle=3, jitter=0)
        start = time.monotonic()
        for _ in range(4):
            await limiter.wait("test.com")
        elapsed = time.monotonic() - start
        assert elapsed >= 0.3
