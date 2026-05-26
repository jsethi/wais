# WAIS — Web Archival & Ingestion System v1.0

Deterministic, reproducible web content archiving. Fetch, store, track, and diff web pages with full provenance metadata.

## Quick Start

```bash
pip install wais
playwright install chromium        # only if using JS rendering

wais run --url https://example.com
wais run --url https://example.com --render playwright --mode full_site
wais run --input urls.csv --depth 2 --concurrency 8
wais list
wais diff <run_id_a> <run_id_b>     # compare two runs' snapshots
```

---

## Table of Contents

- [Installation](#installation)
- [CLI Reference](#cli-reference)
  - [`wais run`](#wais-run)
  - [`wais list`](#wais-list)
  - [`wais diff`](#wais-diff)
  - [`wais resume`](#wais-resume)
- [Input Formats](#input-formats)
  - [Single URL](#single-url)
  - [CSV](#csv-format)
  - [JSON](#json-format)
  - [TXT](#txt-format)
  - [XML](#xml-format)
  - [Markdown](#markdown-format)
- [Output Layout](#output-layout)
  - [Domain Hierarchy (default)](#domain-hierarchy-default)
  - [Flat Mode](#flat-mode)
- [Metadata Sidecars](#metadata-sidecars)
  - [File-level Metadata](#file-level-metadata)
  - [Run-level Metadata](#run-level-metadata)
- [Fetch Modes & Rendering](#fetch-modes--rendering)
- [Crawl Engine](#crawl-engine)
  - [URL Normalization](#url-normalization)
  - [URL Filtering](#url-filtering)
- [Asset Handling](#asset-handling)
- [Diff Engine](#diff-engine)
- [State & Resume](#state--resume)
- [Rate Limiting](#rate-limiting)
- [Environment Variables](#environment-variables)
- [Architecture](#architecture)
- [Development](#development)

---

## Installation

```bash
pip install wais
```

JS rendering requires Playwright browsers:

```bash
playwright install chromium
```

### Dependencies

| Package     | Minimum | Purpose                  |
|-------------|---------|--------------------------|
| typer       | 0.12    | CLI framework            |
| pydantic    | 2.0     | Schema validation        |
| httpx       | 0.27    | Async HTTP client        |
| requests    | 2.31    | Sync HTTP fallback       |
| aiosqlite   | 0.20    | Async SQLite state store |
| beautifulsoup4 | 4.12 | HTML parsing             |
| lxml        | 5.0     | Fast HTML/XML parser     |
| playwright  | 1.40    | Headless Chromium        |

### Dev Dependencies

```bash
pip install "wais[dev]"
# pytest, pytest-asyncio, vcrpy, pytest-vcr, ruff
```

---

## CLI Reference

### `wais run`

Archive a single URL or batch of URLs.

```bash
wais run --url <url> [options]
wais run --input <file> [options]
```

| Option            | Default        | Description                                      |
|-------------------|----------------|--------------------------------------------------|
| `--url`           | —              | Single URL to archive                            |
| `--input`         | —              | Input file path (CSV/JSON/TXT/XML/MD)            |
| `--format`        | auto-detect    | Force input format: `csv`, `json`, `txt`, `xml`, `md` |
| `--data-dir`      | `data`(CWD) or `<project>/data` | Output directory (auto-detects project root) |
| `--mode`          | `html_only`    | Fetch mode: `html_only`, `full_site`, `text_only` |
| `--render`        | `requests`     | Render engine: `requests`, `playwright`          |
| `--depth`         | `0`            | Maximum crawl depth (0 = single page, no link following) |
| `--max-pages`     | `1000`         | Maximum pages to fetch in a single run           |
| `--concurrency`   | `4`            | Number of concurrent fetches                     |
| `--domain-delay`  | `1.0`          | Seconds to wait between requests to the same domain |
| `--resume`        | —              | Resume mode: `continue`, `skip_completed`        |
| `--overwrite`     | `False`        | Re-fetch and overwrite existing files            |
| `--fresh`         | `False`        | Force re-fetch, clearing prior state for URLs    |
| `--respect-robots/--ignore-robots` | `--respect-robots` | Respect robots.txt (use `--ignore-robots` for research archiving) |
| `--stealth`       | `False`        | Realistic browser headers, per-request UA rotation, jitter |
| `--user-agent`    | —              | Custom User-Agent string (disables stealth UA rotation) |
| `-v`, `--verbose` | `False`        | DEBUG-level logging                              |

**Examples:**

```bash
# Single page, no crawl (default)
wais run --url https://example.com

# Full site with asset download, JS rendering
wais run --url https://example.com --mode full_site --render playwright --depth 2

# Batch from CSV with 8 concurrent workers
wais run --input urls.csv --concurrency 8 --depth 2

# Re-fetch previously archived URLs
wais run --url https://example.com --fresh

# Research archiving: stealth + bypass robots.txt + full crawl
wais run --url https://example.com --stealth --ignore-robots --depth 3 --mode full_site

# Stealth mode with realistic browser headers and per-request UA rotation
wais run --url https://example.com --stealth --depth 2

# Custom user agent (disables stealth UA rotation, uses your UA on every request)
wais run --url https://example.com --user-agent "MyBot/1.0"

### `wais list`

List completed runs with summary statistics.

```bash
wais list [--data-dir <dir>] [--run-id <id>]
```

| Option       | Default  | Description                    |
|--------------|----------|--------------------------------|
| `--data-dir` | auto     | Data directory (auto-detects project root) |
| `--run-id`   | —        | Filter to a specific run ID    |

**Example output:**

```
  12c683379f77  pages=   42  errors=  1  start=2026-05-25T23:09:06
  a3f8b21c9044  pages=  103  errors=  0  start=2026-05-25T22:15:30
```

### `wais diff`

Compare two runs and report added, removed, or modified files.

```bash
wais diff <run_id_a> <run_id_b> [options]
```

| Option              | Default  | Description                          |
|---------------------|----------|--------------------------------------|
| `run_id_a`          | —        | First run ID (positional, required)  |
| `run_id_b`          | —        | Second run ID (positional, required) |
| `--data-dir`        | auto     | Data directory (auto-detects project root) |
| `-o`, `--output`    | —        | Write diff report to file            |
| `-v`, `--verbose`   | `False`  | Verbose logging                      |

**Example — detect changes between two runs:**

```bash
# Snapshot the current state
wais run --url https://example.com              # → run a3f8b21c9044

# ... time passes, content changes ...

# Snapshot again
wais run --url https://example.com              # → run def456789012

# See what changed
wais diff a3f8b21c9044 def456789012 -o diff.json
```

### `wais resume`

Inspect the state of a previous run (read-only).

```bash
wais resume <run_id> [options]
```

| Option       | Default     | Description                                      |
|--------------|-------------|--------------------------------------------------|
| `run_id`     | —           | Run ID to inspect (positional, required)         |
| `--mode`     | `continue`  | Resume mode: `continue`, `skip_completed`        |
| `--data-dir` | auto        | Data directory (auto-detects project root)       |
| `-v`, `--verbose` | `False` | Verbose logging                                  |

**Example output:**

```
Run a3f8b21c9044: 150 total, 103 completed, 2 failed, 45 pending
Resume mode: skip_completed
URLs remaining: 45
```

---

## Input Formats

### Single URL

```bash
wais run --url https://example.com
```

### CSV Format

Required column: `url`. Optional: `depth`, `tags`.

```csv
url,depth,tags
https://example.com,0,test
https://httpbin.org,1,api,news
```

```bash
wais run --input urls.csv
```

### JSON Format

Array of objects with `url` and optional `params.depth` / `params.tags`.

```json
[
  {
    "url": "https://example.com",
    "params": {
      "depth": 2,
      "tags": ["news"]
    }
  }
]
```

```bash
wais run --input urls.json
```

### TXT Format

One URL per line. Lines starting with `#` are ignored.

```
https://example.com
# this is a comment
https://httpbin.org
```

```bash
wais run --input urls.txt
```

### XML Format

```xml
<?xml version="1.0"?>
<urls>
  <url depth="0" tags="test">https://example.com</url>
  <url depth="1">https://httpbin.org</url>
</urls>
```

```bash
wais run --input urls.xml
```

### Markdown Format

Links are extracted from markdown `[text](url)` syntax.

```markdown
Check [Example](https://example.com) and [HTTPBin](https://httpbin.org)
```

```bash
wais run --input links.md
```

When no `--format` is given, the format is auto-detected from the file extension. Override with `--format csv|json|txt|xml|md`.

---

## Output Layout

Every run produces an independent snapshot under `<data-dir>/runs/<run_id>/`. Running the same URL twice preserves both versions under separate run IDs, enabling change detection via `wais diff`.

```
data/
├── state.db                      # SQLite resume database (shared)
└── runs/
    ├── a3f8b21c9044/
    │   ├── run.json               # run-level metadata
    │   └── data/                  # archived pages + assets
    │       └── httpbin.org/
    │           └── html/
    │               ├── index.html
    │               └── index.html.meta.json
    └── def456789012/
        ├── run.json
        └── data/
            └── httpbin.org/
                └── html/
                    ├── index.html
                    └── index.html.meta.json
```

### Domain Hierarchy (default)

URL path maps directly to filesystem path under the run's `data/` directory. Each page gets a `.meta.json` sidecar in the same directory.

```
data/runs/a3f8b21c9044/data/
  example.com/
    index.html
    index.html.meta.json
    blog/
      post.html
      post.html.meta.json
  assets/                           # only in full_site mode
    <sha256>.png
    <sha256>.css
    <sha256>.js
```

Layout logic (relative to `<run-data-dir>` = `data/runs/<run_id>/data/`):

| URL                                    | File Path                                         |
|----------------------------------------|---------------------------------------------------|
| `https://example.com`                  | `<run-data-dir>/example.com/index.html`           |
| `https://example.com/page`             | `<run-data-dir>/example.com/page/index.html`      |
| `https://example.com/blog/post.html`   | `<run-data-dir>/example.com/blog/post.html`       |
| `https://example.com/path/to/page/`    | `<run-data-dir>/example.com/path/to/page/index.html` |

### Flat Mode

```
data/runs/<run_id>/data/
  <url-hash-first-16-chars>.html
```

```bash
wais run --url https://example.com --data-dir archive
# uses flat layout via config, or explicitly set --layout (future option)
```

---

## Metadata Sidecars

### File-level Metadata

Every archived file gets a `.meta.json` sidecar with full provenance.

```json
{
  "file_id": "3f324f9914742e62...",
  "run_id": "a3f8b21c9044",
  "url": "https://httpbin.org/html",
  "final_url": "https://httpbin.org/html",
  "file_path": "runs/a3f8b21c9044/data/httpbin.org/html/index.html",
  "content_type": "text/html",
  "hashes": {
    "sha256": "3f324f9914742e62..."
  },
  "timestamps": {
    "acquired_at": "2026-05-25T23:09:06.123456+00:00",
    "response_time": "Mon, 25 May 2026 23:09:06 GMT",
    "last_modified": null
  },
  "http": {
    "status_code": 200,
    "headers": { "content-type": "text/html; charset=utf-8", ... }
  },
  "crawl": {
    "depth": 0,
    "parent_url": null,
    "referrer": null
  },
  "rendering": {
    "engine": "requests",
    "js_rendered": false
  }
}
```

### Run-level Metadata

Each run produces a `run.json` at `<data-dir>/runs/<run_id>/run.json`.

```json
{
  "run_id": "a3f8b21c9044",
  "timestamps": {
    "start": "2026-05-25T22:15:30.123456+00:00",
    "end": "2026-05-25T22:18:42.654321+00:00"
  },
  "input": { "url": "https://example.com" },
  "config": { ... },
  "statistics": {
    "pages_fetched": 103,
    "assets_downloaded": 0,
    "errors": 2
  },
  "environment": {
    "os": "posix",
    "python": "3.10.12"
  }
}
```

---

## Fetch Modes & Rendering

### Fetch Modes (`--mode`)

| Mode         | Description                                          |
|--------------|------------------------------------------------------|
| `html_only`  | Fetch raw HTML only (default)                        |
| `full_site`  | Fetch HTML + download assets (images, CSS, JS)       |
| `text_only`  | Reserved for future text extraction                  |

### Render Engines (`--render`)

| Engine       | Description                                          |
|--------------|------------------------------------------------------|
| `requests`   | Static HTTP fetch via `httpx`. Fast, lightweight.    |
| `playwright` | Headless Chromium via Playwright. Renders JS DOM.    |

Use `--render playwright` when the page requires JavaScript execution to display its content.

### Retry Policy

- Configurable via `timeout` (30s default) and `max_retries` (3 default)
- Exponential backoff with jitter: 2s, 4s, 8s between retries
- Retry applies only to network errors; invalid URLs and value errors raise immediately
- Custom User-Agent via `--user-agent` option, or realistic browser UA with `--stealth`
- `--stealth` rotates UA per-request among Chrome/Firefox variants; `--user-agent` overrides with a fixed string

### Robots.txt

By default WAIS **respects `robots.txt`** — it checks each URL against the site's `robots.txt` before fetching, using the configured `User-Agent`. Pages disallowed by robots.txt are skipped (counted as "skipped" in the progress display).

To bypass `robots.txt` for research archiving or record-keeping purposes (allowed under [fair use](https://fairuse.stanford.edu/overview/fair-use/) in many jurisdictions), pass `--ignore-robots`:

```bash
wais run --url https://example.com --depth 3 --stealth --ignore-robots
```

If `robots.txt` is unreachable (connection error, timeout), WAIS **allows** the fetch (fail-open). Parsed robots.txt files are cached per domain for the duration of the run.

---

## Crawl Engine

The crawl engine performs a BFS (breadth-first) crawl starting from seed URLs. Each fetched page's links are extracted, normalized, filtered, and added to the queue.

### Configuration

| Setting               | Default                             | Description                          |
|-----------------------|-------------------------------------|--------------------------------------|
| `--depth`             | `0` (single page, no link following) | Maximum link-following depth         |
| `--max-pages`         | `1000`                              | Hard limit on total pages fetched    |
| `follow_external_links` | `False`                           | Allow crawling external domains      |

Set `--depth 1` or higher to enable link following.

### URL Normalization

Every discovered URL is normalized before being added to the queue:

| Rule                 | Default   | Description                         |
|----------------------|-----------|-------------------------------------|
| HTTPS upgrade        | `True`    | `http://` → `https://`              |
| Strip fragments      | `True`    | Remove `#section`                   |
| Sort query params    | `False`   | Canonicalize `?b=1&a=2` → `?a=2&b=1` |
| Trailing slash       | `preserve`| `preserve`, `add`, or `remove`      |
| Lowercase domain     | always    | `EXAMPLE.com` → `example.com`       |

### URL Filtering

| Rule                 | Default                          | Description                          |
|----------------------|----------------------------------|--------------------------------------|
| `exclude_regex`      | `logout`, `session=`, `cart`     | Skip URLs matching these patterns    |
| `include_regex`      | `[]` (allow all)                 | Only crawl URLs matching these       |
| `domain_allowlist`   | `[]` (allow all)                 | Restrict to specific domains         |

Links starting with `#`, `//`, `javascript:`, or `mailto:` are always excluded.

---

## Asset Handling

In `full_site` mode, assets are downloaded and rewritten to local paths.

### Asset Types

| Asset Type | Controlled By       | Default |
|------------|---------------------|---------|
| Images     | `download_assets.images` | `True`  |
| CSS        | `download_assets.css`    | `True`  |
| JavaScript | `download_assets.js`     | `True`  |
| Fonts      | `download_assets.fonts`  | `False` |
| Media      | `download_assets.media`  | `False` |

### Asset Deduplication

Assets are **deduplicated by SHA-256 hash**. If two pages reference the same image, it is stored once under `assets/<sha256>.ext`.

### Local Rewriting

When `rewrite_links=True` (default), asset URLs in HTML are rewritten from remote URLs to local `assets/<sha256>.ext` paths. External assets (different domain) are kept as-is.

---

## Diff Engine

Compare two runs to detect changes between them.

```bash
wais diff <run_id_a> <run_id_b>
```

### How It Works

1. Walks all files in each run's `data/` directory
2. Skips `.meta.json` and `run.json` files
3. Compares files at the same relative path by SHA-256 hash
4. Reports: **added** (only in B), **removed** (only in A), **modified** (different hash)

### Diff Types

| Type       | Description                        |
|------------|------------------------------------|
| `html`     | HTML page content changed          |
| `asset`    | Asset file (under `assets/`) changed |
| `metadata` | Metadata sidecar changed           |

### Output Format

```json
{
  "run_id_a": "abc123",
  "run_id_b": "def456",
  "entries": [
    {
      "url": "https://example.com/page",
      "diff_type": "html",
      "changes": {
        "added": [],
        "removed": [],
        "modified": ["example.com/page/index.html"]
      },
      "hash_before": "aaa...",
      "hash_after": "bbb..."
    }
  ]
}
```

---

## State & Resume

Every run is tracked in a SQLite database at `<data-dir>/state.db`.

### URL States

| State       | Description                          |
|-------------|--------------------------------------|
| `pending`   | Queued but not yet fetched           |
| `completed` | Successfully fetched and stored      |
| `failed`    | Fetch failed after all retries       |
| `skipped`   | Skipped (resume mode)                |

### Resume Modes

| Mode                 | Description                                      |
|----------------------|--------------------------------------------------|
| `continue`           | Resume from last checkpoint, retry failed URLs   |
| `skip_completed`     | Only fetch URLs still marked as pending          |

### SQLite Schema

```sql
CREATE TABLE urls (
    url TEXT NOT NULL,
    run_id TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending','completed','failed','skipped')),
    depth INTEGER NOT NULL DEFAULT 0,
    content_hash TEXT NOT NULL DEFAULT '',
    parent_url TEXT NOT NULL DEFAULT '',
    error TEXT NOT NULL DEFAULT '',
    fetched_at TEXT NOT NULL DEFAULT '',
    PRIMARY KEY (url, run_id)
);

CREATE TABLE runs (
    run_id TEXT PRIMARY KEY,
    config_json TEXT NOT NULL DEFAULT '{}',
    started_at TEXT NOT NULL DEFAULT '',
    ended_at TEXT NOT NULL DEFAULT '',
    pages_fetched INTEGER NOT NULL DEFAULT 0,
    assets_downloaded INTEGER NOT NULL DEFAULT 0,
    errors INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE assets (
    asset_hash TEXT PRIMARY KEY,
    original_url TEXT NOT NULL,
    file_path TEXT NOT NULL,
    content_type TEXT NOT NULL DEFAULT '',
    size_bytes INTEGER NOT NULL DEFAULT 0
);
```

---

## Rate Limiting

| Parameter           | Default | Description                                   |
|---------------------|---------|-----------------------------------------------|
| `--domain-delay`    | `1.0s`  | Minimum delay between requests to one domain  |
| `--concurrency`     | `4`     | Maximum concurrent fetches                    |

Jitter of up to 100ms is added to domain delays to avoid thundering herd patterns. Global throttle (requests/second) can be configured but defaults to unlimited.

Example — polite, slow crawl:

```bash
wais run --url https://example.com --depth 2 --domain-delay 5 --concurrency 2
```

---

## Environment Variables

| Variable          | Description                                      |
|-------------------|--------------------------------------------------|
| `WAIS_DATA_DIR`   | Default data directory (overrides `--data-dir`)  |

### Data Directory Resolution

The default `--data-dir` is determined at runtime:

1. If installed from a development checkout (has `pyproject.toml` at the project root), data goes to `<project-root>/data/`
2. Otherwise it falls back to `data/` relative to CWD
3. `--data-dir` or `WAIS_DATA_DIR` always takes precedence

This means running `wais` from anywhere inside the project repository always writes to the same fixed `data/` directory.

---

## Architecture

```
                    ┌──────────────┐
                    │   CLI (Typer) │
                    └──────┬───────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
        ┌──────────┐ ┌──────────┐ ┌──────────┐
        │  run     │ │  diff    │ │  list    │
        └────┬─────┘ └──────────┘ └──────────┘
             │
    ┌────────┼──────────────┐
    ▼        ▼              ▼
┌──────┐ ┌──────┐ ┌──────────────┐
│Loader│ │Fetch │ │State (SQLite)│
└──┬───┘ └──┬───┘ └──────────────┘
   │        │
   ▼        ▼
┌──────┐ ┌──────┐
│Crawl │ │Store │
│Engine│ │Writer│
└──────┘ └──┬───┘
            ▼
      ┌──────────┐
      │Artifacts │
      │on Disk   │
      └──────────┘
```

### Core Subsystems

| Subsystem       | Module              | Responsibility                              |
|-----------------|---------------------|---------------------------------------------|
| Input Loader    | `core/loaders/`     | Parse URLs from various input formats       |
| Crawl Engine    | `core/crawl/`       | BFS crawling, URL normalization, filtering  |
| Fetch Engine    | `core/fetch/`       | HTTP/Playwright fetching, retry, assets     |
| Storage Engine  | `core/storage/`     | File layout, artifact writing, sidecars     |
| State Manager   | `core/state/`       | SQLite-backed resume and tracking           |
| Diff Engine     | `core/diff/`        | Hash-based change detection between runs    |
| Hashing         | `core/hashing/`     | SHA-256 utilities                           |
| Utils           | `core/utils/`       | Rate limiter, URL queue, robots.txt checker |

---

## Development

```bash
git clone <repo>
cd wais
pip install -e ".[dev]"
playwright install chromium
python -m pytest tests/ -v
```

### Project Structure

```
wais/
├── pyproject.toml
├── core/                    # Python package (imported as core.*)
│   ├── main.py              # CLI entrypoint (Typer)
│   ├── cli/                 # Subcommand implementations
│   ├── models/              # Pydantic schemas
│   ├── loaders/             # Input format parsers
│   ├── fetch/               # HTTP + Playwright fetchers
│   ├── storage/             # Output layout + writer
│   ├── state/               # SQLite state stores
│   ├── diff/                # Change detection engine
│   ├── crawl/               # BFS crawl + filters
│   ├── hashing/             # Hash utilities
│   ├── logutil/             # Logging configuration
│   └── utils/               # Rate limiter, queue, robots
├── migrations/              # SQLite schema migrations
└── tests/                   # pytest test suite
```

### Test Suite

49 tests covering all subsystems. Uses `vcrpy` for HTTP recording to ensure deterministic test runs.

```bash
python -m pytest tests/ -v
python -m pytest tests/ -v --cov=core   # with coverage
```

---

## License

MIT
