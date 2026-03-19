from __future__ import annotations

from playwright.async_api import Page


async def is_logged_in(page: Page) -> bool:
    # Strong negative signals first: login routes or auth form.
    current_url = page.url or ""
    if "/i/flow/login" in current_url or current_url.rstrip("/").endswith("/login"):
        return False

    # Login flow has username autocomplete; avoid matching the post composer.
    login_form = page.locator('input[autocomplete="username"]')
    if await login_form.count() > 0:
        return False

    # If we are already on /home and not on an auth route, treat as logged in.
    # X may lazily hydrate selectors after domcontentloaded.
    if "://x.com/home" in current_url:
        return True

    # Positive signals that are language-agnostic and stable across locales.
    if await page.locator('[data-testid="AppTabBar_Home_Link"]').count() > 0:
        return True

    if await page.locator('[data-testid="SideNav_AccountSwitcher_Button"]').count() > 0:
        return True

    if await page.locator('[data-testid="primaryColumn"]').count() > 0:
        return True

    return False


async def get_logged_in_profile_handle(page: Page) -> str | None:
    """
    Best-effort handle for the logged-in account (e.g. symbiomes), from bottom nav profile link.
    """
    try:
        link = page.locator('[data-testid="AppTabBar_Profile_Link"]')
        if await link.count() == 0:
            return None
        href = await link.first.get_attribute("href")
        if not href:
            return None
        parts = [p for p in href.strip("/").split("/") if p]
        if not parts:
            return None
        handle = parts[0]
        if handle.startswith("i") or "flow" in handle:
            return None
        return handle
    except Exception:
        return None
