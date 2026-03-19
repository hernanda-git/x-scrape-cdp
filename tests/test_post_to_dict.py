from __future__ import annotations

from x_scrape_cdp.extract import Post, SCHEMA_VERSION


def test_to_dict_flat_schema_v2():
    p = Post(
        id="99",
        url="https://x.com/a/status/99",
        scraped_at="2026-01-01T00:00:00+00:00",
        listened_target="a",
        content_text="hello",
        content_published_at="2026-01-01T01:00:00.000Z",
        author_handle="a",
        author_display_name="A",
        classification_kind="reply",
        social_context="Replying to @a",
        engagement_replies=1,
        engagement_retweets=2,
        engagement_likes=3,
        engagement_views=100,
        quoted_tweet=None,
        media=[{"kind": "image", "url": "https://example.com/i.jpg"}],
        bookmarks=0,
        reply_to_status_id="88",
        reply_to_handle="a",
    )
    d = p.to_dict()
    assert d["schema_version"] == SCHEMA_VERSION == 2
    assert d["id"] == "99"
    assert d["handle"] == "a"
    assert d["text"] == "hello"
    assert d["kind"] == "reply"
    assert d["reply_to_status_id"] == "88"
    assert d["reply_to_handle"] == "a"
    assert d["media"] == ["https://example.com/i.jpg"]
    assert "classification" not in d
    assert "content" not in d


def test_from_dom_extract_sets_reply_and_kind():
    raw = {
        "id": "2034770435108479460",
        "statusHref": "/0xValarion/status/2034770435108479460",
        "mainText": "$TAO tp1 booked",
        "ts": "2026-03-20T10:00:00.000Z",
        "kind": "reply",
        "socialContext": "Replying to @0xValarion",
        "inReplyToStatusId": "2034770000000000000",
        "inReplyToHandle": "0xValarion",
        "engagement": {
            "replies": None,
            "retweets": None,
            "likes": 5,
            "views": 100,
            "bookmarks": None,
        },
        "quoted": None,
        "authorHandle": "0xValarion",
        "displayName": "Val",
        "mediaItems": [],
    }
    post = Post.from_dom_extract(
        raw, listened_target="0xValarion", scraped_at="2026-03-20T12:00:00+00:00"
    )
    assert post is not None
    assert post.classification_kind == "reply"
    assert post.reply_to_status_id == "2034770000000000000"
    assert post.reply_to_handle == "0xValarion"
    flat = post.to_dict()
    assert flat["kind"] == "reply"
    assert flat["reply_to_status_id"] == "2034770000000000000"
