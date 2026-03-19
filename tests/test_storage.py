from __future__ import annotations

from x_scrape_cdp.extract import Post
from x_scrape_cdp.storage import append_posts_jsonl, filter_new, load_seen, save_seen_atomic


def _post(
    id_: str,
    text: str,
    url: str,
    scraped_at: str = "t",
    listened_target: str = "x",
) -> Post:
    return Post(
        id=id_,
        url=url,
        scraped_at=scraped_at,
        listened_target=listened_target,
        content_text=text,
        content_published_at=None,
        author_handle=None,
        author_display_name=None,
        classification_kind="original",
        social_context=None,
        engagement_replies=None,
        engagement_retweets=None,
        engagement_likes=None,
        engagement_views=None,
        quoted_tweet=None,
        media=[],
    )


def test_seen_roundtrip(tmp_data_dir):
    seen_file = tmp_data_dir / "seen_ids.json"
    save_seen_atomic(seen_file, {"1", "2", "3"})
    loaded = load_seen(seen_file)
    assert loaded == {"1", "2", "3"}


def test_filter_and_append(tmp_data_dir):
    posts_file = tmp_data_dir / "posts.jsonl"
    existing = {"1"}
    posts = [
        _post("1", "old", "u1"),
        _post("2", "new", "u2"),
    ]
    new_posts, updated = filter_new(posts, existing)
    assert [p.id for p in new_posts] == ["2"]
    assert updated == {"1", "2"}

    append_posts_jsonl(posts_file, new_posts)
    lines = posts_file.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    assert '"id": "2"' in lines[0]
