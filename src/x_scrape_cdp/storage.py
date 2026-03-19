from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

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
