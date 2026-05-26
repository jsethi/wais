from __future__ import annotations
from pathlib import Path

from core.models.config import StorageConfig
from core.storage.layout import DomainHierarchyLayout, FlatLayout
from core.storage.writer import StorageWriter


class TestDomainHierarchyLayout:
    def test_simple_url(self):
        layout = DomainHierarchyLayout()
        result = layout.resolve_path("https://example.com/page", Path("/base"))
        assert str(result) == "/base/example.com/page/index.html"

    def test_url_with_path(self):
        layout = DomainHierarchyLayout()
        result = layout.resolve_path("https://example.com/blog/post.html", Path("/base"))
        assert str(result) == "/base/example.com/blog/post.html"

    def test_url_root(self):
        layout = DomainHierarchyLayout()
        result = layout.resolve_path("https://example.com", Path("/base"))
        assert str(result) == "/base/example.com/index.html"

    def test_non_html_extension_normalized(self):
        layout = DomainHierarchyLayout()
        result = layout.resolve_path("https://example.com/page.php", Path("/base"))
        assert str(result) == "/base/example.com/page.html"

    def test_htm_extension_normalized(self):
        layout = DomainHierarchyLayout()
        result = layout.resolve_path("https://example.com/page.htm", Path("/base"))
        assert str(result) == "/base/example.com/page.html"


class TestFlatLayout:
    def test_flat_output(self):
        layout = FlatLayout()
        result = layout.resolve_path("https://example.com/page", Path("/base"))
        assert str(result).startswith("/base/")
        assert str(result).endswith(".html")


class TestStorageWriter:
    def test_writer_initialization(self, tmp_data_dir):
        config = StorageConfig(data_dir=str(tmp_data_dir))
        writer = StorageWriter(config)
        assert writer._data_dir == tmp_data_dir
