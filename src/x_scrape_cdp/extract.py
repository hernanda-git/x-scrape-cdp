from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Awaitable, Callable

from playwright.async_api import Page

from .config import Settings

TWEET_URL_RE = re.compile(r"/status/(\d+)")
TEXT_RE = re.compile(r'<div[^>]*data-testid="tweetText"[^>]*>(.*?)</div>', re.DOTALL)
STRIP_TAGS_RE = re.compile(r"<[^>]+>")

SCHEMA_VERSION = 2

# Load the tweet extraction script from external JS file
_JS_FILE = Path(__file__).parent / "js" / "tweet_extract.js"
TWEET_ARTICLE_EXTRACT_JS = _JS_FILE.read_text(encoding="utf-8")


@dataclass
class Post:
    """Structured post record aligned with schema_version in to_dict()."""

    id: str
    url: str
    scraped_at: str
    listened_target: str
    content_text: str
    content_published_at: str | None
    author_handle: str | None
    author_display_name: str | None
    classification_kind: str
    social_context: str | None
    engagement_replies: int | None
    engagement_retweets: int | None
    engagement_likes: int | None
    engagement_views: int | None
    quoted_tweet: dict[str, Any] | None
    media: list[dict[str, Any]]
    bookmarks: int | None = None

    def to_dict(self) -> dict[str, Any]:
        """Flat JSONL record (schema_version 2)."""
        media_list = [
            str(m["url"])
            for m in self.media
            if isinstance(m, dict) and m.get("url")
        ]
        return {
            "schema_version": SCHEMA_VERSION,
            "id": self.id,
            "handle": self.author_handle,
            "text": self.content_text,
            "published_at": self.content_published_at,
            "replies": self.engagement_replies,
            "retweets": self.engagement_retweets,
            "likes": self.engagement_likes,
            "views": self.engagement_views,
            "bookmarks": self.bookmarks,
            "quoted_tweet": self.quoted_tweet,
            "media": media_list,
            "kind": self.classification_kind,
            "url": self.url,
            "listened_target": self.listened_target,
            "scraped_at": self.scraped_at,
            "social_context": self.social_context,
        }

    @classmethod
    def from_dom_extract(
        cls,
        data: dict[str, Any],
        *,
        listened_target: str,
        scraped_at: str,
    ) -> Post | None:
        if not data or not data.get("id"):
            return None
        href = data.get("statusHref") or ""
        url = href if href.startswith("http") else f"https://x.com{href}" if href else ""
        quoted = data.get("quoted")
        if quoted and isinstance(quoted, dict):
            q_clean = {
                k: v
                for k, v in {
                    "id": quoted.get("id"),
                    "url": quoted.get("url"),
                    "text": quoted.get("text"),
                    "author_handle": quoted.get("author_handle"),
                }.items()
                if v is not None
            }
            quoted = q_clean or None
        else:
            quoted = None
        eng = data.get("engagement") or {}
        media = data.get("mediaItems") or []
        if not isinstance(media, list):
            media = []
        return cls(
            id=str(data["id"]),
            url=url,
            scraped_at=scraped_at,
            listened_target=listened_target,
            content_text=(data.get("mainText") or "").strip(),
            content_published_at=data.get("ts"),
            author_handle=data.get("authorHandle"),
            author_display_name=data.get("displayName"),
            classification_kind=str(data.get("kind") or "original"),
            social_context=data.get("socialContext"),
            engagement_replies=eng.get("replies"),
            engagement_retweets=eng.get("retweets"),
            engagement_likes=eng.get("likes"),
            engagement_views=eng.get("views"),
            quoted_tweet=quoted,
            media=[m for m in media if isinstance(m, dict) and m.get("url")],
            bookmarks=eng.get("bookmarks"),
        )


async def extract_visible_posts(page: Page, listened_target: str) -> list[Post]:
    nodes = page.locator('[data-testid="tweet"]')
    count = await nodes.count()
    posts: list[Post] = []
    now = datetime.now(timezone.utc).isoformat()

    for i in range(count):
        handle = await nodes.nth(i).element_handle()
        if not handle:
            continue
        try:
            raw = await page.evaluate(TWEET_ARTICLE_EXTRACT_JS, handle)
        finally:
            await handle.dispose()

        if not raw or not isinstance(raw, dict):
            continue
        post = Post.from_dom_extract(raw, listened_target=listened_target, scraped_at=now)
        if post:
            posts.append(post)

    return posts


async def extract_posts_agent(page: Page, prompt_template: str | None = None) -> list[Post]:
    """Agent-based extraction - not implemented yet."""
    import warnings
    warnings.warn(
        "Agent-based extraction is not yet implemented. Using Playwright extraction instead.",
        UserWarning,
        stacklevel=2
    )
    return await extract_visible_posts(page, "")


def get_extractor(
    settings: Settings, listened_target: str
) -> Callable[[Page], Awaitable[list[Post]]]:
    if settings.extraction_mode == "agent":
        async def _agent(page: Page) -> list[Post]:
            return await extract_posts_agent(page, settings.extraction_prompt_template)
        return _agent

    async def _playwright(page: Page) -> list[Post]:
        return await extract_visible_posts(page, listened_target)

    return _playwright


def parse_posts_from_html(html: str) -> list[Post]:
    """Legacy HTML parse: minimal structure (no engagement)."""
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
                url=f"https://x.com/i/status/{tweet_id}",
                scraped_at=now,
                listened_target="unknown",
                content_text=text,
                content_published_at=None,
                author_handle=None,
                author_display_name=None,
                classification_kind="unknown",
                social_context=None,
                engagement_replies=None,
                engagement_retweets=None,
                engagement_likes=None,
                engagement_views=None,
                quoted_tweet=None,
                media=[],
            )
        )
    return posts