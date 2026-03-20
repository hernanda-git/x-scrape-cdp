from __future__ import annotations

from pathlib import Path

from x_scrape_cdp.cdp import _cookies_from_path_or_inline, _parse_cookie_text


NETSCAPE_SAMPLE = """# Netscape HTTP Cookie File
.x.com\tTRUE\t/\tTRUE\t1789511796\tdnt\t1
"""


def test_parse_netscape_text():
    cookies = _parse_cookie_text(NETSCAPE_SAMPLE, path_suffix=None)
    assert len(cookies) == 1
    assert cookies[0]["name"] == "dnt"
    assert cookies[0]["value"] == "1"
    assert cookies[0]["domain"] == ".x.com"


def test_parse_json_text():
    raw = '[{"name": "a", "value": "b", "domain": ".x.com", "path": "/"}]'
    cookies = _parse_cookie_text(raw, path_suffix=None)
    assert len(cookies) == 1
    assert cookies[0]["name"] == "a"


def test_cookies_from_file_reads_content(tmp_path: Path):
    p = tmp_path / "cookies.txt"
    p.write_text(NETSCAPE_SAMPLE, encoding="utf-8")
    cookies = _cookies_from_path_or_inline(str(p))
    assert len(cookies) == 1
    assert cookies[0]["name"] == "dnt"


def test_cookies_inline_when_not_a_file():
    cookies = _cookies_from_path_or_inline(NETSCAPE_SAMPLE.strip())
    assert len(cookies) == 1
