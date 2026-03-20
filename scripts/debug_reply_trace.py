from __future__ import annotations

import asyncio
import json
import logging

from playwright.async_api import Page

from x_scrape_cdp.cdp import connect_playwright
from x_scrape_cdp.config import load_settings
from x_scrape_cdp.extract import TWEET_ARTICLE_EXTRACT_JS


async def _debug_on_page(page: Page, url: str, *, label: str) -> None:
    await page.goto(url, wait_until="domcontentloaded")
    # X often loads tweet content after initial DOM load.
    await page.wait_for_timeout(6000)

    # Status-detail pages often wrap tweets differently than the timeline DOM.
    locators = {
        "any_[data-testid='tweet']": page.locator("[data-testid='tweet']"),
        "article_[data-testid='tweet']": page.locator("article[data-testid='tweet']"),
        "div_[data-testid='tweet']": page.locator("div[data-testid='tweet']"),
    }
    counts = {k: await v.count() for k, v in locators.items()}
    if all(v == 0 for v in counts.values()):
        print(f"[{label}] {url} :: no tweet container found. counts={counts}")
        return

    # Prefer article container if present, else fall back to any match.
    handle = None
    for preferred in ["article_[data-testid='tweet']", "any_[data-testid='tweet']", "div_[data-testid='tweet']"]:
        if counts.get(preferred, 0) > 0:
            nodes = locators[preferred]
            handle = await nodes.first.element_handle()
            break

    if not handle:
        print(f"[{label}] {url} :: could not get element_handle()")
        return

    try:
        extracted = await page.evaluate(TWEET_ARTICLE_EXTRACT_JS, handle)

        dom_debug = await page.evaluate(
            """
            (el) => {
              const q = (root, sel) => root.querySelector(sel);
              const qa = (root, sel) => Array.from(root.querySelectorAll(sel));

              const quoteRoot = q(el, '[data-testid="quoteTweet"]');
              const socialEl = q(el, '[data-testid="socialContext"]');
              const socialText = socialEl ? (socialEl.textContent || '').trim() : null;

              const linksAllStatus = qa(el, 'a[href*="/status/"]')
                .map(a => a.getAttribute('href'))
                .filter(Boolean);

              const linksSocialStatus = socialEl
                ? qa(socialEl, 'a[href*="/status/"]').map(a => a.getAttribute('href')).filter(Boolean)
                : [];

              const timeAnchors = qa(el, 'time').map(t => {
                if (quoteRoot && quoteRoot.contains(t)) return null;
                const parentA = t.closest('a');
                const href = parentA ? parentA.getAttribute('href') : null;
                return {
                  datetime: t.getAttribute('datetime'),
                  closestATagHref: href,
                  closestATagStatusId: href ? String(href).match(/\\/status\\/(\\d+)/)?.[1] ?? null : null,
                };
              }).filter(Boolean);

              const kindGuess = socialText ? socialText.toLowerCase() : '';

              return {
                hasSocialEl: !!socialEl,
                socialText,
                linksAllStatus,
                linksSocialStatus,
                timeAnchors,
                kindGuessSample: kindGuess.slice(0, 80),
                hasQuoteRoot: !!quoteRoot,
              };
            }
            """,
            handle,
        )

        print(f"\n==== {label} ====")
        print("url:", url)
        print("extracted:", json.dumps(extracted, ensure_ascii=False, indent=2) if extracted else None)
        print("dom_debug:", json.dumps(dom_debug, ensure_ascii=False, indent=2))
    finally:
        await handle.dispose()


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    settings = load_settings("config/test_0xvalarion.yaml")
    conn = await connect_playwright(settings.cdp_http_url)
    try:
        account = settings.targets[0].lstrip("@")
        ids = [
            ("parent_ref", "2034767814800941353"),
            ("reply_ref", "2034770435108479460"),
        ]

        for label, tid in ids:
            url = f"https://x.com/{account}/status/{tid}"
            await _debug_on_page(conn.page, url, label=label)
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())

