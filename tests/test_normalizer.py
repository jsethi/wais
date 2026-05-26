from __future__ import annotations

from core.crawl.normalizer import URLNormalizer


class TestURLNormalizer:
    def test_https_upgrade(self):
        n = URLNormalizer(prefer_https=True)
        assert n.normalize("http://example.com") == "https://example.com"

    def test_strip_fragment(self):
        n = URLNormalizer(strip_fragments=True)
        assert n.normalize("https://example.com/page#section") == "https://example.com/page"

    def test_lowercase_domain(self):
        n = URLNormalizer()
        assert n.normalize("https://EXAMPLE.COM/Path") == "https://example.com/Path"

    def test_sort_params(self):
        n = URLNormalizer(sort_params=True)
        result = n.normalize("https://example.com/?b=2&a=1")
        assert "a=1" in result
        assert "b=2" in result
        assert result.index("a=1") < result.index("b=2")

    def test_trailing_slash_add(self):
        n = URLNormalizer(trailing_slash="add")
        assert n.normalize("https://example.com/page") == "https://example.com/page/"

    def test_trailing_slash_remove(self):
        n = URLNormalizer(trailing_slash="remove")
        assert n.normalize("https://example.com/page/") == "https://example.com/page"
