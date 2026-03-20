from __future__ import annotations

from pathlib import Path

from x_scrape_cdp.config import load_settings


def test_load_settings_defaults():
    settings = load_settings("config/default.yaml")
    assert settings.cdp_http_url.startswith("http://")
    assert isinstance(settings.targets, list)
    assert settings.posts_file == Path("data/posts.jsonl")


def test_session_cookie_file_env_overrides_yaml(monkeypatch):
    monkeypatch.setenv("COOKIE_FILE", "/tmp/x_cookies.txt")
    settings = load_settings("config/default.yaml")
    assert settings.session_cookie_file == "/tmp/x_cookies.txt"


def test_session_cookie_file_whitespace_env_falls_back_to_yaml(monkeypatch):
    monkeypatch.setenv("COOKIE_FILE", "   ")
    settings = load_settings("config/default.yaml")
    assert settings.session_cookie_file is None
