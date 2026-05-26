from __future__ import annotations
from pathlib import Path

from core.diff.engine import DiffEngine


class TestDiffEngine:
    def test_compare_runs_identical(self, tmp_path):
        run_a = tmp_path / "run_001" / "data"
        run_b = tmp_path / "run_002" / "data"
        run_a.mkdir(parents=True)
        run_b.mkdir(parents=True)
        (run_a / "index.html").write_text("hello")
        (run_b / "index.html").write_text("hello")

        engine = DiffEngine()
        report = engine.compare_runs(run_a, run_b)
        assert len(report.entries) == 0

    def test_compare_runs_different(self, tmp_path):
        run_a = tmp_path / "run_001" / "data"
        run_b = tmp_path / "run_002" / "data"
        run_a.mkdir(parents=True)
        run_b.mkdir(parents=True)
        (run_a / "index.html").write_text("hello")
        (run_b / "index.html").write_text("world")

        engine = DiffEngine()
        report = engine.compare_runs(run_a, run_b)
        assert len(report.entries) == 1
        assert report.entries[0].changes.modified == ["index.html"]

    def test_compare_runs_added_removed(self, tmp_path):
        run_a = tmp_path / "run_001" / "data"
        run_b = tmp_path / "run_002" / "data"
        run_a.mkdir(parents=True)
        run_b.mkdir(parents=True)
        (run_a / "old.html").write_text("old")
        (run_b / "new.html").write_text("new")

        engine = DiffEngine()
        report = engine.compare_runs(run_a, run_b)
        assert len(report.entries) == 2
        removed = [e for e in report.entries if e.changes.removed]
        added = [e for e in report.entries if e.changes.added]
        assert len(removed) == 1
        assert len(added) == 1
