from __future__ import annotations

from playwright.async_api import Page


async def is_logged_in(page: Page) -> bool:
    login_cta = page.get_by_role("link", name="Log in")
    if await login_cta.count() > 0:
        return False

    home_link = page.get_by_role("link", name="Home")
    if await home_link.count() > 0:
        return True

    primary_timeline = page.locator('[data-testid="primaryColumn"]')
    if await primary_timeline.count() > 0:
        return True

    return False
