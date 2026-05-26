from __future__ import annotations
import json
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def tmp_data_dir():
    with tempfile.TemporaryDirectory() as d:
        yield Path(d)


@pytest.fixture
def sample_csv(tmp_path):
    path = tmp_path / "urls.csv"
    path.write_text("url,depth,tags\nhttps://example.com,0,test\nhttps://httpbin.org,1,api\n")
    return str(path)


@pytest.fixture
def sample_json(tmp_path):
    path = tmp_path / "urls.json"
    data = [
        {"url": "https://example.com", "params": {"depth": 0, "tags": ["test"]}},
        {"url": "https://httpbin.org", "params": {"depth": 1, "tags": ["api"]}},
    ]
    path.write_text(json.dumps(data))
    return str(path)


@pytest.fixture
def sample_txt(tmp_path):
    path = tmp_path / "urls.txt"
    path.write_text("https://example.com\n# comment\nhttps://httpbin.org\n")
    return str(path)


@pytest.fixture
def sample_xml(tmp_path):
    path = tmp_path / "urls.xml"
    path.write_text(
        '<?xml version="1.0"?>\n<urls>\n'
        '  <url depth="0" tags="test">https://example.com</url>\n'
        '  <url depth="1">https://httpbin.org</url>\n'
        "</urls>"
    )
    return str(path)


@pytest.fixture
def sample_md(tmp_path):
    path = tmp_path / "links.md"
    path.write_text(
        "# Links\n\n"
        "Check [Example](https://example.com) and "
        "[HTTPBin](https://httpbin.org)\n"
    )
    return str(path)
