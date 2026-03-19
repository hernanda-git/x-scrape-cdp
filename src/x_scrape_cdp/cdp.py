from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from playwright.async_api import Browser, BrowserContext, Page, Playwright, async_playwright


@dataclass
class PlaywrightConnection:
    playwright: Playwright
    browser: Browser
    context: BrowserContext
    page: Page

    async def close(self) -> None:
        await self.playwright.stop()


async def load_cookies_if_configured(context: BrowserContext, cookie_file: str | None) -> None:
    if not cookie_file:
        return

    path = Path(cookie_file)
    if not path.exists():
        return

    with path.open("r", encoding="utf-8") as f:
        cookies = json.load(f)
    if isinstance(cookies, list) and cookies:
        await context.add_cookies(cookies)


async def connect_playwright(cdp_http_url: str) -> PlaywrightConnection:
    try:
        p = await async_playwright().start()
        browser = await p.chromium.connect_over_cdp(cdp_http_url)
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(
            f"Failed connecting to CDP URL '{cdp_http_url}'. "
            "Check CDP_URL and confirm Chrome is running with --remote-debugging-port."
        ) from exc

    contexts = browser.contexts
    if contexts:
        context = contexts[0]
    else:
        context = await browser.new_context()

    pages = context.pages
    if pages:
        page = pages[0]
    else:
        page = await context.new_page()

    return PlaywrightConnection(playwright=p, browser=browser, context=context, page=page)
