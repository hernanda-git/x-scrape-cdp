from __future__ import annotations

import asyncio
import logging

from playwright.async_api import Page

from x_scrape_cdp.cdp import connect_playwright
from x_scrape_cdp.config import load_settings


async def _check(page: Page, url: str, *, status_id: str) -> None:
    await page.goto(url, wait_until="domcontentloaded")
    await page.wait_for_timeout(6000)

    res = await page.evaluate(
        """
        (statusId) => {
          const selfLinkCount = document.querySelectorAll(`a[href*="/status/${statusId}"]`).length;
          const tweetContainers = document.querySelectorAll('[data-testid="tweet"]').length;
          const articleTweetContainers = document.querySelectorAll('article[data-testid="tweet"]').length;
          const allDataTestIdsSample = Array.from(document.querySelectorAll('[data-testid]'))
            .slice(0, 30)
            .map(n => n.getAttribute('data-testid'));

          return {
            selfLinkCount,
            tweetContainers,
            articleTweetContainers,
            allDataTestIdsSample,
            bodyTextSample: (document.body ? document.body.innerText || '' : '').slice(0, 200),
          };
        }
        """,
        status_id,
    )

    print(f"\n=== {url} ===")
    print(res)


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    settings = load_settings("config/test_0xvalarion.yaml")
    conn = await connect_playwright(settings.cdp_http_url)
    try:
        account = settings.targets[0].lstrip("@")
        targets = ["2034767814800941353", "2034770435108479460"]
        for tid in targets:
            url = f"https://x.com/{account}/status/{tid}"
            await _check(conn.page, url, status_id=tid)
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())

