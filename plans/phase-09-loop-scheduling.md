# Phase 9 — Loop & scheduling

## Goal

Continuous listening with sane backoff and jitter.

## Pattern

```python
async def listener_loop(targets, interval_min=5):
    while True:
        for username in targets:
            posts = await scrape_profile(f"https://x.com/{username}")
            new_posts = detect_new(posts)
            if new_posts:
                save_and_notify(new_posts)
        await asyncio.sleep(random.uniform(interval_min * 60, interval_min * 60 + 120))
```

## Operations

- **24/7:** cron, systemd, supervisor, or process manager of choice.
- **State:** history + dedupe by tweet ID.
- **Timing:** randomize interval (e.g. 3–12 minutes) and add jitter between targets if needed.

## Acceptance criteria

- [ ] Single-instance loop exits cleanly on SIGINT/SIGTERM (if required).
- [ ] Logs include run timestamp, success/failure, and new-post count.

## Dependencies

- [Phase 7 — Data extraction](./phase-07-data-extraction.md) (Phase 8 optional)

## Next phase

→ [Phase 10 — Multi-instance scaling](./phase-10-multi-instance-scaling.md)
