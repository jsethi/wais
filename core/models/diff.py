from __future__ import annotations
from enum import Enum
from pydantic import BaseModel


class DiffType(str, Enum):
    html = "html"
    asset = "asset"
    metadata = "metadata"


class Changes(BaseModel):
    added: list[str] = []
    removed: list[str] = []
    modified: list[str] = []


class DiffEntry(BaseModel):
    url: str
    diff_type: DiffType
    changes: Changes
    hash_before: str = ""
    hash_after: str = ""


class DiffReport(BaseModel):
    run_id_a: str
    run_id_b: str
    entries: list[DiffEntry] = []
