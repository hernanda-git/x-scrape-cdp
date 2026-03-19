from __future__ import annotations

import random
from dataclasses import dataclass

from playwright.async_api import Page
from playwright_stealth import stealth_async


@dataclass
class StealthProfile:
    viewport_width: int
    viewport_height: int
    user_agent: str | None = None
    jitter_percent: int = 10


def _jitter(base: int, jitter_percent: int) -> int:
    delta = max(1, int(base * (jitter_percent / 100.0)))
    return max(200, base + random.randint(-delta, delta))


async def apply_stealth(page: Page, profile: StealthProfile) -> None:
    width = _jitter(profile.viewport_width, profile.jitter_percent)
    height = _jitter(profile.viewport_height, profile.jitter_percent)
    await page.set_viewport_size({"width": width, "height": height})
    if profile.user_agent:
        await page.set_extra_http_headers({"User-Agent": profile.user_agent})
    await page.add_init_script(
        """
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
        """
    )
    await stealth_async(page)
