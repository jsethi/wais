from __future__ import annotations
import json
from pathlib import Path

import typer

from core.cli.utils import resolve_data_dir
from core.diff.engine import DiffEngine
from core.logutil.setup import setup_logging


DEFAULT_DATA_DIR = resolve_data_dir()


def diff_command(
    run_id_a: str = typer.Argument(..., help="First run ID"),
    run_id_b: str = typer.Argument(..., help="Second run ID"),
    data_dir: str = typer.Option(DEFAULT_DATA_DIR, "--data-dir", help="Data directory"),
    output: str | None = typer.Option(None, "--output", "-o", help="Output diff report to file"),
    verbose: bool = typer.Option(False, "--verbose", "-v"),
):
    setup_logging("DEBUG" if verbose else "INFO")

    base = Path(data_dir) / "runs"
    dir_a = base / run_id_a / "data"
    dir_b = base / run_id_b / "data"

    if not dir_a.exists():
        typer.echo(f"Run {run_id_a} not found at {dir_a}", err=True)
        raise typer.Exit(1)
    if not dir_b.exists():
        typer.echo(f"Run {run_id_b} not found at {dir_b}", err=True)
        raise typer.Exit(1)

    engine = DiffEngine()
    report = engine.compare_runs(dir_a, dir_b)

    if output:
        out_path = Path(output)
        out_path.write_text(report.model_dump_json(indent=2))
        typer.echo(f"Diff report written to {out_path}")
    else:
        typer.echo(report.model_dump_json(indent=2))

    typer.echo(f"Differences found: {len(report.entries)}")
