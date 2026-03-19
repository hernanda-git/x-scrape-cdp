# Phase 1 — Preparation layer

## Goal

Ready the environment for an X-specific listener.

## Tasks

1. Create or age one or more dummy or real X accounts (phone-verified preferred; X is strict on new accounts).
2. Install latest Chrome/Chromium (stable channel).
3. Install Python tooling:
   - `pip install playwright playwright-stealth`
   - `playwright install chromium`
4. Launch Chrome with remote debugging and a dedicated profile.

### macOS / Linux

```bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9222 \
  --user-data-dir=./x_profile_listener \
  --no-first-run --no-default-browser-check
```

### Windows

Use `chrome.exe` with the same flags (adjust path to your Chrome install).

5. Optional: install a cookie exporter extension (e.g. “Get cookies.txt LOCALLY” or “Cookie-Editor”) in this Chrome profile.

**Recommended simplification:** use `--user-data-dir` as above and log in manually once. Session persists across restarts; cookie export may be unnecessary.

## Acceptance criteria

- [ ] Chrome launches with debugging on the chosen port (e.g. 9222).
- [ ] Dedicated user data directory exists and is reused.
- [ ] Playwright + stealth packages installed; Chromium fetched for Playwright if needed.

## Outputs

- Runnable Chrome + debug port + profile path documented for the project.

## Dependencies

- [Phase 0 — Context and risks](./phase-00-context-and-risks.md)

## Next phase

→ [Phase 2 — Authentication capture](./phase-02-authentication-capture.md)
