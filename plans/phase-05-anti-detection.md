# Phase 5 — Anti-detection layer

## Goal

Reduce fingerprinting and automation signals for X’s 2026 stack.

## Apply in order

```python
from playwright_stealth import stealth_async

await stealth_async(page)
await page.add_init_script(
    "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
)
```

Additional measures:

- **User-Agent:** real Chrome string; rotate occasionally across runs.
- **Viewport:** e.g. `await page.set_viewport_size({"width": 1920, "height": 1080})` with ±10% jitter.
- **Screen / WebGL:** optional `context.add_init_script` to keep `screen` dimensions and WebGL plausible and stable per session.
- **No headless** in UA; CDP to real Chrome already helps.

## Checklist (target state)

- `navigator.webdriver` not truthy in the way detectors expect
- WebGL fingerprint random but consistent per session
- Valid-looking canvas/WebGL
- No burst of inhuman actions

## X-specific

Random mouse movement and human delays (tie in with Phase 6 navigation).

## Acceptance criteria

- [ ] Stealth applied once per page (or per policy you document).
- [ ] Viewport and UA strategy documented.

## Dependencies

- [Phase 4 — CDP connection](./phase-04-cdp-connection.md)

## Next phase

→ [Phase 6 — Navigation & interaction](./phase-06-navigation-listener.md)
