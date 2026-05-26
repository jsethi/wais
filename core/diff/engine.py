from __future__ import annotations
import json
import logging
from pathlib import Path

from core.hashing.utils import hash_file
from core.models.diff import DiffReport, DiffEntry, DiffType, Changes
from core.models.metadata import FileMeta

logger = logging.getLogger(__name__)


class DiffEngine:
    def compare_runs(self, run_dir_a: Path, run_dir_b: Path) -> DiffReport:
        run_id_a = run_dir_a.parent.name
        run_id_b = run_dir_b.parent.name

        files_a = self._walk_files(run_dir_a)
        files_b = self._walk_files(run_dir_b)

        entries: list[DiffEntry] = []

        all_paths = set(files_a.keys()) | set(files_b.keys())

        for path in sorted(all_paths):
            path_a = files_a.get(path)
            path_b = files_b.get(path)

            if path_a and path_b:
                hash_a = hash_file(str(path_a))
                hash_b = hash_file(str(path_b))
                if hash_a != hash_b:
                    entries.append(DiffEntry(
                        url=self._url_for_sidecar(path_a),
                        diff_type=self._diff_type_for_path(path),
                        changes=Changes(modified=[path]),
                        hash_before=hash_a,
                        hash_after=hash_b,
                    ))
            elif path_a and not path_b:
                hash_a = hash_file(str(path_a))
                entries.append(DiffEntry(
                    url=self._url_for_sidecar(path_a),
                    diff_type=self._diff_type_for_path(path),
                    changes=Changes(removed=[path]),
                    hash_before=hash_a,
                ))
            elif path_b and not path_a:
                hash_b = hash_file(str(path_b))
                entries.append(DiffEntry(
                    url=self._url_for_sidecar(path_b),
                    diff_type=self._diff_type_for_path(path),
                    changes=Changes(added=[path]),
                    hash_after=hash_b,
                ))

        return DiffReport(run_id_a=run_id_a, run_id_b=run_id_b, entries=entries)

    def _walk_files(self, run_dir: Path) -> dict[str, Path]:
        result = {}
        for f in run_dir.glob("**/*"):
            if f.is_file() and not f.name.endswith(".meta.json") and f.name != "run.json":
                relative = f.relative_to(run_dir)
                result[str(relative)] = f
        return result

    def _url_for_sidecar(self, file_path: Path) -> str:
        meta_path = file_path.with_suffix(file_path.suffix + ".meta.json")
        if meta_path.exists():
            try:
                data = json.loads(meta_path.read_text())
                return data.get("url", "")
            except (json.JSONDecodeError, KeyError):
                pass
        return str(file_path)

    def _diff_type_for_path(self, path: str) -> DiffType:
        if path.startswith("assets/"):
            return DiffType.asset
        if path.endswith(".meta.json"):
            return DiffType.metadata
        return DiffType.html
