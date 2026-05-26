from __future__ import annotations

from core.crawl.filters import URLFilter


class TestURLFilter:
    def test_exclude_regex(self):
        f = URLFilter(exclude_regex=["logout", "session="])
        assert f.is_allowed("https://example.com/page")
        assert not f.is_allowed("https://example.com/logout")
        assert not f.is_allowed("https://example.com/?session=abc")

    def test_domain_allowlist(self):
        f = URLFilter(domain_allowlist=["example.com"])
        assert f.is_allowed("https://example.com/page")
        assert f.is_allowed("https://sub.example.com/page")
        assert not f.is_allowed("https://other.com")

    def test_follow_external_disabled(self):
        f = URLFilter(follow_external=False)
        assert f.is_allowed("https://example.com/page", base_domain="example.com")
        assert not f.is_allowed("https://other.com/page", base_domain="example.com")

    def test_follow_external_enabled(self):
        f = URLFilter(follow_external=True)
        assert f.is_allowed("https://other.com/page", base_domain="example.com")
