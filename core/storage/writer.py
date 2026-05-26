from __future__ import annotations
import asyncio
import json
import logging
from pathlib import Path

from core.fetch.base import FetchResult
from core.models.config import StorageConfig
from core.models.metadata import FileMeta, RunMeta
from core.storage.layout import DomainHierarchyLayout, FlatLayout

logger = logging.getLogger(__name__)


class StorageWriter:
    def __init__(self, config: StorageConfig):
        self._config = config
        self._layout = self._build_layout()
        self._data_dir = Path(config.data_dir)

    def _build_layout(self):
        if self._config.layout.value == "domain":
            return DomainHierarchyLayout()
        return FlatLayout()

    def resolve_path(self, url: str, run_id: str = "") -> Path:
        base = self._data_dir
        if run_id:
            base = base / "runs" / run_id / "data"
        return self._layout.resolve_path(url, base)

    async def write_page(self, result: FetchResult, run_id: str) -> tuple[Path, bool]:
        url = result.final_url or (result.metadata.url if result.metadata else "")
        out_path = self.resolve_path(url, run_id)
        await asyncio.to_thread(out_path.parent.mkdir, parents=True, exist_ok=True)

        if out_path.exists() and not self._config.overwrite:
            logger.debug("Skipping existing %s (overwrite=False)", out_path)
            return out_path, True

        await asyncio.to_thread(out_path.write_bytes, result.content)
        logger.info("Wrote %s (%d bytes)", out_path, len(result.content))

        if result.metadata:
            result.metadata.run_id = run_id
            result.metadata.file_path = str(out_path)
            await self._write_sidecar(out_path, result.metadata)

        return out_path, False

    async def write_asset(self, content: bytes, asset_path: str, run_id: str = "") -> Path:
        base = self._data_dir
        if run_id:
            base = base / "runs" / run_id / "data"
        full_path = base / asset_path
        await asyncio.to_thread(full_path.parent.mkdir, parents=True, exist_ok=True)
        await asyncio.to_thread(full_path.write_bytes, content)
        return full_path

    async def _write_sidecar(self, file_path: Path, meta: FileMeta) -> None:
        meta_path = file_path.with_suffix(file_path.suffix + ".meta.json")
        await asyncio.to_thread(meta_path.write_text, meta.model_dump_json(indent=2))
        logger.debug("Wrote metadata sidecar %s", meta_path)

    async def write_run_meta(self, run_meta: RunMeta) -> Path:
        meta_dir = self._data_dir / "runs" / run_meta.run_id
        await asyncio.to_thread(meta_dir.mkdir, parents=True, exist_ok=True)
        meta_path = meta_dir / "run.json"
        await asyncio.to_thread(meta_path.write_text, run_meta.model_dump_json(indent=2))
        return meta_path
