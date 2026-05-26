from __future__ import annotations
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class FetchMode(str, Enum):
    html_only = "html_only"
    full_site = "full_site"
    text_only = "text_only"


class RenderEngine(str, Enum):
    requests = "requests"
    playwright = "playwright"


class LayoutMode(str, Enum):
    domain = "domain"
    flat = "flat"


class AssetConfig(BaseModel):
    images: bool = True
    css: bool = True
    js: bool = True
    fonts: bool = False
    media: bool = False


class CrawlConfig(BaseModel):
    max_depth: int = 0
    max_pages: int = 1000
    follow_external_links: bool = False
    include_regex: list[str] = []
    exclude_regex: list[str] = ["logout", "session=", "cart"]
    strip_query_params: bool = False
    sort_query_params: bool = False
    prefer_https: bool = True
    strip_fragments: bool = True
    trailing_slash: str = "preserve"


STEALTH_UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"


class FetchConfig(BaseModel):
    mode: FetchMode = FetchMode.html_only
    render_engine: RenderEngine = RenderEngine.requests
    timeout: int = 30
    max_retries: int = 3
    user_agent: str = STEALTH_UA
    respect_robots_txt: bool = True
    download_assets: AssetConfig = Field(default_factory=AssetConfig)
    rewrite_links: bool = True
    stealth: bool = False


class StorageConfig(BaseModel):
    layout: LayoutMode = LayoutMode.domain
    data_dir: str = "data"
    overwrite: bool = False


class WAISConfig(BaseModel):
    crawl: CrawlConfig = Field(default_factory=CrawlConfig)
    fetch: FetchConfig = Field(default_factory=FetchConfig)
    storage: StorageConfig = Field(default_factory=StorageConfig)
    run_id: str = ""
    concurrency: int = 4
    per_domain_delay: float = Field(default=1.0, ge=0)
    global_throttle: int = 0
