from __future__ import annotations
import re
from urllib.parse import urlparse


class URLFilter:
    def __init__(self, include_regex: list[str] | None = None, exclude_regex: list[str] | None = None, domain_allowlist: list[str] | None = None, follow_external: bool = False):
        self._include = [re.compile(p) for p in (include_regex or [])]
        self._exclude = [re.compile(p) for p in (exclude_regex or [])]
        self._domain_allowlist = domain_allowlist or []
        self._follow_external = follow_external

    def is_allowed(self, url: str, base_domain: str = "") -> bool:
        parsed = urlparse(url)

        if not parsed.netloc:
            return False

        if self._include:
            if not any(p.search(url) for p in self._include):
                return False

        for pattern in self._exclude:
            if pattern.search(url):
                return False

        if self._domain_allowlist:
            domain = parsed.netloc.lower()
            if not any(domain == d.lower() or domain.endswith("." + d.lower()) for d in self._domain_allowlist):
                return False

        if not self._follow_external and base_domain:
            domain = parsed.netloc.lower()
            if domain != base_domain.lower() and not domain.endswith("." + base_domain.lower()):
                return False

        return True
