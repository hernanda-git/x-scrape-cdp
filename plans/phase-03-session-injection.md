# Phase 3 — Session injection (CDP)

## Goal

Reuse the login inside automation connected over CDP.

## Tasks

1. Start Chrome with the same flags as Phase 1 (or attach to an already running instance).
2. If using exported cookies: after connecting via CDP, call `context.add_cookies(cookies)` from the Playwright cookie JSON.
3. Validate session:
   - Navigate to `https://x.com`
   - Confirm logged-in signals (e.g. avatar, Home tab).

## Persistence note

With `user-data-dir`, injection is often optional—the profile retains cookies and `localStorage` automatically.

## Outputs

- Confirmed authenticated context when automation attaches.

## Acceptance criteria

- [ ] CDP-attached code sees the same logged-in state as manual Chrome.
- [ ] Cookie path (file vs profile-only) is documented in code/config.

## Dependencies

- [Phase 2 — Authentication capture](./phase-02-authentication-capture.md)

## Next phase

→ [Phase 4 — CDP connection layer](./phase-04-cdp-connection.md)
