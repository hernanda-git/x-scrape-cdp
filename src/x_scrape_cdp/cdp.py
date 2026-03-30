from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from playwright.async_api import Browser, BrowserContext, Page, Playwright, async_playwright

logger = logging.getLogger("x_scrape_cdp.cdp")


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

    raw = cookie_file.strip()
    if not raw:
        return

    cookies = _cookies_from_path_or_inline(raw)
    if cookies:
        await context.add_cookies(cookies)


def _cookies_from_path_or_inline(raw: str) -> list[dict[str, Any]]:
    """
    Resolve cookie data from a filesystem path (read file contents) or from inline
    text (Netscape export or JSON array) when ``raw`` is not an existing file path.
    """
    path = Path(raw).expanduser()
    if path.is_file():
        text = path.read_text(encoding="utf-8")
        return _parse_cookie_text(text, path_suffix=path.suffix.lower())
    return _parse_cookie_text(raw, path_suffix=None)


def _parse_cookie_text(text: str, path_suffix: str | None) -> list[dict[str, Any]]:
    """Parse Playwright JSON cookie list or Netscape cookie export text."""
    t = text.strip()
    if not t:
        return []

    want_json = path_suffix == ".json" or t.startswith("[")
    if want_json:
        try:
            data = json.loads(t)
            return data if isinstance(data, list) else []
        except json.JSONDecodeError:
            if path_suffix == ".json":
                return []

    return _parse_netscape_lines(t)


def _parse_netscape_lines(text: str) -> list[dict[str, Any]]:
    cookies: list[dict[str, Any]] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        parts = line.split("\t")
        if len(parts) != 7:
            continue

        domain, _, cookie_path, secure_flag, expires_raw, name, value = parts
        cookie: dict[str, Any] = {
            "name": name,
            "value": value,
            "domain": domain,
            "path": cookie_path or "/",
            "secure": secure_flag.upper() == "TRUE",
        }

        try:
            expires_int = int(expires_raw)
            if expires_int > 0:
                cookie["expires"] = float(expires_int)
        except ValueError:
            pass

        cookies.append(cookie)
    return cookies


async def connect_playwright(cdp_http_url: str) -> PlaywrightConnection:
    try:
        p = await async_playwright().start()
        browser = await p.chromium.connect_over_cdp(cdp_http_url)
    except Exception as exc:
        raise RuntimeError(
            f"Failed connecting to CDP URL '{cdp_http_url}'. "
            "Check CDP_URL and confirm Chrome is running with --remote-debugging-port."
        ) from exc

    contexts = browser.contexts
    if not contexts:
        logger.warning("No browser contexts found, creating new context")
        context = await browser.new_context()
    else:
        context = contexts[0]

    pages = context.pages
    if not pages:
        logger.warning("No pages in context, creating new page")
        page = await context.new_page()
    else:
        page = pages[0]

    return PlaywrightConnection(playwright=p, browser=browser, context=context, page=page)