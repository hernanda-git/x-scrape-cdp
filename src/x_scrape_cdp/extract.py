from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable

from playwright.async_api import Page

from .config import Settings

TWEET_URL_RE = re.compile(r"/status/(\d+)")
TEXT_RE = re.compile(r'<div[^>]*data-testid="tweetText"[^>]*>(.*?)</div>', re.DOTALL)
STRIP_TAGS_RE = re.compile(r"<[^>]+>")

SCHEMA_VERSION = 1

# Extract structured fields from one tweet article (DOM root = data-testid="tweet").
TWEET_ARTICLE_EXTRACT_JS = """
(el) => {
  const q = (root, sel) => root.querySelector(sel);
  const qa = (root, sel) => Array.from(root.querySelectorAll(sel));

  const quoteRoot = q(el, '[data-testid="quoteTweet"]');
  const socialEl = q(el, '[data-testid="socialContext"]');
  const socialText = socialEl ? (socialEl.innerText || "").trim() : "";

  let statusHref = null;
  for (const a of qa(el, 'a[href*="/status/"]')) {
    if (quoteRoot && quoteRoot.contains(a)) continue;
    const h = a.getAttribute("href");
    if (!h) continue;
    if (/\\/status\\/\\d+/.test(h)) {
      statusHref = h;
      break;
    }
  }
  if (!statusHref) return null;
  const idMatch = statusHref.match(/\\/status\\/(\\d+)/);
  const id = idMatch ? idMatch[1] : null;
  if (!id) return null;

  const parseAriaCount = (testid) => {
    const btn = q(el, '[data-testid="' + testid + '"]');
    if (!btn) return null;
    const label = btn.getAttribute("aria-label") || "";
    const m = label.match(/([\\d,.]+)\\s*[KkMmBb]?/);
    if (!m) return null;
    let raw = m[1].replace(/,/g, "");
    if (raw.endsWith(".")) raw = raw.slice(0, -1);
    const n = parseFloat(raw);
    if (Number.isNaN(n)) return null;
    const mult = /[Kk]/.test(label) ? 1000 : /[Mm]/.test(label) ? 1000000 : /[Bb]/.test(label) ? 1000000000 : 1;
    return Math.round(n * mult);
  };

  const tweetTexts = qa(el, '[data-testid="tweetText"]');
  let mainText = "";
  if (quoteRoot) {
    const mainBlocks = tweetTexts.filter((t) => !quoteRoot.contains(t));
    mainText = mainBlocks.map((t) => (t.innerText || "").trim()).join(" ").trim();
  } else {
    mainText = tweetTexts.map((t) => (t.innerText || "").trim()).join(" ").trim();
  }

  let ts = null;
  for (const t of qa(el, "time")) {
    if (quoteRoot && quoteRoot.contains(t)) continue;
    ts = t.getAttribute("datetime");
    if (ts) break;
  }

  const st = socialText.toLowerCase();
  let kind = "original";
  if (st.includes("reposted") || st.includes("retweeted") || st.includes("repost")) {
    kind = "retweet";
  } else if (st.includes("replied")) {
    kind = "reply";
  }
  if (quoteRoot) {
    if (kind === "original") kind = "quote";
    else kind = kind + "_with_quote";
  }

  const mediaItems = [];
  for (const img of qa(el, "img")) {
    if (quoteRoot && quoteRoot.contains(img)) continue;
    const src = img.getAttribute("src");
    if (!src || !src.startsWith("http")) continue;
    if (src.includes("profile_images")) continue;
    if (src.includes("/emoji/")) continue;
    mediaItems.push({ kind: "image", url: src });
  }

  let quoted = null;
  if (quoteRoot) {
    let qh = null;
    let qid = null;
    for (const a of qa(quoteRoot, 'a[href*="/status/"]')) {
      const h = a.getAttribute("href");
      const m = h && h.match(/\\/status\\/(\\d+)/);
      if (m) {
        qh = h;
        qid = m[1];
        break;
      }
    }
    const qt = q(quoteRoot, '[data-testid="tweetText"]');
    const qUser = q(quoteRoot, '[data-testid="User-Name"]');
    let qAuthor = null;
    if (qUser) {
      for (const a of qa(qUser, 'a[href^="/"]')) {
        const h = a.getAttribute("href") || "";
        if (/^\\/[^/]+\\/?$/.test(h) && !h.includes("/i/")) {
          qAuthor = h.replace(/^\\//, "").split("/")[0] || null;
          break;
        }
      }
    }
    quoted = {
      id: qid,
      text: qt ? (qt.innerText || "").trim() : "",
      url: qh ? (qh.startsWith("http") ? qh : "https://x.com" + qh) : null,
      author_handle: qAuthor,
    };
  }

  const userNameRoot = q(el, '[data-testid="User-Name"]');
  let authorHandle = null;
  let displayName = null;
  if (userNameRoot) {
    for (const a of qa(userNameRoot, 'a[href^="/"]')) {
      const h = a.getAttribute("href") || "";
      if (/^\\/[^/]+\\/?$/.test(h) && !h.includes("/i/")) {
        authorHandle = h.replace(/^\\//, "").split("/")[0] || null;
        break;
      }
    }
    const sp = q(userNameRoot, "span");
    if (sp) displayName = (sp.innerText || "").trim() || null;
  }

  let views = null;
  for (const a of qa(el, "a")) {
    const href = a.getAttribute("href") || "";
    if (!href.includes("analytics")) continue;
    const lab = a.getAttribute("aria-label") || a.innerText || "";
    const m = lab.match(/([\\d,.]+)\\s*[KkMmBb]?/);
    if (m) {
      let raw = m[1].replace(/,/g, "");
      const n = parseFloat(raw);
      if (!Number.isNaN(n)) {
        const mult = /[Kk]/.test(lab) ? 1000 : /[Mm]/.test(lab) ? 1000000 : 1;
        views = Math.round(n * mult);
        break;
      }
    }
  }

  return {
    id,
    statusHref,
    mainText,
    ts,
    kind,
    socialContext: socialText || null,
    engagement: {
      replies: parseAriaCount("reply"),
      retweets: parseAriaCount("retweet"),
      likes: parseAriaCount("like"),
      views,
      bookmarks: parseAriaCount("bookmark"),
    },
    quoted,
    authorHandle,
    displayName,
    mediaItems,
  };
}
"""


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
        return {
            "schema_version": SCHEMA_VERSION,
            "id": self.id,
            "url": self.url,
            "scraped_at": self.scraped_at,
            "context": {"listened_target": self.listened_target},
            "author": {
                "handle": self.author_handle,
                "display_name": self.author_display_name,
            },
            "content": {
                "text": self.content_text,
                "published_at": self.content_published_at,
            },
            "classification": {
                "kind": self.classification_kind,
                "social_context": self.social_context,
            },
            "engagement": {
                "replies": self.engagement_replies,
                "retweets": self.engagement_retweets,
                "likes": self.engagement_likes,
                "views": self.engagement_views,
                "bookmarks": self.bookmarks,
            },
            "quoted_tweet": self.quoted_tweet,
            "media": self.media,
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
    raise NotImplementedError("Agent extraction is optional and not implemented by default.")


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
