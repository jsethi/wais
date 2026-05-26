from __future__ import annotations

from core.models.config import WAISConfig, CrawlConfig, FetchConfig, StorageConfig
from core.models.input import URLInput, FileInput
from core.models.metadata import FileMeta, Hashes, Timestamps, HTTPInfo, CrawlInfo, RenderingInfo
from core.models.state import URLState
from core.models.diff import DiffEntry, Changes


class TestInputModels:
    def test_url_input(self):
        inp = URLInput(source="https://example.com", depth=2, tags=["news"])
        assert inp.type.value == "url"
        assert inp.source == "https://example.com"

    def test_file_input(self):
        inp = FileInput(source="urls.csv", format="csv")
        assert inp.type.value == "file"
        assert inp.source == "urls.csv"


class TestConfigModels:
    def test_default_config(self):
        config = WAISConfig()
        assert config.crawl.max_depth == 0
        assert config.fetch.mode.value == "html_only"
        assert config.storage.layout.value == "domain"
        assert config.concurrency == 4

    def test_custom_config(self):
        config = WAISConfig(
            crawl=CrawlConfig(max_depth=5, max_pages=100),
            fetch=FetchConfig(mode="full_site", render_engine="playwright"),
            storage=StorageConfig(layout="flat"),
        )
        assert config.crawl.max_depth == 5
        assert config.fetch.render_engine.value == "playwright"
        assert config.storage.layout.value == "flat"


class TestMetadataModels:
    def test_file_meta(self):
        meta = FileMeta(
            file_id="abc123",
            run_id="run_001",
            url="https://example.com",
            final_url="https://example.com",
            file_path="data/example.com/index.html",
            content_type="text/html",
            hashes=Hashes(sha256="a" * 64, md5="b" * 32),
            timestamps=Timestamps(acquired_at="2024-01-01T00:00:00"),
            http=HTTPInfo(status_code=200),
            crawl=CrawlInfo(depth=0),
            rendering=RenderingInfo(engine="requests", js_rendered=False),
        )
        assert meta.file_id == "abc123"
        assert meta.hashes.sha256 == "a" * 64


class TestStateModels:
    def test_url_state(self):
        state = URLState(url="https://example.com", run_id="run_001")
        assert state.status.value == "pending"
        assert state.depth == 0

    def test_url_state_serialization(self):
        state = URLState(url="https://example.com", status="completed", content_hash="abc")
        d = state.model_dump()
        assert d["status"] == "completed"
        assert d["content_hash"] == "abc"


class TestDiffModels:
    def test_diff_entry(self):
        entry = DiffEntry(
            url="https://example.com",
            diff_type="html",
            changes=Changes(modified=["index.html"]),
            hash_before="aaa",
            hash_after="bbb",
        )
        assert len(entry.changes.modified) == 1
