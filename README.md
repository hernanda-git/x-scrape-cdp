# x-scrape-cdp

X profile post listener using a real Chrome session connected via CDP and Playwright.

## Safety and scope

- Risk policy: [`docs/RISKS.md`](docs/RISKS.md)
- Operational boundaries: [`docs/SCOPE.md`](docs/SCOPE.md)
- Session decision: [`docs/ADR-001-session-strategy.md`](docs/ADR-001-session-strategy.md)

## Prerequisites

- Python 3.11+
- Google Chrome installed
- Windows PowerShell (or bash on macOS/Linux)

## Quick start

1. Create a virtual environment and install dependencies:
   - `python -m venv .venv`
   - `.venv\Scripts\activate` (Windows) or `source .venv/bin/activate` (macOS/Linux)
   - `pip install -e .[dev]`
2. Install Playwright browser support:
   - `playwright install chromium`
3. Launch Chrome with CDP:
   - Windows: `./scripts/launch_chrome.ps1 -Port 9222 -UserDataDir ./data/chrome_profile`
   - macOS/Linux: `./scripts/launch_chrome.sh 9222 ./data/chrome_profile`
4. Open X in that browser and log in manually (including 2FA if required).
5. Validate session:
   - `python -m x_scrape_cdp.cli validate-session`
6. Run one cycle:
   - `python -m x_scrape_cdp.cli once`
7. Run loop:
   - `python -m x_scrape_cdp.cli run`

## Authentication capture workflow

1. Start Chrome via the launcher script with the same `user-data-dir`.
2. Visit `https://x.com/` and log in.
3. Wait around 60 seconds after successful login.
4. Keep using the same profile for listener runs.

Optional cookie-file mode is available via `session.cookie_file` in `config/default.yaml`.

## Config

Default config is at [`config/default.yaml`](config/default.yaml). You can override with:

- `CONFIG_PATH` environment variable
- `CDP_URL` environment variable

## Data outputs

- Seen IDs: `data/seen_ids.json`
- Appended posts: `data/posts.jsonl`

## Maintenance

- Re-check selectors weekly or after major X UI updates.
- Backup `data/posts.jsonl` to external storage if running long-term.
- Prefer one listener instance per IP unless you configure separate proxies.

## Multi-instance

- Define instances in [`config/instances.yaml`](config/instances.yaml).
- Launch one by name on Windows:
  - `./scripts/run_instance.ps1 -Name primary`
