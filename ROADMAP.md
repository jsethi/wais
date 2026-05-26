# WAIS Roadmap

## Phase 1 — Foundation Fixes

| # | Item | Status | Impact |
|---|------|--------|--------|
| 1 | Wire `--resume` flag to `_run()` | ❌ Broken | `wais run --resume` does nothing |
| 2 | Fix `crawl.enabled=False` path | ❌ Broken | Default `--depth 0` skips asset handling, stats |
| 3 | Add `WAIS_DATA_DIR` env var | ❌ Missing | Documented but unimplemented |
| 4 | Remove dead code (`JSONStore`, `ManifestWriter`, stale migration SQL) | 🗑️ Cleanup | Reduces maintenance surface |
| 5 | CrawlEngine + Fetcher tests | ❌ Untested | Biggest risk for refactoring |

## Phase 2 — Integration

| # | Item | Status | Impact |
|---|------|--------|--------|
| 6 | Wire `RobotsChecker` into fetchers | 🏗️ Built, unused | `respect_robots_txt` ignored |
| 7 | Run SQL migrations programmatically | 🏗️ Schema drift | `runs`/`assets` tables never created |
| 8 | Expose orphan config via CLI (`--global-throttle`, `--respect-robots`, `--domain-allowlist`, `--sort-params`) | 🏗️ Defined, no CLI | Unexploitable config surface |

## Phase 3 — Versatility

| # | Item | Why |
|---|------|-----|
| 9 | `wais serve` — browse archives in browser | Instant accessibility |
| 10 | WARC export — industry archival format | Interop with Wayback Machine, Browsertrix |
| 11 | Content extraction (`text_only`) — clean markdown from HTML | Enables search, LLM ingestion, semantic diff |
| 12 | Full-text search via SQLite FTS5 | `wais search <query>` across runs |
| 13 | Scheduled re-crawl (`--cron`) | Makes diff useful over time |
| 14 | Export run as PDF, MHTML, markdown | Shareable snapshots |

## Phase 4 — Scale

| # | Item | Why |
|---|------|-----|
| 15 | `wais gc` — garbage collect old runs, prune assets | Disk management |
| 16 | Incremental crawl — skip unchanged URLs | Bandwidth/time savings |
| 17 | Proxy + auth support | Archive behind-firewall content |
| 18 | Web UI with diff viewer | Visual change tracking |
| 19 | Distributed fetching | Multi-machine scaling |
