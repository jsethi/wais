# WAIS Codebase Status

## Remaining Risks

| # | Risk | Location | Impact |
|---|------|----------|--------|
| C2 | Playwright is a hard dependency | `pyproject.toml:15` | `pip install wais` drags in ~50MB Playwright package even for static-HTTP-only users. *(Kept mandatory by maintainer decision)* |

---

## Remaining Opportunities

### Low-hanging fruit (hours)

| # | Opportunity | Gain |
|---|-------------|------|
| 1 | Remove dead code (`JSONStore`, `ManifestWriter`, `URLQueue`, `ResumeMode.restart_modified_only`, `CrawlConfig.strip_query_params`) | ~150 lines less to maintain |
| 2 | Convert `FetchResult` to Pydantic model or `dataclass` | Consistency with rest of codebase |

### High-value (days)

| # | Opportunity | Gain |
|---|-------------|------|
| 3 | `wais serve` — static file server for archives | Archives become browsable in a browser (~100 lines) |
| 4 | WARC export | Industry standard — interop with Wayback Machine, Browsertrix, pywb |
| 5 | Content extraction (text_only) + SQLite FTS5 | Full-text search across all archived pages |
| 6 | Scheduled re-crawl with cron | Makes the diff engine valuable over time |
| 7 | Test coverage: fetchers, asset handler, crawl engine | 3 major components with zero tests |
| 8 | `wais resume` should resume or rename to `wais status` | Fix misleading command name |

### Strategic (weeks)

| # | Opportunity | Gain |
|---|-------------|------|
| 9 | Web UI with side-by-side HTML diff viewer | Visual change tracking — the killer feature for archival |
| 10 | Incremental crawl (check ETag/Last-Modified) | Massively reduces bandwidth for recurring crawls |
| 11 | `wais gc` — garbage collect old runs, deduplicate content | Disk management for long-term use |
| 12 | Proxy + auth support | Archive behind-firewall and authenticated content |

---

## Ledger (Completed Items)

| # | Item | Category | Notes |
|---|------|----------|-------|
| C1 | Path traversal guard in `layout.py` | Risk (Critical) | `netloc.split("/")[0]` + filter `..` from path parts |
| C3 | Dependency upper bounds in `pyproject.toml` | Risk (Critical) | All deps capped at `<NEXT_MAJOR` |
| R1 | `PlaywrightFetcher.client` property added | Risk (Critical) | Enables `--render playwright --mode full_site` |
| H1 | Retryable exception types in `policy.py` | Risk (High) | Network errors retry; invalid URL, value errors raise immediately |
| H2 | Progress crash handling in `run.py` | Risk (High) | `try`/`except` around all `live.update()` calls |
| H3 | Graceful Playwright failure message | Risk (High) | `RuntimeError` with actionable `playwright install chromium` |
| H4 | Removed dead non-crawl path | Risk (High) | Unreachable `else` branch removed (11 lines) |
| H5 | `RobotsChecker` wired into crawl engine | Risk (High) | Config-gated via `--respect-robots/--ignore-robots` |
| H6 | `WAIS_DATA_DIR` env var + shared `resolve_data_dir()` | Risk (High) | Env var + 3 CLI files deduplicated into `core/cli/utils.py` |
| R2 | Captured `run_start` for wall-clock timestamps | Risk (High) | `run.json` now shows non-zero duration |
| R3 | `clear_run()` + `--fresh` wiring | Risk (High) | `--fresh` now actually clears state via `SQLiteStore.clear_run()` |
| R4 | `_detect_charset()` cascading encoding detection | Risk (High) | Content-Type header → `<meta charset>` → `<meta http-equiv>` → UTF-8 fallback |
| M1 | Wired `--resume` flag through to `get_pending()` | Risk (Medium) | CLI → `_run()` → `engine.crawl()` → `store.get_pending(resume_mode=...)` |
| M2 | Per-request UA rotation in stealth mode | Risk (Medium) | UA list moved to `UAS` tuple in `policy.py`, per-request `random.choice()` |
| M3 | `_sanitize_segment()` for filename sanitization | Risk (Medium) | Filters control chars, `..`, long paths in `layout.py` |
| M4 | `"WARN"` → `"WARNING"` canonical log level | Risk (Medium) | Removes deprecated alias usage |
| M5 | Stale migration SQL dir removed | Risk (Medium) | Deleted during workspace cleanup |
| R5 | Depth guard before enqueuing discovered URLs | Risk (Medium) | Prevents wasted DB I/O and queue memory on resume with lowered depth |
| R6 | `Field(ge=0)` + `max(0, ...)` for delay validation | Risk (Medium) | `ValueError: sleep length must be non-negative` prevented |
| R7 | Fixed subdomain false positives in `_is_same_domain` | Risk (Medium) | Removed dead `lstrip(".")` from `asset_handler.py` |
| R8 | XXE mitigation in XML loader | Risk (Medium) | `XMLParser(resolve_entities=False)` with TypeError fallback |
| R9 | `check_available()` eager Playwright init | Risk (Medium) | Surfaces install error at CLI start, not first fetch |
| R10 | `networkidle` → `domcontentloaded` | Risk (Medium) | Prevents hangs on WebSocket/SSE/long-poll pages |
| L4 | Removed redundant CSS decode (dead code) | Risk (Low) | Lines 88-89 in `asset_handler.py` |
| L5 | Removed `crawl.enabled` dead field | Risk (Low) | Zero references in codebase |
| L6 | Filtered protocol-relative `//` href values | Risk (Low) | Prevents `href="//evil.com"` domain confusion |
| L7 | `run_id` added to `URLState()` in queue | Risk (Low) | Prevents PK constraint failure if serialized |
| L8 | `rglob("*")` → `glob("**/*")` in diff engine | Risk (Low) | Prevents symlink traversal |
| Opt 1 | Rate limiter wait moved before semaphore | Optimization | Concurrency slots no longer burned on sleep |
| Opt 2 | Sync I/O → `asyncio.to_thread()` in `StorageWriter` | Optimization | 4 methods converted, 7 blocking calls offloaded |
| Opt 3 | Double HTML parse → single parse with soup reuse | Optimization | `full_site` mode: 1 BS4 parse instead of 2 per page |
| Opt 4 | Rate limiter memory leak | Optimization (N/A) | Code was already correct — append inside guard |
| Opt 5 | Second httpx client removed, shares fetcher's | Optimization | One connection pool instead of two |
| Opt 6 | SQLite batch commits (every 50 ops) | Optimization | ~20K fsyncs → ~400 on a 10K page crawl |
| Opt 7 | `get_pending()` bounded by `max_pages` via LIMIT | Optimization | Deque holds 200KB instead of 200MB on resume |
| Opt 8 | Anonymous `type()` → `URLState` model | Optimization | No throwaway class per discovered link |
| Opt 9 | `SELECT *` → explicit columns in `get_pending()` | Optimization | Returns 7/8 columns (dropped unreferenced `fetched_at`) |
| Opt 10 | Removed unused MD5 hash computation | Optimization | 2 `hash_bytes(content, "md5")` calls removed from both fetchers |
| Opt 11 | `write_bytes()` → `asyncio.to_thread()` in asset handler | Optimization | Blocking I/O offloaded from async path |
| Opt 12 | Cached `headers` dict in `RequestPolicy` | Optimization | Built once in `__init__`, returned as copy from property. UA and Accept-Language selected once per-run (still different per `wais run`). |
| Opt 13 | Rate limiter `list` → `deque` for O(1) pruning | Optimization | `while popleft()` instead of O(n) list comprehension |
| Opt 14 | Removed duplicate import in `models/__init__.py` | Optimization | One line deleted |
| Opt 15 | `dict` → `Counter` for domain stats | Optimization | `most_common(5)` replaces `sorted(..., key=lambda x: -x[1])` |
