# Phase 2 — Authentication capture

## Goal

Obtain a valid logged-in session for X.

## Tasks

1. Open the Chrome instance from Phase 1.
2. Manually log into X (complete 2FA if enabled).
3. Stay on x.com for 30–60 seconds so cookies settle.
4. Either:
   - Export cookies as `cookies.json` (Playwright format) or `cookies.txt`, **or**
   - Rely on persistent `user-data-dir` only (no export).

If exporting: use the extension → export → copy into the project folder.

## Outputs

- `cookies.json` (optional) **or** persistent profile with session.
- Document which method the project uses.

## Nuances

- Aged accounts (~30+ days) are generally trusted more.
- Consider storing multiple cookie sets for rotation (advanced).

## Acceptance criteria

- [ ] Browser shows a logged-in X session after restart (if using profile persistence) **or** valid cookie file exists and loads.

## Dependencies

- [Phase 1 — Preparation](./phase-01-preparation.md)

## Next phase

→ [Phase 3 — Session injection (CDP)](./phase-03-session-injection.md)
