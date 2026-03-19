from __future__ import annotations

from pathlib import Path

from x_scrape_cdp.config import Settings


def test_default_max_refreshes_per_minute():
    s = Settings(raw={"schedule": {}}, config_path=Path("c.yaml"))
    assert s.max_refreshes_per_minute == 15
    assert s.min_seconds_between_cycles == 60.0 / 15


def test_rate_cap_disabled():
    s = Settings(raw={"schedule": {"max_refreshes_per_minute": 0}}, config_path=Path("c.yaml"))
    assert s.min_seconds_between_cycles == 0.0
