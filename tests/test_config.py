from __future__ import annotations

from pathlib import Path

from x_scrape_cdp.config import load_settings


def test_load_settings_defaults():
    settings = load_settings("config/default.yaml")
    assert settings.cdp_http_url.startswith("http://")
    assert isinstance(settings.targets, list)
    assert settings.posts_file == Path("data/posts.jsonl")
