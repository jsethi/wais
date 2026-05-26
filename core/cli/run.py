from __future__ import annotations
import asyncio
import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import typer
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.table import Table

from core.crawl.engine import CrawlEngine, CrawlStats
from core.fetch.asset_handler import AssetHandler
from core.fetch.policy import RequestPolicy
from core.fetch.requests_fetcher import RequestsFetcher
from core.loaders.csv_loader import CSVLoader
from core.loaders.json_loader import JSONLoader
from core.loaders.md_loader import MDLoader
from core.loaders.single import SingleURLLoader
from core.loaders.txt_loader import TxtLoader
from core.loaders.xml_loader import XMLLoader
from core.cli.utils import resolve_data_dir
from core.logutil.setup import setup_logging
from core.models.config import WAISConfig, CrawlConfig, FetchConfig, StorageConfig, AssetConfig
from core.models.metadata import RunMeta, Statistics, EnvironmentInfo
from core.models.state import ResumeMode
from core.state.sqlite_store import SQLiteStore
from core.storage.writer import StorageWriter
logger = logging.getLogger(__name__)
console = Console()


DEFAULT_DATA_DIR = resolve_data_dir()


def run_command(
    url: str | None = typer.Option(None, "--url", help="Single URL to archive"),
    input: str | None = typer.Option(None, "--input", help="Input file path"),
    format: str | None = typer.Option(None, "--format", help="Input file format (csv/json/txt/xml/md)"),
    data_dir: str = typer.Option(DEFAULT_DATA_DIR, "--data-dir", help="Data output directory"),
    mode: str = typer.Option("html_only", "--mode", help="Fetch mode: html_only, full_site, text_only"),
    render: str = typer.Option("requests", "--render", help="Render engine: requests, playwright"),
    depth: int = typer.Option(0, "--depth", help="Maximum crawl depth (0 = single page)"),
    max_pages: int = typer.Option(1000, "--max-pages", help="Maximum pages to fetch"),
    concurrency: int = typer.Option(4, "--concurrency", help="Concurrent fetches"),
    domain_delay: float = typer.Option(1.0, "--domain-delay", help="Delay between requests to same domain"),
    resume: str | None = typer.Option(None, "--resume", help="Resume mode: continue, skip_completed"),
    overwrite: bool = typer.Option(False, "--overwrite", help="Overwrite existing files"),
    fresh: bool = typer.Option(False, "--fresh", help="Re-fetch all URLs (overwrite + clear state)"),
    respect_robots: bool = typer.Option(True, "--respect-robots/--ignore-robots", help="Respect robots.txt (disable for research archiving)"),
    user_agent: str | None = typer.Option(None, "--user-agent", help="Custom User-Agent string (overrides stealth UA rotation)"),
    stealth: bool = typer.Option(False, "--stealth", help="Stealth mode: realistic browser headers + per-request UA rotation + jitter"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose logging"),
):
    setup_logging("DEBUG" if verbose else "WARNING", use_stderr=not verbose)

    config = WAISConfig(
        crawl=CrawlConfig(max_depth=depth, max_pages=max_pages),
        fetch=FetchConfig(mode=mode, render_engine=render, user_agent=user_agent or "", stealth=stealth, respect_robots_txt=respect_robots),
        storage=StorageConfig(data_dir=data_dir, overwrite=overwrite or fresh),
        concurrency=concurrency,
        per_domain_delay=domain_delay,
    )

    run_id = uuid4().hex[:12]
    config.run_id = run_id

    data_path = Path(data_dir)
    data_path.mkdir(parents=True, exist_ok=True)

    state_db_path = data_path / "state.db"
    start_time = datetime.now(timezone.utc)

    if not verbose:
        flags = f" [dim]{'stealth' if config.fetch.stealth else ''}{' fresh' if fresh else ''}[/]"
        console.print(f"[bold cyan]WAIS[/] v1.0 — Run [yellow]{run_id}[/]{flags}")
        console.print()

    stats, pages, errors, assets_dl, elapsed = asyncio.run(
        _run(config, url, input, format, run_id, str(state_db_path), verbose, resume)
    )

    elapsed_str = _format_duration(elapsed)
    end_time = datetime.now(timezone.utc)

    if not verbose:
        console.print()
        summary = Table.grid(padding=(0, 2))
        summary.add_row("[bold]Run[/]", f"[yellow]{run_id}[/]")
        summary.add_row("[bold]Pages[/]", f"[green]{pages}[/]")
        summary.add_row("[bold]Assets[/]", f"[blue]{assets_dl}[/]")
        summary.add_row("[bold]Errors[/]", f"[red]{errors}[/]")
        summary.add_row("[bold]Elapsed[/]", elapsed_str)
        summary.add_row("[bold]Finished[/]", end_time.strftime("%Y-%m-%d %H:%M:%S UTC"))
        console.print(Panel(summary, title="[bold]Complete[/]", border_style="green"))
    else:
        typer.echo(f"Run {run_id} complete: {pages} pages, {assets_dl} assets, {errors} errors in {elapsed_str}")


async def _run(
    config: WAISConfig,
    url: str | None,
    input_path: str | None,
    fmt: str | None,
    run_id: str,
    state_db_path: str,
    verbose: bool,
    resume: str | None = None,
) -> tuple[CrawlStats, int, int, int, float]:
    resume_mode: ResumeMode | None = None
    if resume:
        try:
            resume_mode = ResumeMode(resume)
        except ValueError:
            typer.echo(f"Invalid resume mode: {resume} (options: continue, skip_completed)", err=True)
            raise typer.Exit(1)

    run_start = datetime.now(timezone.utc)

    if url:
        from core.loaders.single import SingleURLLoader
        loader = SingleURLLoader(url)
    elif input_path:
        loader_map = {
            "csv": CSVLoader,
            "json": JSONLoader,
            "txt": TxtLoader,
            "xml": XMLLoader,
            "md": MDLoader,
        }
        if fmt:
            loader_cls = loader_map.get(fmt)
            if not loader_cls:
                typer.echo(f"Unsupported format: {fmt}", err=True)
                raise typer.Exit(1)
            loader = loader_cls(input_path)
        else:
            ext = Path(input_path).suffix.lstrip(".").lower()
            loader_cls = loader_map.get(ext)
            if not loader_cls:
                typer.echo(f"Cannot detect format from extension: {ext}", err=True)
                raise typer.Exit(1)
            loader = loader_cls(input_path)
    else:
        typer.echo("Provide --url or --input", err=True)
        raise typer.Exit(1)

    inputs = list(loader.load())

    policy = RequestPolicy(
        timeout=config.fetch.timeout,
        max_retries=config.fetch.max_retries,
        user_agent=config.fetch.user_agent,
        stealth=config.fetch.stealth,
    )

    if config.fetch.render_engine.value == "playwright":
        from core.fetch.playwright_fetcher import PlaywrightFetcher
        fetcher = PlaywrightFetcher(policy)
        await fetcher.check_available()
    else:
        fetcher = RequestsFetcher(policy)

    store = SQLiteStore(state_db_path)
    await store.open()

    if config.storage.overwrite and fresh:
        logger.info("Clearing state for run %s (--fresh)", run_id)
        await store.clear_run(run_id)

    writer = StorageWriter(config.storage)

    asset_handler = None
    assets_dir = Path(config.storage.data_dir) / "runs" / run_id / "data" / "assets"
    if config.fetch.mode.value == "full_site":
        asset_handler = AssetHandler(
            config.fetch.download_assets,
            assets_dir,
            fetcher.client,
        )

    stats = CrawlStats(config.crawl.max_pages)

    engine = CrawlEngine(config, fetcher, store, writer, asset_handler, stats)

    if not verbose:
        await _run_with_progress(engine, [i.source for i in inputs], run_id, stats, resume_mode=resume_mode)
    else:
        await engine.crawl([i.source for i in inputs], run_id, resume_mode=resume_mode)

    elapsed = time.monotonic() - stats.start_time

    db_stats = await store.get_stats(run_id)
    run_meta = RunMeta(
        run_id=run_id,
        timestamps={
            "start": run_start.isoformat(),
            "end": datetime.now(timezone.utc).isoformat(),
        },
        input={"url": url} if url else {"input": input_path},
        config=config.model_dump(mode="json"),
        statistics=Statistics(
            pages_fetched=db_stats.get("completed", 0),
            assets_downloaded=stats.assets_downloaded,
            errors=db_stats.get("failed", 0),
        ),
        environment=EnvironmentInfo(
            os=os.name,
            python=__import__("sys").version,
        ),
    )
    await writer.write_run_meta(run_meta)

    await store.close()
    await fetcher.close()

    return stats, db_stats.get("completed", 0), db_stats.get("failed", 0), stats.assets_downloaded, elapsed


def _render_progress(stats: CrawlStats, run_id: str) -> Panel:
    url_text = stats.current_url
    if len(url_text) > 90:
        url_text = url_text[:87] + "..."
    elapsed = time.monotonic() - stats.start_time
    rate = stats.pages_fetched / elapsed if elapsed > 0 else 0
    top_domains = stats.domains.most_common(5)
    domains_str = "  ".join(f"{d} ({c})" for d, c in top_domains) if top_domains else "—"
    pct = f"{stats.pages_fetched / max(stats.max_pages, 1) * 100:.0f}%"
    bar_len = 20
    filled = int(stats.pages_fetched / max(stats.max_pages, 1) * bar_len)
    bar = "█" * filled + "░" * (bar_len - filled)
    progress_text = (
        f"  [green]Pages[/] {stats.pages_fetched}/{stats.max_pages}  "
        f"{bar} {pct}  "
        f"[bold]{rate:.1f}/s[/]\n"
    )
    skipped_str = f"  [dim]Skipped[/] {stats.skipped}" if stats.skipped else ""
    status_text = (
        f"  [bold]Fetched[/] {stats.pages_fetched}  "
        f"[bold]Errors[/] [red]{stats.errors}[/]  "
        f"[bold]Assets[/] {stats.assets_downloaded}"
        f"{skipped_str}\n"
        f"  [dim]URL:[/] {url_text}\n"
        f"  [dim]Domains:[/] {domains_str}"
    )
    return Panel(
        f"{progress_text}{status_text}",
        title=f"[yellow]{run_id}[/]",
        border_style="blue",
    )


async def _run_with_progress(engine: CrawlEngine, start_urls: list[str], run_id: str, stats: CrawlStats, resume_mode: ResumeMode | None = None):
    with Live(refresh_per_second=4) as live:
        crawl_task = asyncio.create_task(engine.crawl(start_urls, run_id, resume_mode=resume_mode))

        try:
            live.update(_render_progress(stats, run_id))
        except Exception:
            logger.exception("Initial progress render failed")

        try:
            while not crawl_task.done():
                live.update(_render_progress(stats, run_id))
                await asyncio.sleep(0.25)
        except Exception:
            logger.exception("Progress render crashed, continuing without display")
            while not crawl_task.done():
                await asyncio.sleep(0.5)

        await crawl_task

        try:
            live.update(_render_progress(stats, run_id))
        except Exception:
            logger.exception("Final progress render failed")


def _format_duration(seconds: float) -> str:
    hours, remainder = divmod(int(seconds), 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours}h {minutes:02d}m {secs:02d}s"
    if minutes:
        return f"{minutes}m {secs:02d}s"
    return f"{secs}s"
