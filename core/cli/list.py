from __future__ import annotations
import json
from pathlib import Path

import typer

from core.cli.utils import resolve_data_dir


DEFAULT_DATA_DIR = resolve_data_dir()


def list_command(
    data_dir: str = typer.Option(DEFAULT_DATA_DIR, "--data-dir", help="Data directory"),
    run_id: str | None = typer.Option(None, "--run-id", help="Filter by run ID"),
):
    base = Path(data_dir) / "runs"
    if not base.exists():
        typer.echo("No runs found")
        return

    for run_dir in sorted(base.iterdir()):
        if run_dir.is_dir() and (run_dir / "run.json").exists():
            meta = json.loads((run_dir / "run.json").read_text())
            if run_id and run_id != meta.get("run_id", run_dir.name):
                continue
            timestamps = meta.get("timestamps", {})
            stats = meta.get("statistics", {})
            typer.echo(
                f"  {meta.get('run_id', run_dir.name):12s}  "
                f"pages={stats.get('pages_fetched', 0):5d}  "
                f"errors={stats.get('errors', 0):3d}  "
                f"start={timestamps.get('start', 'N/A')[:19]}"
            )
