from __future__ import annotations
import asyncio
import logging
import re
import time
from collections import Counter, deque
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from core.crawl.filters import URLFilter
from core.crawl.normalizer import URLNormalizer
from core.fetch.asset_handler import AssetHandler
from core.fetch.base import Fetcher
from core.models.config import WAISConfig
from core.models.state import URLState, ResumeMode
from core.state.sqlite_store import SQLiteStore
from core.storage.writer import StorageWriter
from core.utils.rate_limiter import RateLimiter
from core.utils.robots import RobotsChecker

logger = logging.getLogger(__name__)

_CHARSET_RE = re.compile(r'charset=([^;\s]+)', re.IGNORECASE)
_META_CHARSET_RE = re.compile(r'<meta[^>]+charset=["\']?([^"\'\s>]+)', re.IGNORECASE)
_META_CONTENT_TYPE_RE = re.compile(
    r'<meta[^>]+http-equiv=["\']Content-Type["\'][^>]+content=["\']([^"\']+)', re.IGNORECASE
)


def _detect_charset(content: bytes, headers: dict[str, str] | None = None) -> str:
    if headers:
        ct = headers.get("content-type", "") or headers.get("Content-Type", "")
        m = _CHARSET_RE.search(ct)
        if m:
            return m.group(1).strip().lower()
    head = content[:4096].decode("ascii", errors="ignore")
    m = _META_CHARSET_RE.search(head)
    if m:
        return m.group(1).strip().lower()
    m = _META_CONTENT_TYPE_RE.search(head)
    if m:
        cm = _CHARSET_RE.search(m.group(1))
        if cm:
            return cm.group(1).strip().lower()
    return "utf-8"


class CrawlStats:
    def __init__(self, max_pages: int):
        self.pages_fetched = 0
        self.assets_downloaded = 0
        self.errors = 0
        self.skipped = 0
        self.max_pages = max_pages
        self.current_url = ""
        self.current_domain = ""
        self.start_time = time.monotonic()
        self.domains: Counter[str] = Counter()
        self.done = False


class CrawlEngine:
    def __init__(
        self,
        config: WAISConfig,
        fetcher: Fetcher,
        store: SQLiteStore,
        writer: StorageWriter,
        asset_handler: AssetHandler | None = None,
        stats: CrawlStats | None = None,
    ):
        self._config = config
        self._fetcher = fetcher
        self._store = store
        self._writer = writer
        self._asset_handler = asset_handler
        self._stats = stats or CrawlStats(config.crawl.max_pages)
        self._normalizer = URLNormalizer(
            prefer_https=config.crawl.prefer_https,
            strip_fragments=config.crawl.strip_fragments,
            sort_params=config.crawl.sort_query_params,
            trailing_slash=config.crawl.trailing_slash,
        )
        self._filter = URLFilter(
            include_regex=config.crawl.include_regex,
            exclude_regex=config.crawl.exclude_regex,
            follow_external=config.crawl.follow_external_links,
        )
        self._rate_limiter = RateLimiter(
            per_domain_delay=config.per_domain_delay,
            global_throttle=config.global_throttle,
        )
        self._semaphore = asyncio.Semaphore(config.concurrency)

        self._robots_checker: RobotsChecker | None = None
        if config.fetch.respect_robots_txt:
            self._robots_checker = RobotsChecker(user_agent=config.fetch.user_agent)

    @property
    def stats(self) -> CrawlStats:
        return self._stats

    async def crawl(self, start_urls: list[str], run_id: str, resume_mode: ResumeMode | None = None):
        s = self._stats
        s.start_time = time.monotonic()
        logger.info("Starting crawl run_id=%s with %d seed URLs", run_id, len(start_urls))

        max_depth = self._config.crawl.max_depth
        await self._store.add_urls(
            [{"url": u, "depth": 0, "parent_url": ""} for u in start_urls if 0 <= max_depth],
            run_id,
        )

        pending = await self._store.get_pending(run_id, resume_mode=resume_mode, limit=s.max_pages)
        queue = deque(pending)

        while queue and s.pages_fetched < s.max_pages:
            batch = []
            while queue and len(batch) < self._config.concurrency:
                batch.append(queue.popleft())

            tasks = [self._fetch_url(state.url, state.depth, run_id) for state in batch]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for state, result in zip(batch, results):
                if isinstance(result, Exception):
                    logger.error("Failed to fetch %s: %s", state.url, result)
                    s.errors += 1
                    await self._store.mark_failed(state.url, run_id, str(result))
                elif result:
                    new_urls = result
                    if state.depth + 1 <= max_depth:
                        await self._store.add_urls(
                            [{"url": u, "depth": state.depth + 1, "parent_url": state.url} for u in new_urls],
                            run_id,
                        )
                        for u in new_urls:
                            queue.append(URLState(url=u, depth=state.depth + 1, run_id=run_id))

        s.done = True
        if self._asset_handler:
            s.assets_downloaded = self._asset_handler.asset_count

        logger.info("Crawl complete: %d pages, %d errors", s.pages_fetched, s.errors)

    async def _fetch_url(self, url: str, depth: int, run_id: str) -> list[str] | None:
        domain = urlparse(url).netloc
        await self._rate_limiter.wait(domain)

        if self._robots_checker and not await self._robots_checker.can_fetch(url):
            self._stats.skipped += 1
            logger.debug("Skipped (robots.txt): %s", url)
            return None

        async with self._semaphore:
            self._stats.current_url = url
            self._stats.current_domain = domain

            if depth > self._config.crawl.max_depth:
                return None

            try:
                result = await self._fetcher.fetch(url, depth=depth)
            except Exception as e:
                logger.error("Fetch failed: %s - %s", url, e)
                raise

            self._stats.domains[domain] += 1
            logger.info("Fetched [%d] %s", result.status_code, url)

            content = result.content
            soup: BeautifulSoup | None = None
            if self._asset_handler and self._config.fetch.mode.value == "full_site":
                page_path = self._writer.resolve_path(result.final_url, run_id)
                charset = _detect_charset(content, result.headers)
                decoded = content.decode(charset, errors="replace")
                decoded, soup = await self._asset_handler.rewrite_html(decoded, url, page_path)
                content = decoded.encode("utf-8")
                result.content = content

            _, was_skipped = await self._writer.write_page(result, run_id)

            if was_skipped:
                self._stats.skipped += 1
            else:
                self._stats.pages_fetched += 1

            await self._store.mark_completed(url, run_id, result.metadata.hashes.sha256 if result.metadata else "")

            if depth >= self._config.crawl.max_depth:
                return None

            return self._extract_links(content, url, soup)

    def _extract_links(self, content: bytes, base_url: str, soup: BeautifulSoup | None = None) -> list[str]:
        if soup is None:
            if not content:
                return []
            try:
                soup = BeautifulSoup(content.decode("utf-8", errors="replace"), "lxml")
            except Exception:
                return []

        links = []
        base_domain = urlparse(base_url).netloc

        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            if not href or href.startswith(("#", "//", "javascript:", "mailto:")):
                continue
            full_url = urljoin(base_url, href)
            normalized = self._normalizer.normalize(full_url)

            if self._filter.is_allowed(normalized, base_domain):
                links.append(normalized)

        return links
