from __future__ import annotations
from enum import Enum
from typing import Optional
from pydantic import BaseModel, HttpUrl


class InputType(str, Enum):
    url = "url"
    file = "file"


class FileFormat(str, Enum):
    csv = "csv"
    json = "json"
    txt = "txt"
    xml = "xml"
    md = "md"


class URLInput(BaseModel):
    type: InputType = InputType.url
    source: str
    depth: int = 0
    tags: list[str] = []


class FileInput(BaseModel):
    type: InputType = InputType.file
    source: str
    format: FileFormat


InputSource = URLInput | FileInput
