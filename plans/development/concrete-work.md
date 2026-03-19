# Concrete development work — phase extensions

This document **extends** each [modular phase](../README.md) with implementation-focused work: repository layout, modules, checklists, config keys, and how to verify completion. Use it as the day-to-day build spec.

**Convention:** Paths are relative to the repo root `x-scrape-cdp/`. Adjust naming if you prefer a flat layout.

---

## Target repository layout (reference)

```text
x-scrape-cdp/
├── pyproject.toml              # or requirements.txt
├── .env.example
├── README.md                   # how to launch Chrome + run listener
├── config/
│   └── default.yaml            # targets, intervals, CDP URL, paths
├── scripts/
│   ├── launch_chrome.ps1       # Windows
│   └── launch_chrome.sh        # macOS/Linux
├── src/
│   └── x_scrape_cdp/
│       ├── __init__.py
│       ├── config.py           # load settings (yaml + env)
│       ├── logging_setup.py    # structured logging
│       ├── cdp.py              # phases 3–4
│       ├── session.py          # phase 3 validation
│       ├── stealth.py          # phase 5
│       ├── navigation.py       # phase 6
│       ├── extract.py          # phase 7
│       ├── storage.py          # phase 7 seen + jsonl
│       ├── loop.py             # phase 9
│       ├── cli.py              # typer or argparse entrypoint
│       ├── notify.py           # optional webhooks (phase 7/9)
│       └── agent/              # phase 8 (optional package)
│           └── __init__.py
├── data/                       # gitignored except .gitkeep
│   ├── .gitkeep
│   ├── seen_ids.json
│   └── posts.jsonl
├── tests/
│   ├── conftest.py
│   ├── test_storage.py
│   ├── test_extract_parsing.py # pure functions with saved HTML fixtures
│   └── test_config.py
└── docker/                     # phase 10
    └── compose.multi.yaml
```

You can collapse `src/x_scrape_cdp/` to a single `listener.py` for a minimal MVP; the layout above is what “production-shaped” looks like.

---

## Phase 0 — Context & risks → governance artifacts

**Goal:** Make risk and scope explicit so implementation choices stay defensible.

| Item | Concrete action |
|------|-----------------|
| **Doc** | Add `docs/RISKS.md`: ToS, CFAA-style notes, account/IP ban risk, data retention. |
| **Doc** | Add `docs/SCOPE.md`: “public profiles only”, max accounts, max poll frequency, no resale. |
| **Config** | Reserve `config/default.yaml` keys: `targets[]`, `interval_seconds_min/max`, `max_scroll_rounds`, `dry_run: bool`. |
| **Decision** | Record cookie-file vs `user-data-dir` in `docs/ADR-001-session-strategy.md` (one paragraph). |

**Verification**

- [ ] `docs/RISKS.md` and `docs/SCOPE.md` exist and are linked from root `README.md`.
- [ ] Team/user has explicitly chosen session strategy in ADR or README.

**Definition of done:** A new contributor can read two pages and know legal/ethical boundaries and operational limits.

---

## Phase 1 — Preparation → runnable Chrome + deps

**Goal:** One command (or documented command) starts Chrome with CDP; Python env is reproducible.

| Deliverable | Detail |
|-------------|--------|
| `scripts/launch_chrome.ps1` | Parameters: `-Port 9222`, `-UserDataDir .\data\chrome_profile`. Pass `--remote-debugging-port`, `--user-data-dir`, `--no-first-run`, `--no-default-browser-check`. Echo the CDP URL. |
| `scripts/launch_chrome.sh` | Same for macOS/Linux; use `#!/usr/bin/env bash`, `set -euo pipefail`. |
| `pyproject.toml` | Dependencies: `playwright`, `playwright-stealth`, `pyyaml`, `httpx` (webhooks), `typer` or no CLI lib. Dev: `pytest`, `ruff`. |
| `README.md` section | “Prerequisites”: Chrome path, Python version, `playwright install chromium` once. |
| `.env.example` | `CDP_URL=http://127.0.0.1:9222`, `CONFIG_PATH=config/default.yaml`. |

**Checklist**

1. Run script → Chrome opens → visit `http://127.0.0.1:9222/json/version` → JSON returns with `webSocketDebuggerUrl`.
2. `python -c "import playwright; print(playwright.__version__)"` succeeds.
3. `playwright install chromium` completed (for standalone use later).

**Definition of done:** Another machine can follow README and reach a listening CDP port without guessing flags.

---

## Phase 2 — Authentication → documented session capture

**Goal:** Exactly one supported path for “logged in” (prefer `user-data-dir` for MVP).

| Deliverable | Detail |
|-------------|--------|
| `README.md` | Step-by-step: launch script → open x.com → login + 2FA → wait 60s → close optional. |
| `data/chrome_profile/` | Gitignored; documented in `.gitignore`. |
| Optional `cookies.json` | If using file cookies: document export steps; add `data/cookies.example.json` (empty array `[]`) as shape reference—**never commit real cookies**. |

**Checklist**

1. After login, restart Chrome with same `user-data-dir` → still logged in.
2. If using cookies: `cookies.json` is valid Playwright list format (domain, path, name, value, …).

**Definition of done:** Session survives Chrome restart; method is documented as single source of truth.

---

## Phase 3 — Session injection → validate auth in code

**Goal:** Programmatically confirm logged-in state after attach.

| Module | Responsibilities |
|--------|------------------|
| `session.py` | `async def is_logged_in(page) -> bool`: e.g. URL allows x.com home, and locator for avatar OR “Home” nav OR absence of “Log in” button (pick 2 signals to avoid false positives). |
| `cdp.py` | `async def load_cookies_if_configured(context, path) -> None` reads JSON and calls `add_cookies` when file exists. |

| Config | |
|--------|--|
| `session.cookie_file` | Path or null |
| `session.validate_on_startup` | `true` |

**Checklist**

1. With valid session: `is_logged_in` is True within 15s of `goto("https://x.com/home")`.
2. Logged out profile: False with clear log message telling user to re-login.

**Definition of done:** Listener aborts early with actionable error if session is invalid.

---

## Phase 4 — CDP connection → stable attach

**Goal:** Single function returns `(browser, context, page)` with predictable lifecycle.

| Module | API sketch |
|--------|------------|
| `cdp.py` | `async def connect_playwright(cdp_http_url: str) -> PlaywrightConnection` holding browser/context/default page factory. |
| | Handle: no pages → `new_page()`; log context count if >1. |

| Config | |
|--------|--|
| `cdp.http_url` | `http://127.0.0.1:9222` |

**Checklist**

1. Unit/integration: mock or real CDP—connect twice in one process without leaking (close on shutdown if API allows).
2. Connection failure (wrong port): exception message includes `CDP_URL` and “is Chrome running with remote debugging?”.

**Definition of done:** `cli.py run` reaches “connected to browser” log line.

---

## Phase 5 — Anti-detection → applied policy

**Goal:** Centralize stealth so every page gets the same treatment.

| Module | Responsibilities |
|--------|------------------|
| `stealth.py` | `async def apply_stealth(page, profile: StealthProfile)` calls `stealth_async`, `add_init_script` for `webdriver`, sets viewport from profile. |
| `StealthProfile` | `viewport_width/height`, optional `user_agent` string from config. |

| Config | |
|--------|--|
| `stealth.viewport` | `{ width: 1920, height: 1080 }` |
| `stealth.user_agent` | null = don’t override |
| `stealth.jitter_percent` | e.g. `10` for ±10% viewport randomization |

**Checklist**

1. In DevTools on loaded page: `navigator.webdriver` is falsy or undefined as intended.
2. Viewport matches configured dimensions within jitter bounds.

**Definition of done:** All navigation entry points call `apply_stealth` exactly once per new page (document if reused).

---

## Phase 6 — Navigation → profile load + human pacing

**Goal:** One function per concern: goto profile, wait timeline, soft scroll.

| Module | API sketch |
|--------|------------|
| `navigation.py` | `async def open_profile(page, username: str, *, replies: bool) -> None` |
| | `async def human_warmup(page) -> None` mouse move + sleep |
| | `async def gentle_scroll_for_fresh_posts(page, rounds: int, pause_range_sec: tuple) -> None` |

| Config | |
|--------|--|
| `navigation.wait_until` | `domcontentloaded` or `networkidle` (document tradeoff) |
| `navigation.tweet_timeout_ms` | `15000` |
| `navigation.scroll_rounds` | `3` |
| `navigation.pause_seconds_min/max` | `2.0` / `4.0` |

**Checklist**

1. Run against a known public account: at least one `[data-testid="tweet"]` appears within timeout.
2. Total scroll count never exceeds `max_scroll_rounds` from global safety cap (Phase 0 config).

**Definition of done:** Navigation is parameterized by username and config only—no hardcoded URLs in multiple files.

---

## Phase 7 — Extraction & storage → durable listener state

**Goal:** Typed post records, JSONL append, atomic-ish `seen_ids` updates.

| Module | Responsibilities |
|--------|------------------|
| `extract.py` | `async def extract_visible_posts(page) -> list[Post]`; `Post` dataclass or pydantic model: `id`, `text`, `timestamp`, `url`, `media_urls` (optional). |
| `storage.py` | `load_seen(path) -> set[str]`; `save_seen_atomic(path, ids)` (write temp + rename); `append_posts_jsonl(path, posts)`; `filter_new(posts, seen) -> tuple[list, set]` |

| Data contracts | |
|------------------|--|
| `posts.jsonl` | One JSON object per line; include `scraped_at` ISO timestamp. |
| `seen_ids.json` | `{"ids": ["...", "..."] }` or plain list—pick one and document. |

**Checklist**

1. **Unit test:** feed HTML fixture → parser returns expected IDs and text (no network).
2. **Crash test:** interrupt after new posts detected but before `save_seen`—document whether duplicate append is acceptable or implement two-phase commit (optional stretch).
3. `notify.py`: optional `POST` webhook with HMAC or simple secret header from env.

**Definition of done:** Running twice does not duplicate lines in JSONL for the same tweet ID.

---

## Phase 8 — AI agent (optional) → pluggable backend

**Goal:** Same output shape as `extract.py` without breaking the main path.

| Deliverable | Detail |
|-------------|--------|
| `config` | `extraction.mode`: `playwright` \| `agent` |
| `agent/` | `async def extract_posts_agent(page, prompt_template: str) -> list[Post]` stub that calls your chosen integration (HTTP to local agent, etc.). |
| `extract.py` | Factory `get_extractor(settings)` returns appropriate implementation. |

**Checklist**

1. With `mode=playwright`, agent code is never imported (optional dependency).
2. Agent path returns `Post` objects validating with same schema as deterministic extractor.

**Definition of done:** Switching modes is one config change; tests still pass for playwright mode.

---

## Phase 9 — Loop & scheduling → production-shaped runner

**Goal:** Long-running loop with jitter, per-target errors, structured logs.

| Module | Responsibilities |
|--------|------------------|
| `loop.py` | `async def run_listener(settings)`: connect once, reuse page, for each target call nav + extract + storage + notify; sleep `uniform(min,max)`. |
| `cli.py` | Commands: `run`, `once` (single pass for debugging), `validate-session`. |
| `logging_setup.py` | JSON or key=value logs: `event`, `target`, `new_count`, `error`. |

| Config | |
|--------|--|
| `schedule.interval_seconds_min` / `_max` | e.g. `240` / `600` |
| `targets` | list of usernames without `@` |

**Checklist**

1. `once` completes one full cycle and exits 0.
2. Simulated exception in one target does not kill entire loop (log + continue).
3. SIGINT triggers graceful shutdown (close playwright connection).

**Definition of done:** Process can run under systemd/PM2 with restart policy; logs are parseable.

---

## Phase 10 — Multi-instance → isolation matrix

**Goal:** Table-driven instances: port, profile dir, proxy, config file.

| Deliverable | Detail |
|-------------|--------|
| `config/instances.yaml` | List of `{ name, cdp_port, user_data_dir, proxy_url?, config_path }`. |
| `docker/compose.multi.yaml` | Optional: one service per instance with different ports/volumes (only if you containerize Chrome—often host Chrome is easier). |
| `scripts/run_instance.ps1` | Wrapper: set `CDP_URL` and `CONFIG_PATH` for one instance. |

**Checklist**

1. Two Chromes on 9222 and 9223 with different profiles do not share cookies.
2. Document max recommended instances per IP without proxy (likely 1).

**Definition of done:** Operator can add a new row to `instances.yaml` and start a second listener without code changes.

---

## Phase 99 — Reference / maintenance → operational hooks

**Goal:** Ongoing quality and recovery.

| Deliverable | Detail |
|-------------|--------|
| `tests/smoke/` | One pytest that hits a **staging** HTML fixture or skipped-by-default live test (`@pytest.mark.live`). |
| `Makefile` or `justfile` | Targets: `lint`, `test`, `run-once`. |
| `README` maintenance | Weekly selector check reminder; link to X UI changelog if you track one. |

**Verification**

- [ ] CI runs `ruff` + `pytest` (excluding `live`).
- [ ] Backup procedure for `data/posts.jsonl` documented (copy to S3, etc.).

---

## Suggested implementation order (sprints)

| Sprint | Phases | Outcome |
|--------|--------|---------|
| **A** | 1, 4, 3 (validate only), CLI `validate-session` | Attach + confirm login |
| **B** | 5, 6, 7, `once` | First real JSONL line |
| **C** | 9 | Continuous loop + logs |
| **D** | 10 | Second instance |
| **E** | 8 | Agent fallback (if needed) |

---

## Traceability matrix

| Phase doc | This section |
|-----------|----------------|
| [phase-00-context-and-risks.md](../phase-00-context-and-risks.md) | Phase 0 |
| [phase-01-preparation.md](../phase-01-preparation.md) | Phase 1 |
| [phase-02-authentication-capture.md](../phase-02-authentication-capture.md) | Phase 2 |
| [phase-03-session-injection.md](../phase-03-session-injection.md) | Phase 3 |
| [phase-04-cdp-connection.md](../phase-04-cdp-connection.md) | Phase 4 |
| [phase-05-anti-detection.md](../phase-05-anti-detection.md) | Phase 5 |
| [phase-06-navigation-listener.md](../phase-06-navigation-listener.md) | Phase 6 |
| [phase-07-data-extraction.md](../phase-07-data-extraction.md) | Phase 7 |
| [phase-08-ai-agent-integration.md](../phase-08-ai-agent-integration.md) | Phase 8 |
| [phase-09-loop-scheduling.md](../phase-09-loop-scheduling.md) | Phase 9 |
| [phase-10-multi-instance-scaling.md](../phase-10-multi-instance-scaling.md) | Phase 10 |
| [phase-99-reference-flow-maintenance.md](../phase-99-reference-flow-maintenance.md) | Phase 99 |

Parent index: [../../full-plan.md](../../full-plan.md) · Dev folder: [README.md](./README.md)
