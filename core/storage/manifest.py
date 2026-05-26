from __future__ import annotations
import json
from pathlib import Path


class ManifestWriter:
    def __init__(self, data_dir: Path):
        self._data_dir = data_dir

    def write(self, run_id: str, entries: list[dict]) -> Path:
        manifest_dir = self._data_dir / "runs" / run_id
        manifest_dir.mkdir(parents=True, exist_ok=True)
        path = manifest_dir / "manifest.json"
        path.write_text(json.dumps(entries, indent=2))
        return path
