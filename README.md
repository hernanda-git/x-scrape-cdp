# x-scrape-cdp 

<p align="center">
  <strong>Cyberpunk-grade X profile listener powered by Chrome CDP + Playwright</strong><br />
  Tap into real logged-in browser sessions, stream fresh posts, and archive signal like a data runner.
</p>

<p align="center"><code>[[ SIGNAL PIPELINE ACTIVE ]]</code></p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.9%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.9+" />
  <img src="https://img.shields.io/badge/playwright-async-2EAD33?style=for-the-badge&logo=playwright&logoColor=white" alt="Playwright" />
  <img src="https://img.shields.io/badge/chrome-cdp-00E5FF?style=for-the-badge&logo=googlechrome&logoColor=black" alt="Chrome CDP" />
  <img src="https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-FF00C8?style=for-the-badge" alt="Cross platform" />
  <img src="https://img.shields.io/badge/mode-cyberpunk-8A2BE2?style=for-the-badge" alt="Cyberpunk mode" />
</p>

---

## Navigation Grid

- [Mission Profile](#mission-profile)
- [Safety and Operational Scope](#safety-and-operational-scope)
- [Neon Architecture Map](#neon-architecture-map)
- [System Prerequisites](#system-prerequisites)
- [Step-by-Step Quick Start](#step-by-step-quick-start)
- [CLI Commands](#cli-commands)
- [Config Matrix](#config-matrix)
- [Data Vault and Samples](#data-vault-and-samples)
- [Multi-Instance Usage](#multi-instance-usage)
- [Docker Compose (Multi Listener)](#docker-compose-multi-listener)
- [Troubleshooting](#troubleshooting)
- [Ops Checklist](#ops-checklist)

---

## Mission Profile

`x-scrape-cdp` listens for posts from configured X profiles by connecting to a real Chrome session via the Chrome DevTools Protocol (CDP).  
It avoids brittle "fake login" automation by reusing your authenticated browser profile and writing deduplicated post data to JSON files.

### Core Capabilities

- Real-session authentication (manual login + 2FA supported)
- Async Playwright scraping flow with stealth profile tuning
- Deduplication via persistent `seen_ids.json`
- JSONL append-only post archive for downstream pipelines
- Optional webhook notification per fresh batch
- Multi-instance support via named configs and separate CDP ports

---

## Safety and Operational Scope

Project policy docs:

- Risk policy: [`docs/RISKS.md`](docs/RISKS.md)
- Operational boundaries: [`docs/SCOPE.md`](docs/SCOPE.md)
- Session architecture decision: [`docs/ADR-001-session-strategy.md`](docs/ADR-001-session-strategy.md)

Use responsibly and ensure your operation complies with platform terms, local regulation, and your own risk controls.

---

## Neon Architecture Map

```text
[ Chrome: logged-in profile ]
             |
             v   CDP // http://127.0.0.1:9222
[ Playwright live connection ]
             |
             v
[ Navigate targets -> extract posts -> deduplicate ]
             |
             +--> data/seen_ids.json   (identity ledger)
             +--> data/posts.jsonl     (event stream)
             +--> optional webhook     (live relay)
```

Core modules:

- `src/x_scrape_cdp/cli.py` -> CLI entrypoints (`validate-session`, `once`, `run`)
- `src/x_scrape_cdp/loop.py` -> orchestration loop and per-target cycle
- `src/x_scrape_cdp/extract.py` -> post extraction model + parser
- `src/x_scrape_cdp/config.py` -> YAML/env settings resolution
- `src/x_scrape_cdp/session.py` -> login state detection

---

## System Prerequisites

- Python `3.9+` (recommended `3.11+`)
- Google Chrome installed
- PowerShell on Windows (bash/zsh for Linux/macOS)
- A valid X account session in Chrome

---

## Step-by-Step Quick Start

### 1) Clone and enter project

```bash
git clone <your-repo-url>
cd x-scrape-cdp
```

### 2) Create and activate virtual environment

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.venv\Scripts\activate
```

Linux/macOS:

```bash
source .venv/bin/activate
```

### 3) Install project dependencies

```bash
pip install -e .[dev]
playwright install chromium
```

### 4) Launch Chrome with remote debugging (CDP uplink)

Windows:

```powershell
./scripts/launch_chrome.ps1 -Port 9222 -UserDataDir ./data/chrome_profile
```

Expected output:

```text
Chrome launched with CDP at http://127.0.0.1:9222
Check endpoint: http://127.0.0.1:9222/json/version
```

Linux/macOS:

```bash
./scripts/launch_chrome.sh 9222 ./data/chrome_profile
```

### 5) Login manually on X in that same browser window

1. Open `https://x.com/` in the launched Chrome window.
2. Complete login (including 2FA if required).
3. Wait ~60 seconds after successful login.
4. Keep using the same user-data directory for future runs.

### 6) Validate the captured session

```bash
python -m x_scrape_cdp.cli validate-session
```

Expected success output:

```text
Session is valid.
```

### 7) Run a single scrape cycle

```bash
python -m x_scrape_cdp.cli once
```

Example output:

```text
Completed once cycle. New posts: 3
```

### 8) Run continuous listener mode (always-on)

```bash
python -m x_scrape_cdp.cli run
```

Stop gracefully with `Ctrl+C`.

---

## CLI Commands

| Command | Purpose |
| --- | --- |
| `python -m x_scrape_cdp.cli validate-session` | Verifies current session is logged in |
| `python -m x_scrape_cdp.cli once` | Runs one fetch cycle across all targets |
| `python -m x_scrape_cdp.cli run` | Runs infinite scheduled loop |
| `python -m x_scrape_cdp.cli <cmd> --config config/default.yaml` | Uses an explicit config file |
| `x-scrape-cdp <cmd>` | Equivalent script entrypoint from `pyproject.toml` |

Developer helpers:

| Command | Purpose |
| --- | --- |
| `make lint` | Ruff linting on `src` and `tests` |
| `make test` | Pytest run excluding `live` marker |
| `make run-once` | Shortcut for one cycle |

---

## Config Matrix

Primary config: [`config/default.yaml`](config/default.yaml)

### Resolution order

1. CLI `--config` argument
2. `CONFIG_PATH` environment variable
3. default `config/default.yaml`

CDP URL can be overridden with:

```bash
CDP_URL=http://127.0.0.1:9222
```

### Main settings matrix

| Section | Key fields | Description |
| --- | --- | --- |
| `cdp` | `http_url` | CDP endpoint for Playwright connect |
| `session` | `cookie_file`, `validate_on_startup` | Session source + startup validation |
| `stealth` | viewport, `user_agent`, `jitter_percent` | Browser fingerprint hardening knobs |
| `navigation` | waits, timeouts, scrolls, replies | Timeline navigation behavior |
| `schedule` | `interval_seconds_min/max` | Loop sleep window between cycles |
| `extraction` | `mode`, `prompt_template` | Extraction strategy (`playwright` default) |
| `storage` | file paths for seen IDs and posts | Output locations |
| `notify` | webhook enabled/url | Optional push notifications |
| root | `targets`, `max_scroll_rounds`, `dry_run` | High-level runtime controls |

### Minimal target example

```yaml
targets:
  - "Learnernoearner"
```

---

## Data Vault and Samples

Generated files:

- `data/seen_ids.json` -> deduplication index
- `data/posts.jsonl` -> append-only extracted posts

### `posts.jsonl` sample

```json
{"id":"2034599322013041108","text":"$BTC \n\nThanks for playing\n\nGm $BTC this weeks move","timestamp":"2026-03-19T11:54:14.000Z","url":"https://x.com/Learnernoearner/status/2034599322013041108","media_urls":["https://pbs.twimg.com/profile_images/1722060690775539712/OP8MFN04_normal.jpg","https://pbs.twimg.com/media/HDxZTNoW4AAbitm?format=jpg&name=small"],"scraped_at":"2026-03-19T22:29:52.909031+00:00"}
{"id":"2034601941242720344","text":"$SOL full tp done #SOL $SOL LIMIT SHORT TRADE\n\nENTRY: 97.35 - 98.5\n\nTARGET: 91.2\n\nSTOPLOSS: 100.35","timestamp":"2026-03-19T12:04:38.000Z","url":"https://x.com/Learnernoearner/status/2034601941242720344","media_urls":["https://pbs.twimg.com/profile_images/1722060690775539712/OP8MFN04_normal.jpg","https://pbs.twimg.com/media/HDxbrmpWsAAWOIG?format=jpg&name=small"],"scraped_at":"2026-03-19T22:29:52.909031+00:00"}
```

### `seen_ids.json` sample

```json
{
  "ids": [
    "2034599322013041108",
    "2034601941242720344",
    "2034602223464853814"
  ]
}
```

---

## Multi-Instance Usage

Define instances in [`config/instances.yaml`](config/instances.yaml):

```yaml
instances:
  - name: "primary"
    cdp_port: 9222
    user_data_dir: "data/chrome_profile_primary"
    config_path: "config/default.yaml"
```

Run one named instance on Windows:

```powershell
./scripts/run_instance.ps1 -Name primary
```

Runtime behavior:

- Reads instance metadata from `config/instances.yaml`
- Sets `CDP_URL` and `CONFIG_PATH`
- Starts `python -m x_scrape_cdp.cli run`

---

## Docker Compose (Multi Listener)

Compose file: [`docker/compose.multi.yaml`](docker/compose.multi.yaml)

Deployment lanes:

- `listener-primary` -> uses host CDP `9222`
- `listener-secondary` -> uses host CDP `9223`

Start:

```bash
docker compose -f docker/compose.multi.yaml up --build
```

Note: each listener still depends on a separately launched and authenticated Chrome profile on the host machine.

---

## Troubleshooting

### Session invalid on startup

- Reopen the same `user-data-dir` profile in Chrome.
- Confirm login in `https://x.com/home`.
- Re-run `validate-session`.

### CDP endpoint not reachable

- Check launcher output endpoint.
- Open `http://127.0.0.1:9222/json/version` in browser.
- Ensure no firewall or port collision.

### No new posts detected

- Verify `targets` list in config.
- Increase `navigation.scroll_rounds`.
- Check whether IDs are already present in `seen_ids.json`.

### Selector drift after X UI changes

- Revalidate extraction selectors in `extract.py`.
- Re-test session indicators in `session.py`.

---

## Ops Checklist

- Recheck selectors after major X UI updates
- Back up `data/posts.jsonl` regularly
- Keep one listener identity per profile/IP unless using dedicated proxy segmentation
- Pin and update dependencies deliberately (`playwright`, `playwright-stealth`, `PyYAML`)

---

<p align="center">
  Built for robust session-aware listening and clean downstream data pipelines.
</p>
