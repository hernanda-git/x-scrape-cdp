# Phase 4 — CDP connection layer

## Goal

Establish full Playwright control over the real Chrome instance.

## Pattern (Python)

```python
import asyncio
from playwright.async_api import async_playwright

async def get_cdp_browser():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        context = browser.contexts[0]  # or create new
        page = context.pages[0] if context.pages else await context.new_page()
        return browser, context, page
```

## Result

Control of the live logged-in browser: pages, context, and CDP-backed execution.

## Acceptance criteria

- [ ] Script connects without launching a second browser.
- [ ] Default context/page selection is correct for your workflow (document if using multiple contexts).

## Dependencies

- [Phase 3 — Session injection](./phase-03-session-injection.md)

## Next phase

→ [Phase 5 — Anti-detection layer](./phase-05-anti-detection.md)
