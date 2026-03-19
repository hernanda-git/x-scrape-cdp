# Phase 7 — Data extraction

## Goal

Structured posts plus reliable new-post detection.

## Selectors (verify periodically)

| Field | Selector / method |
|-------|-------------------|
| Tweet root | `article[data-testid="tweet"]` or `div[data-testid="cellInnerDiv"]` |
| Text | `div[data-testid="tweetText"]` |
| User / name | `div[data-testid="User-Name"]` |
| Timestamp | `time` → `datetime` attribute |
| URL / ID | `a[href*="/status/"]` → parse ID from path |
| Media | `img[data-testid="tweetPhoto"]` or video sources |
| Engagement | `div[data-testid="like"]`, etc. |

## Extraction sketch

```python
async def extract_posts(page):
    tweets = await page.get_by_test_id("tweet").all()
    posts = []
    for tweet in tweets:
        try:
            text_el = tweet.get_by_test_id("tweetText")
            text = await text_el.inner_text() if await text_el.count() else ""
            link_elem = tweet.locator("a[href*='/status/']").first
            url = await link_elem.get_attribute("href")
            tweet_id = url.split("/status/")[-1]
            timestamp = await tweet.locator("time").get_attribute("datetime")
            photos = tweet.get_by_test_id("tweetPhoto")
            media = [await img.get_attribute("src") for img in await photos.all()] or None
            posts.append({
                "id": tweet_id,
                "text": text.strip(),
                "timestamp": timestamp,
                "url": f"https://x.com{url}",
                "media": media,
            })
        except Exception:
            continue
    return posts
```

## Listener logic

1. Load `seen_ids` store (e.g. `seen_ids.json`).
2. Extract current posts; keep those whose IDs are not in `seen`.
3. Append new posts to `posts.jsonl` (append-only); update `seen`.

Optional: Discord/Telegram webhook on new posts.

## Acceptance criteria

- [ ] Deduplication by tweet ID is deterministic.
- [ ] JSONL append and `seen` update are atomic enough for your crash scenarios (document strategy).

## Dependencies

- [Phase 6 — Navigation](./phase-06-navigation-listener.md)

## Next phase

→ [Phase 8 — AI agent integration (optional)](./phase-08-ai-agent-integration.md)
