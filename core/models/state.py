from __future__ import annotations
from enum import Enum
from datetime import datetime
from pydantic import BaseModel


class URLStatus(str, Enum):
    pending = "pending"
    completed = "completed"
    failed = "failed"
    skipped = "skipped"


class ResumeMode(str, Enum):
    continue_ = "continue"
    skip_completed = "skip_completed"
    restart_modified_only = "restart_modified_only"


class URLState(BaseModel):
    url: str
    status: URLStatus = URLStatus.pending
    depth: int = 0
    run_id: str = ""
    content_hash: str = ""
    parent_url: str = ""
    error: str = ""
    fetched_at: str = ""


class ResumeState(BaseModel):
    run_id: str
    mode: ResumeMode
    urls: list[URLState] = []
