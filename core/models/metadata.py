from __future__ import annotations
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class Hashes(BaseModel):
    sha256: str


class Timestamps(BaseModel):
    acquired_at: str
    response_time: Optional[str] = None
    last_modified: Optional[str] = None


class HTTPInfo(BaseModel):
    status_code: int
    headers: dict[str, str] = {}


class CrawlInfo(BaseModel):
    depth: int = 0
    parent_url: Optional[str] = None
    referrer: Optional[str] = None


class RenderingInfo(BaseModel):
    engine: str = "requests"
    js_rendered: bool = False


class FileMeta(BaseModel):
    file_id: str
    run_id: str
    url: str
    final_url: str
    file_path: str
    content_type: str
    hashes: Hashes
    timestamps: Timestamps
    http: HTTPInfo
    crawl: CrawlInfo
    rendering: RenderingInfo


class Statistics(BaseModel):
    pages_fetched: int = 0
    assets_downloaded: int = 0
    errors: int = 0


class EnvironmentInfo(BaseModel):
    os: str = ""
    python: str = ""


class RunMeta(BaseModel):
    run_id: str
    timestamps: dict[str, str] = {}
    input: dict = {}
    config: dict = {}
    statistics: Statistics = Field(default_factory=Statistics)
    environment: EnvironmentInfo = Field(default_factory=EnvironmentInfo)
