# Phase 6 — Navigation & interaction (listener core)

## Goal

Mimic a real user visiting a profile timeline.

## Target URL

- `https://x.com/TARGET_USERNAME`
- Optional: `/with_replies` if you need replies in scope.

## Pattern

```python
await page.goto(url, wait_until="networkidle")
await page.wait_for_selector("[data-testid='tweet']", timeout=15000)

# Human simulation
await page.mouse.move(300 + random.randint(-50, 50), 400 + random.randint(-50, 50))
await asyncio.sleep(random.uniform(1.5, 3.5))

# Light scroll for latest posts (avoid deep scrolling)
for _ in range(3):
    await page.evaluate("window.scrollBy(0, window.innerHeight * 0.6)")
    await asyncio.sleep(random.uniform(2, 4))
```

## Validation

Timeline shows recent tweets and selectors resolve.

## Acceptance criteria

- [ ] Navigation tolerates slow network within timeouts.
- [ ] Scroll depth and count are capped (e.g. 3–5 passes) to limit rate-limit risk.

## Dependencies

- [Phase 5 — Anti-detection](./phase-05-anti-detection.md)

## Next phase

→ [Phase 7 — Data extraction](./phase-07-data-extraction.md)
