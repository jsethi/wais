from __future__ import annotations
from datetime import datetime, timezone

import httpx

from core.fetch.base import Fetcher, FetchResult
from core.fetch.policy import RequestPolicy
from core.hashing.utils import hash_bytes
from core.models.metadata import FileMeta, Hashes, Timestamps, HTTPInfo, CrawlInfo, RenderingInfo


class RequestsFetcher(Fetcher):
    def __init__(self, policy: RequestPolicy | None = None):
        self._policy = policy or RequestPolicy()
        self._client = httpx.AsyncClient(
            timeout=self._policy.timeout,
            follow_redirects=True,
            headers=self._policy.headers,
        )

    async def fetch(self, url: str, depth: int = 0, parent_url: str = "") -> FetchResult:
        if self._policy.stealth and parent_url:
            headers = {**self._policy.headers, "Referer": parent_url}
            resp = await self._policy.retry(url, self._client.get, url, headers=headers)
        else:
            resp = await self._policy.retry(url, self._client.get, url)

        content = resp.content
        content_type = resp.headers.get("content-type", "text/html").split(";")[0]
        headers = dict(resp.headers)
        final_url = str(resp.url)
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
                response_time=resp.headers.get("date", ""),
                last_modified=resp.headers.get("last-modified"),
            ),
            http=HTTPInfo(
                status_code=resp.status_code,
                headers=headers,
            ),
            crawl=CrawlInfo(
                depth=depth,
                parent_url=parent_url,
            ),
            rendering=RenderingInfo(
                engine="requests",
                js_rendered=False,
            ),
        )

        return FetchResult(
            content=content,
            content_type=content_type,
            status_code=resp.status_code,
            headers=headers,
            final_url=final_url,
            metadata=meta,
        )

    @property
    def client(self) -> httpx.AsyncClient:
        return self._client

    async def close(self):
        await self._client.aclose()
