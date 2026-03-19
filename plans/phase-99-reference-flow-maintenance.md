# Reference — End-to-end flow, skeleton, edge cases, maintenance

## High-level flow

1. Launch Chrome + log in once  
2. Export cookies **or** use `user-data-dir`  
3. Connect Playwright over CDP (e.g. 9222)  
4. Apply stealth + `add_cookies` if needed  
5. Navigate to `https://x.com/TARGET` + human scroll/mouse  
6. Extract tweets via `data-testid` selectors  
7. Compare IDs → save only new  
8. *(Optional)* AI agent control  
9. Sleep random interval → loop  
10. Scale: multiple ports + proxies  

## Sample listener skeleton

```python
import asyncio
import json
import os
import random

from playwright.async_api import async_playwright
from playwright_stealth import stealth_async

COOKIES_PATH = "cookies.json"
SEEN_IDS_PATH = "seen_ids.json"


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        context = browser.contexts[0]
        page = context.pages[0] if context.pages else await context.new_page()

        if os.path.exists(COOKIES_PATH):
            with open(COOKIES_PATH) as f:
                await context.add_cookies(json.load(f))

        await stealth_async(page)

        while True:
            posts = await extract_posts(page, "https://x.com/elonmusk")
            seen = load_seen()
            new_ones = [p for p in posts if p["id"] not in seen]
            if new_ones:
                save_new(new_ones)
                print(f"NEW POSTS: {len(new_ones)}")
            await asyncio.sleep(random.uniform(240, 600))


asyncio.run(main())
```

Expand with full `extract_posts` and file helpers from Phase 7.

## Detection evasion and edge cases (2026)

- **Behavioral:** random mouse moves, variable delays; limit scrolls to 3–5.
- **IP/session:** residential proxy per instance; rotate cookies every 7–14 days if needed.
- **UI changes:** `data-testid` is relatively stable—if broken, fallback to `page.content()` + LLM parsing; run a weekly smoke test.
- **Rate limits / CAPTCHAs:** pause 30–60 minutes or switch profile.
- **Media / threads:** lazy-loaded images → short `wait_for_timeout` after scroll (e.g. ~800 ms).
- **Multi-account:** one browser context per account or separate CDP endpoints.

## Maintenance & monitoring

| Cadence | Action |
|---------|--------|
| Weekly | Test one account; refresh selectors if needed |
| Ongoing | Logs: timestamp, success/fail, new post count |
| Alerts | Webhook on errors or unusual volume (e.g. >5 new posts) if that fits your use case |
| Backup | Git + daily JSONL export |

## Recommended rollout

Start with a **single profile** using `user-data-dir`. When stable, add proxies and multi-instance scaling (Phase 10).
