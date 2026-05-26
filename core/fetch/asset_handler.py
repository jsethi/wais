from __future__ import annotations
import asyncio
import logging
from pathlib import Path
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from core.hashing.utils import hash_bytes
from core.models.config import AssetConfig

logger = logging.getLogger(__name__)


class AssetHandler:
    def __init__(self, config: AssetConfig, assets_dir: Path, client: httpx.AsyncClient):
        self._config = config
        self._assets_dir = assets_dir
        self._assets_dir.mkdir(parents=True, exist_ok=True)
        self._client = client
        self._seen_hashes: set[str] = set()
        self._asset_count = 0

    @property
    def asset_count(self) -> int:
        return self._asset_count

    def _asset_relative_path(self, page_path: Path) -> str:
        parts = page_path.parent.relative_to(page_path.anchor).parts if page_path.parent != page_path else []
        depth = len(page_path.relative_to(page_path.anchor).parent.parts)
        if depth == 0:
            return "assets/"
        return "../" * depth + "assets/"

    def _is_same_domain(self, asset_url: str, base_url: str) -> bool:
        asset_domain = urlparse(asset_url).netloc
        base_domain = urlparse(base_url).netloc
        if not asset_domain:
            return True
        return asset_domain == base_domain or asset_domain.endswith("." + base_domain)

    async def _fetch_asset(self, asset_url: str) -> bytes | None:
        try:
            resp = await self._client.get(asset_url, timeout=15)
            resp.raise_for_status()
            return resp.content
        except Exception as e:
            logger.debug("Failed to fetch asset %s: %s", asset_url, e)
            return None

    async def rewrite_html(self, html: str, base_url: str, page_path: Path, soup: BeautifulSoup | None = None) -> tuple[str, BeautifulSoup]:
        if not (self._config.images or self._config.css or self._config.js):
            return html, soup or BeautifulSoup(html, "lxml")

        rel = self._asset_relative_path(page_path)
        if soup is None:
            soup = BeautifulSoup(html, "lxml")

        if self._config.css:
            await self._inline_css(soup, base_url)

        if self._config.js:
            await self._inline_js(soup, base_url)

        if self._config.images:
            await self._rewrite_images(soup, base_url, rel)

        return str(soup), soup

    async def _inline_css(self, soup: BeautifulSoup, base_url: str):
        for tag in soup.find_all("link", rel=lambda v: v and "stylesheet" in v):
            href = tag.get("href")
            if not href or href.startswith("data:"):
                continue
            full_url = urljoin(base_url, href)
            if not self._is_same_domain(full_url, base_url):
                continue
            content = await self._fetch_asset(full_url)
            if content is None:
                continue
            sha256 = hash_bytes(content, "sha256")
            if sha256 not in self._seen_hashes:
                self._seen_hashes.add(sha256)
                self._asset_count += 1
            style_tag = soup.new_tag("style")
            style_tag.string = content.decode("utf-8", errors="replace")
            tag.replace_with(style_tag)
            logger.debug("Inlined CSS %s (%d bytes)", full_url, len(content))

    async def _inline_js(self, soup: BeautifulSoup, base_url: str):
        for tag in soup.find_all("script", src=True):
            src = tag.get("src")
            if not src or src.startswith("data:"):
                continue
            full_url = urljoin(base_url, src)
            if not self._is_same_domain(full_url, base_url):
                continue
            content = await self._fetch_asset(full_url)
            if content is None:
                continue
            sha256 = hash_bytes(content, "sha256")
            if sha256 not in self._seen_hashes:
                self._seen_hashes.add(sha256)
                self._asset_count += 1
            del tag["src"]
            tag.string = content.decode("utf-8", errors="replace")
            logger.debug("Inlined JS %s (%d bytes)", full_url, len(content))

    async def _rewrite_images(self, soup: BeautifulSoup, base_url: str, rel: str):
        for tag in soup.find_all("img", src=True):
            src = tag.get("src")
            if not src or src.startswith("data:"):
                continue
            full_url = urljoin(base_url, src)
            if not self._is_same_domain(full_url, base_url):
                continue
            content = await self._fetch_asset(full_url)
            if content is None:
                continue
            ext = Path(urlparse(full_url).path).suffix or ".bin"
            sha256 = hash_bytes(content, "sha256")
            filename = f"{sha256}{ext}"
            if sha256 not in self._seen_hashes:
                self._seen_hashes.add(sha256)
                await asyncio.to_thread((self._assets_dir / filename).write_bytes, content)
                self._asset_count += 1
            tag["src"] = f"{rel}{filename}"
            logger.debug("Rewrote image %s -> %s%s", full_url, rel, filename)
