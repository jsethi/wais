from __future__ import annotations
import asyncio
import logging
from urllib.parse import urlparse, urlunparse
from urllib.robotparser import RobotFileParser

logger = logging.getLogger(__name__)


class RobotsChecker:
    def __init__(self, user_agent: str):
        self._user_agent = user_agent
        self._parsers: dict[str, RobotFileParser] = {}

    async def can_fetch(self, url: str) -> bool:
        parsed = urlparse(url)
        base = f"{parsed.scheme}://{parsed.netloc}"
        if base not in self._parsers:
            rp = RobotFileParser(
                urlunparse((parsed.scheme, parsed.netloc, "/robots.txt", "", "", ""))
            )
            try:
                await asyncio.to_thread(rp.read)
            except Exception as e:
                logger.debug("Failed to read robots.txt for %s: %s", base, e)
                self._parsers[base] = rp
                return True
            self._parsers[base] = rp
        return self._parsers[base].can_fetch(self._user_agent, url)
