from __future__ import annotations

import random
from dataclasses import dataclass

from playwright.async_api import Page

# Explicit version detection for playwright-stealth
try:
    import playwright_stealth
    _STEALTH_VERSION = getattr(playwright_stealth, "__version__", None)
    # Default to 2.x if version not found (newer versions don't have __version__)
    if _STEALTH_VERSION is None:
        _STEALTH_VERSION = "2.x"
    _HAS_STEALTH_ASYNC = True
except ImportError:
    _STEALTH_VERSION = None
    _HAS_STEALTH_ASYNC = False


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

    if not _HAS_STEALTH_ASYNC:
        return

    # Use version-appropriate API
    if _STEALTH_VERSION and _STEALTH_VERSION.startswith("1."):
        # playwright-stealth 1.x
        from playwright_stealth import stealth_async
        await stealth_async(page)
    else:
        # playwright-stealth 2.x
        from playwright_stealth.stealth import Stealth
        await Stealth().apply_stealth_async(page)