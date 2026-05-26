from __future__ import annotations
import os
from pathlib import Path


def resolve_data_dir() -> str:
    env = os.environ.get("WAIS_DATA_DIR")
    if env:
        return env
    pkg = Path(__file__).resolve().parent.parent
    if (pkg.parent / "pyproject.toml").exists():
        return str(pkg.parent / "data")
    return "data"
