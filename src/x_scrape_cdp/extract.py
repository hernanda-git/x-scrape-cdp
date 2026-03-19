from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Awaitable, Callable

from playwright.async_api import Page
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from .config import Settings

TWEET_URL_RE = re.compile(r"/status/(\d+)")
TEXT_RE = re.compile(r'<div[^>]*data-testid="tweetText"[^>]*>(.*?)</div>', re.DOTALL)
STRIP_TAGS_RE = re.compile(r"<[^>]+>")


@dataclass
class Post:
    id: str
    text: str
    timestamp: str | None
    url: str
    media_urls: list[str]
    scraped_at: str

    def to_dict(self) -> dict:
        return asdict(self)


async def extract_visible_posts(page: Page) -> list[Post]:
    nodes = page.locator('[data-testid="tweet"]')
    count = await nodes.count()
    posts: list[Post] = []
    now = datetime.now(timezone.utc).isoformat()

    for i in range(count):
        node = nodes.nth(i)
        link = node.locator('a[href*="/status/"]').first
        href = await link.get_attribute("href")
        if not href:
            continue
        match = TWEET_URL_RE.search(href)
        if not match:
            continue

        text_locator = node.locator('[data-testid="tweetText"]')
        text_count = await text_locator.count()
        if text_count:
            # Some tweets render multiple text blocks; strict inner_text() can fail.
            if text_count == 1:
                text = await text_locator.inner_text()
            else:
                text = " ".join(
                    chunk.strip() for chunk in await text_locator.all_inner_texts() if chunk.strip()
                )
        else:
            text = ""
        time_locator = node.locator("time")
        if await time_locator.count():
            ts = await time_locator.first.get_attribute("datetime")
        else:
            ts = None
        media_nodes = node.locator("img")
        media_urls: list[str] = []
        media_count = await media_nodes.count()
        for j in range(media_count):
            try:
                src = await media_nodes.nth(j).get_attribute("src", timeout=1500)
            except PlaywrightTimeoutError:
                continue
            if src and src.startswith("http"):
                media_urls.append(src)

        posts.append(
            Post(
                id=match.group(1),
                text=text.strip(),
                timestamp=ts,
                url=f"https://x.com{href}" if href.startswith("/") else href,
                media_urls=media_urls,
                scraped_at=now,
            )
        )

    return posts


async def extract_posts_agent(page: Page, prompt_template: str | None = None) -> list[Post]:
    raise NotImplementedError("Agent extraction is optional and not implemented by default.")


def get_extractor(settings: Settings) -> Callable[[Page], Awaitable[list[Post]]]:
    if settings.extraction_mode == "agent":
        async def _agent(page: Page) -> list[Post]:
            return await extract_posts_agent(page, settings.extraction_prompt_template)
        return _agent
    return extract_visible_posts


def parse_posts_from_html(html: str) -> list[Post]:
    now = datetime.now(timezone.utc).isoformat()
    ids = list(dict.fromkeys(TWEET_URL_RE.findall(html)))
    text_matches = TEXT_RE.findall(html)
    posts: list[Post] = []
    for idx, tweet_id in enumerate(ids):
        text_raw = text_matches[idx] if idx < len(text_matches) else ""
        text = STRIP_TAGS_RE.sub("", text_raw).strip()
        posts.append(
            Post(
                id=tweet_id,
                text=text,
                timestamp=None,
                url=f"https://x.com/i/status/{tweet_id}",
                media_urls=[],
                scraped_at=now,
            )
        )
    return posts
