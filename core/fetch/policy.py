from __future__ import annotations
import asyncio
import logging
import random

import httpx

logger = logging.getLogger(__name__)

_RETRYABLE = (
    httpx.ConnectError,
    httpx.ConnectTimeout,
    httpx.ReadTimeout,
    httpx.WriteTimeout,
    httpx.PoolTimeout,
    httpx.RemoteProtocolError,
    ConnectionResetError,
    TimeoutError,
    asyncio.TimeoutError,
)


UAS = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0",
)

STEALTH_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Sec-Ch-Ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Linux"',
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
    "Dnt": "1",
    "Connection": "keep-alive",
}


class RequestPolicy:
    def __init__(
        self,
        timeout: int = 30,
        max_retries: int = 3,
        user_agent: str = "",
        stealth: bool = False,
    ):
        self.timeout = timeout
        self.max_retries = max_retries
        self.stealth = stealth
        self._uas: tuple[str, ...] | None = None
        if stealth and not user_agent:
            self._uas = UAS
            self.user_agent = UAS[0]
        else:
            self.user_agent = user_agent or UAS[2]
        self._cached_headers = self._build_headers()

    def _build_headers(self) -> dict[str, str]:
        if self.stealth and self._uas:
            ua = random.choice(self._uas)
        else:
            ua = self.user_agent
        h = {"User-Agent": ua}
        if self.stealth:
            h.update(STEALTH_HEADERS)
            h["User-Agent"] = ua
            h["Accept-Language"] = random.choice(["en-US,en;q=0.9", "en-GB,en;q=0.8", "en-US,en;q=0.7"])
        return h

    @property
    def headers(self) -> dict[str, str]:
        return dict(self._cached_headers)

    async def retry(self, url: str, fetch_fn, *args, **kwargs):
        last_exc = None
        for attempt in range(1, self.max_retries + 1):
            try:
                return await fetch_fn(*args, **kwargs)
            except _RETRYABLE as e:
                last_exc = e
                logger.warning("Attempt %d/%d failed for %s: %s", attempt, self.max_retries, url, e)
                if attempt < self.max_retries:
                    wait = (2 ** attempt) + (random.uniform(0, 1) if self.stealth else 0)
                    logger.info("Backing off %.1fs before retry %s", wait, url)
                    await asyncio.sleep(wait)
            except Exception as e:
                logger.error("Non-retryable error for %s: %s", url, e)
                raise
        raise last_exc
