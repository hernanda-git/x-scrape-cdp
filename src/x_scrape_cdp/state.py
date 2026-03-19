from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from .config import Settings


def _canonical_config_payload(raw: dict[str, Any]) -> str:
    return yaml.dump(raw, sort_keys=True, allow_unicode=True)


def compute_config_fingerprint(settings: Settings) -> str:
    """Stable hash when config file path or effective YAML content changes."""
    payload = f"{settings.config_path.resolve()}\n{_canonical_config_payload(settings.raw)}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def load_scrape_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError):
        return {}


def save_scrape_state(
    path: Path,
    *,
    config_fingerprint: str,
    session_handle: str | None,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "config_fingerprint": config_fingerprint,
        "session_handle": session_handle,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    temp = path.with_suffix(path.suffix + ".tmp")
    with temp.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=True, indent=2)
    temp.replace(path)


def should_reset_listener_data(
    stored: dict[str, Any],
    config_fingerprint: str,
    session_handle: str | None,
) -> bool:
    """
    Reset when config identity changes, or when logged-in X account changes.
    First run (no stored fingerprint): do not wipe existing files.
    """
    prev_cfg = stored.get("config_fingerprint")
    if not prev_cfg:
        return False
    if prev_cfg != config_fingerprint:
        return True
    prev_sess = stored.get("session_handle")
    if session_handle and prev_sess and prev_sess != session_handle:
        return True
    return False
