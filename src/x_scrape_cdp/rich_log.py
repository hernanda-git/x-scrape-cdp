from __future__ import annotations

import json
import sys
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from rich.text import Text
from rich.theme import Theme

LISTENER_THEME = Theme(
    {
        "title": "bold bright_cyan",
        "target": "bold bright_magenta",
        "key": "cyan",
        "val": "bright_white",
        "accent": "bold bright_green",
        "sleep": "bold bright_yellow",
        "count": "bold bright_green",
        "warn": "bold bright_red",
        "id": "bold bright_blue",
        "border_hi": "bright_magenta",
    }
)

_console = Console(theme=LISTENER_THEME, stderr=False)


def use_rich_stdout() -> bool:
    return sys.stdout.isatty()


def print_listener_start(targets: list[str]) -> None:
    if not use_rich_stdout():
        return
    t = ", ".join(targets)
    _console.print()
    _console.print(
        Panel.fit(
            Text.assemble(("● ", "accent"), ("listener ", "title"), ("active", "bold")),
            subtitle=f"[target]{t}[/]",
            border_style="bright_cyan",
        )
    )


def print_new_posts_summary(target: str, count: int) -> None:
    if not use_rich_stdout():
        return
    _console.print(
        Text.assemble(
            ("  ↳ ", "accent"),
            ("new posts: ", "key"),
            (str(count), "count"),
            ("  @", "dim"),
            (target, "target"),
        )
    )


def print_new_post_detail(flat: dict[str, Any]) -> None:
    """Pretty table of all JSONL-relevant fields (and extras)."""
    if not use_rich_stdout():
        return
    table = Table(show_header=False, box=None, padding=(0, 1), title="[title]new post[/]")
    table.add_column("key", style="key", justify="right", no_wrap=True)
    table.add_column("value", style="val")

    order = [
        "schema_version",
        "id",
        "handle",
        "kind",
        "text",
        "published_at",
        "replies",
        "retweets",
        "likes",
        "views",
        "bookmarks",
        "quoted_tweet",
        "media",
        "url",
        "listened_target",
        "scraped_at",
        "social_context",
    ]
    for k in order:
        if k not in flat:
            continue
        v = flat[k]
        if v is None:
            s = "[dim]—[/]"
        elif k in ("quoted_tweet",) and isinstance(v, dict):
            s = json.dumps(v, ensure_ascii=True)[:500]
            if len(json.dumps(v, ensure_ascii=True)) > 500:
                s += "…"
        elif k == "media" and isinstance(v, list):
            s = json.dumps(v, ensure_ascii=True)
        elif k == "text" and isinstance(v, str) and len(v) > 200:
            s = v[:200] + "…"
        else:
            s = str(v)
        table.add_row(k, s)

    _console.print(
        Panel(
            table,
            title="[accent]◆[/] [title]new post[/] [dim]captured[/]",
            border_style="bright_green",
            padding=(0, 2),
        )
    )


def print_sleep(seconds: float, *, clamped: bool, cap: int, floor: float) -> None:
    if not use_rich_stdout():
        return
    msg = Text.assemble(
        ("  ⏱ ", "sleep"),
        ("next cycle in ", "key"),
        (f"{seconds:.1f}s", "bold sleep"),
    )
    if clamped:
        msg.append(f"  (rate floor {floor:.1f}s · max {cap}/min)", style="dim")
    _console.print(msg)
    _console.print(Rule(style="dim cyan"))
    _console.print()


def print_plain_fallback(message: str) -> None:
    """When not a TTY, caller should use logging; this is a no-op."""
    return
