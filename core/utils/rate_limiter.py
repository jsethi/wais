from __future__ import annotations
import asyncio
import random
import time
from collections import deque


class RateLimiter:
    def __init__(self, per_domain_delay: float = 1.0, global_throttle: int = 0, jitter: float = 0.1):
        self._per_domain_delay = per_domain_delay
        self._global_throttle = global_throttle
        self._jitter = jitter
        self._last_fetch: dict[str, float] = {}
        self._global_timestamps: deque[float] = deque()

    async def wait(self, domain: str):
        now = time.monotonic()

        if domain in self._last_fetch:
            elapsed = now - self._last_fetch[domain]
            delay = max(0, self._per_domain_delay + random.uniform(0, self._jitter))
            if elapsed < delay:
                await asyncio.sleep(delay - elapsed)

        if self._global_throttle > 0:
            while self._global_timestamps and now - self._global_timestamps[0] >= 1.0:
                self._global_timestamps.popleft()
            if len(self._global_timestamps) >= self._global_throttle:
                await asyncio.sleep(1.0 - (now - self._global_timestamps[0]))
            self._global_timestamps.append(time.monotonic())

        self._last_fetch[domain] = time.monotonic()
