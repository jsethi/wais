from __future__ import annotations
from urllib.parse import urlparse, urlunparse, urlencode, parse_qsl


class URLNormalizer:
    def __init__(self, prefer_https: bool = True, strip_fragments: bool = True, sort_params: bool = False, trailing_slash: str = "preserve"):
        self._prefer_https = prefer_https
        self._strip_fragments = strip_fragments
        self._sort_params = sort_params
        self._trailing_slash = trailing_slash

    def normalize(self, url: str) -> str:
        parsed = urlparse(url.strip())

        scheme = "https" if (self._prefer_https and parsed.scheme == "http") else parsed.scheme

        path = parsed.path
        if self._trailing_slash == "add":
            if not path.endswith("/"):
                path += "/"
        elif self._trailing_slash == "remove":
            if path.endswith("/") and len(path) > 1:
                path = path.rstrip("/")

        query = parsed.query
        if self._sort_params:
            params = parse_qsl(query, keep_blank_values=True)
            params.sort(key=lambda x: x[0])
            query = urlencode(params)

        fragment = "" if self._strip_fragments else parsed.fragment

        return urlunparse((scheme, parsed.netloc.lower(), path, parsed.params, query, fragment))
