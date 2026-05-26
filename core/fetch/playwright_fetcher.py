from __future__ import annotations
from datetime import datetime, timezone

import httpx
from playwright.async_api import async_playwright

from core.fetch.base import Fetcher, FetchResult
from core.fetch.policy import RequestPolicy
from core.hashing.utils import hash_bytes
from core.models.metadata import FileMeta, Hashes, Timestamps, HTTPInfo, CrawlInfo, RenderingInfo


class PlaywrightFetcher(Fetcher):
    def __init__(self, policy: RequestPolicy | None = None):
        self._policy = policy or RequestPolicy()
        self._playwright = None
        self._browser = None

    async def _ensure_browser(self):
        if self._browser is None:
            try:
                self._playwright = await async_playwright().start()
                self._browser = await self._playwright.chromium.launch(headless=True)
            except Exception as e:
                raise RuntimeError(
                    "Failed to launch Playwright browser. "
                    "Run 'playwright install chromium' to install the browser binary."
                ) from e

    async def check_available(self):
        await self._ensure_browser()
        if self._browser:
            await self._browser.close()
            self._browser = None

    async def fetch(self, url: str, depth: int = 0, parent_url: str = "") -> FetchResult:
        await self._ensure_browser()
        context = await self._browser.new_context(
            user_agent=self._policy.user_agent,
        )
        page = await context.new_page()

        try:
            resp = await page.goto(url, wait_until="domcontentloaded", timeout=self._policy.timeout * 1000)
            content = await page.content()
            content = content.encode("utf-8")
        finally:
            await page.close()
            await context.close()

        content_type = "text/html"
        headers = dict(resp.headers) if resp else {}
        status_code = resp.status if resp else 0
        final_url = page.url
        acquired_at = datetime.now(timezone.utc).isoformat()

        sha256 = hash_bytes(content, "sha256")

        meta = FileMeta(
            file_id=sha256,
            run_id="",
            url=url,
            final_url=final_url,
            file_path="",
            content_type=content_type,
            hashes=Hashes(sha256=sha256),
            timestamps=Timestamps(
                acquired_at=acquired_at,
                response_time=headers.get("date", ""),
                last_modified=headers.get("last-modified"),
            ),
            http=HTTPInfo(
                status_code=status_code,
                headers=headers,
            ),
            crawl=CrawlInfo(
                depth=depth,
                parent_url=parent_url,
            ),
            rendering=RenderingInfo(
                engine="playwright",
                js_rendered=True,
            ),
        )

        return FetchResult(
            content=content,
            content_type=content_type,
            status_code=status_code,
            headers=headers,
            final_url=final_url,
            metadata=meta,
        )

    @property
    def client(self) -> httpx.AsyncClient:
        if not hasattr(self, "_client"):
            self._client = httpx.AsyncClient(timeout=15)
        return self._client

    async def close(self):
        if hasattr(self, "_client"):
            await self._client.aclose()
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
