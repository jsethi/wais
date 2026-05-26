from __future__ import annotations
import asyncio
import logging
from pathlib import Path

import typer

from core.logutil.setup import setup_logging
from core.models.config import WAISConfig
from core.models.state import ResumeMode
from core.state.sqlite_store import SQLiteStore

logger = logging.getLogger(__name__)


def _resolve_data_dir() -> str:
    pkg = Path(__file__).resolve().parent.parent
    if (pkg.parent / "pyproject.toml").exists():
        return str(pkg.parent / "data")
    return "data"


DEFAULT_DATA_DIR = _resolve_data_dir()


def resume_command(
    run_id: str = typer.Argument(..., help="Run ID to resume"),
    mode: str = typer.Option("continue", "--mode", help="Resume mode: continue, skip_completed"),
    data_dir: str = typer.Option(DEFAULT_DATA_DIR, "--data-dir", help="Data directory"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose logging"),
):
    setup_logging("DEBUG" if verbose else "INFO")
    asyncio.run(_resume(run_id, mode, data_dir))


async def _resume(run_id: str, mode: str, data_dir: str):
    state_db_path = f"{data_dir}/state.db"
    store = SQLiteStore(state_db_path)
    await store.open()

    resume_mode = ResumeMode(mode)

    pending = await store.get_pending(run_id, resume_mode)
    stats = await store.get_stats(run_id)

    typer.echo(f"Run {run_id}: {stats.get('total', 0)} total, "
               f"{stats.get('completed', 0)} completed, "
               f"{stats.get('failed', 0)} failed, "
               f"{stats.get('pending', 0)} pending")

    typer.echo(f"Resume mode: {mode}")
    typer.echo(f"URLs remaining: {len(pending)}")

    await store.close()
