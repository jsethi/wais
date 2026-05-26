from __future__ import annotations
import logging
import sys


def setup_logging(level: str = "INFO", use_stderr: bool = False):
    handler = logging.StreamHandler(sys.stderr if use_stderr else sys.stdout)
    handler.setFormatter(logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    ))
    root = logging.getLogger("wais")
    root.setLevel(getattr(logging, level.upper(), logging.INFO))
    root.handlers.clear()
    root.addHandler(handler)
