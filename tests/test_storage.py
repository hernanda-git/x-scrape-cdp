from __future__ import annotations

from x_scrape_cdp.extract import Post
from x_scrape_cdp.storage import append_posts_jsonl, filter_new, load_seen, save_seen_atomic


def test_seen_roundtrip(tmp_data_dir):
    seen_file = tmp_data_dir / "seen_ids.json"
    save_seen_atomic(seen_file, {"1", "2", "3"})
    loaded = load_seen(seen_file)
    assert loaded == {"1", "2", "3"}


def test_filter_and_append(tmp_data_dir):
    posts_file = tmp_data_dir / "posts.jsonl"
    existing = {"1"}
    posts = [
        Post(id="1", text="old", timestamp=None, url="u1", media_urls=[], scraped_at="t"),
        Post(id="2", text="new", timestamp=None, url="u2", media_urls=[], scraped_at="t"),
    ]
    new_posts, updated = filter_new(posts, existing)
    assert [p.id for p in new_posts] == ["2"]
    assert updated == {"1", "2"}

    append_posts_jsonl(posts_file, new_posts)
    lines = posts_file.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    assert '"id": "2"' in lines[0]
