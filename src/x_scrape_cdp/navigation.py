from __future__ import annotations

import asyncio
import random

from playwright.async_api import Page


async def open_profile(
    page: Page,
    username: str,
    *,
    replies: bool = False,
    wait_until: str = "domcontentloaded",
) -> None:
    suffix = "/with_replies" if replies else ""
    url = f"https://x.com/{username}{suffix}"
    await page.goto(url, wait_until=wait_until)


async def human_warmup(page: Page) -> None:
    await page.mouse.move(100, 200, steps=8)
    await asyncio.sleep(random.uniform(0.4, 1.2))
    await page.mouse.wheel(0, random.randint(120, 260))
    await asyncio.sleep(random.uniform(0.5, 1.4))


async def gentle_scroll_for_fresh_posts(
    page: Page, rounds: int, pause_range_sec: tuple[float, float]
) -> None:
    low, high = pause_range_sec
    for _ in range(rounds):
        distance = random.randint(500, 1100)
        await page.mouse.wheel(0, distance)
        await asyncio.sleep(random.uniform(low, high))
