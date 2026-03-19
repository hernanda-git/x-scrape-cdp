from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass
class Settings:
    raw: dict[str, Any]
    config_path: Path

    @property
    def cdp_http_url(self) -> str:
        env_url = os.getenv("CDP_URL")
        if env_url:
            return env_url
        return str(self.raw.get("cdp", {}).get("http_url", "http://127.0.0.1:9222"))

    @property
    def session_cookie_file(self) -> str | None:
        return self.raw.get("session", {}).get("cookie_file")

    @property
    def session_validate_on_startup(self) -> bool:
        return bool(self.raw.get("session", {}).get("validate_on_startup", True))

    @property
    def targets(self) -> list[str]:
        values = self.raw.get("targets", [])
        if not isinstance(values, list):
            return []
        return [str(v).lstrip("@") for v in values if str(v).strip()]

    @property
    def extraction_mode(self) -> str:
        return str(self.raw.get("extraction", {}).get("mode", "playwright"))

    @property
    def extraction_prompt_template(self) -> str | None:
        return self.raw.get("extraction", {}).get("prompt_template")

    @property
    def include_replies(self) -> bool:
        return bool(self.raw.get("navigation", {}).get("include_replies", False))

    @property
    def wait_until(self) -> str:
        return str(self.raw.get("navigation", {}).get("wait_until", "domcontentloaded"))

    @property
    def tweet_timeout_ms(self) -> int:
        return int(self.raw.get("navigation", {}).get("tweet_timeout_ms", 15000))

    @property
    def scroll_rounds(self) -> int:
        rounds = int(self.raw.get("navigation", {}).get("scroll_rounds", 3))
        max_rounds = int(self.raw.get("max_scroll_rounds", rounds))
        return min(rounds, max_rounds)

    @property
    def pause_seconds_min(self) -> float:
        return float(self.raw.get("navigation", {}).get("pause_seconds_min", 2.0))

    @property
    def pause_seconds_max(self) -> float:
        return float(self.raw.get("navigation", {}).get("pause_seconds_max", 4.0))

    @property
    def interval_seconds_min(self) -> int:
        return int(self.raw.get("schedule", {}).get("interval_seconds_min", 240))

    @property
    def interval_seconds_max(self) -> int:
        return int(self.raw.get("schedule", {}).get("interval_seconds_max", 600))

    @property
    def max_refreshes_per_minute(self) -> int:
        """
        Upper bound on poll cycles per minute (sleep between run_once iterations).
        Default 15 => minimum sleep 4s. Set to 0 to disable the safety floor.
        """
        raw = self.raw.get("schedule", {}).get("max_refreshes_per_minute", 15)
        if raw is None:
            return 15
        return int(raw)

    @property
    def min_seconds_between_cycles(self) -> float:
        cap = self.max_refreshes_per_minute
        if cap <= 0:
            return 0.0
        return 60.0 / float(cap)

    @property
    def data_dir(self) -> Path:
        return Path(str(self.raw.get("storage", {}).get("data_dir", "data")))

    @property
    def seen_ids_file(self) -> Path:
        return Path(str(self.raw.get("storage", {}).get("seen_ids_file", "data/seen_ids.json")))

    @property
    def posts_file(self) -> Path:
        return Path(str(self.raw.get("storage", {}).get("posts_file", "data/posts.jsonl")))

    @property
    def scrape_state_file(self) -> Path:
        return Path(str(self.raw.get("storage", {}).get("state_file", "data/scrape_state.json")))

    @property
    def reset_data_on_config_or_session_change(self) -> bool:
        return bool(self.raw.get("storage", {}).get("reset_on_change", True))

    @property
    def webhook_enabled(self) -> bool:
        return bool(self.raw.get("notify", {}).get("enabled", False))

    @property
    def webhook_url(self) -> str | None:
        return self.raw.get("notify", {}).get("webhook_url")

    @property
    def viewport_width(self) -> int:
        return int(self.raw.get("stealth", {}).get("viewport", {}).get("width", 1920))

    @property
    def viewport_height(self) -> int:
        return int(self.raw.get("stealth", {}).get("viewport", {}).get("height", 1080))

    @property
    def stealth_user_agent(self) -> str | None:
        return self.raw.get("stealth", {}).get("user_agent")

    @property
    def jitter_percent(self) -> int:
        return int(self.raw.get("stealth", {}).get("jitter_percent", 10))


def load_settings(config_path: str | None = None) -> Settings:
    resolved = Path(config_path or os.getenv("CONFIG_PATH", "config/default.yaml"))
    if not resolved.exists():
        raise FileNotFoundError(f"Config file not found: {resolved}")

    with resolved.open("r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    if not isinstance(raw, dict):
        raise ValueError("Config root must be a mapping/object.")

    return Settings(raw=raw, config_path=resolved)
