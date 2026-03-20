from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Iterable

from .extract import Post


def ensure_data_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def load_seen(path: Path) -> set[str]:
    if not path.exists():
        return set()
    with path.open("r", encoding="utf-8") as f:
        payload = json.load(f)
    if isinstance(payload, dict):
        values = payload.get("ids", [])
    else:
        values = payload
    if not isinstance(values, list):
        return set()
    return {str(v) for v in values}


def save_seen_atomic(path: Path, ids: Iterable[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(path.suffix + ".tmp")
    payload = {"ids": sorted({str(v) for v in ids})}
    with temp_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=True, indent=2)
    temp_path.replace(path)


def filter_new(posts: list[Post], seen: set[str]) -> tuple[list[Post], set[str]]:
    new_posts = [p for p in posts if p.id not in seen]
    new_ids = {p.id for p in new_posts}
    return new_posts, seen.union(new_ids)


def append_posts_jsonl(path: Path, posts: list[Post]) -> None:
    if not posts:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        for post in posts:
            f.write(json.dumps(post.to_dict(), ensure_ascii=True) + "\n")


def truncate_file(path: Path) -> None:
    """Empty a file (create parent dirs). Used when resetting listener data."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("", encoding="utf-8")


def reset_listener_data_files(posts_file: Path, seen_ids_file: Path) -> None:
    truncate_file(posts_file)
    save_seen_atomic(seen_ids_file, set())


def load_recent_posts_jsonl(path: Path, *, limit: int = 10) -> list[dict[str, Any]]:
    """
    Tail a JSONL file and parse the last `limit` JSON objects.
    Designed to avoid loading the whole file in memory for large scrape runs.
    """
    if limit <= 0 or not path.exists():
        return []

    size = path.stat().st_size
    if size == 0:
        return []

    # Read backwards in chunks until we likely have enough newlines.
    # Then parse only the last `limit` complete lines.
    with path.open("rb") as f:
        f.seek(0, os.SEEK_END)
        end = f.tell()
        chunk_size = 8192
        data = b""
        newline_count = 0
        while end > 0 and newline_count < (limit + 2):
            read_size = min(chunk_size, end)
            end -= read_size
            f.seek(end)
            data = f.read(read_size) + data
            newline_count = data.count(b"\n")

    lines = [ln for ln in data.split(b"\n") if ln.strip()]
    raw_lines = lines[-limit:]

    out: list[dict[str, Any]] = []
    for ln in raw_lines:
        try:
            obj = json.loads(ln.decode("utf-8", errors="replace"))
            if isinstance(obj, dict):
                out.append(obj)
        except Exception:
            continue
    return out
