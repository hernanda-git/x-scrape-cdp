from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from typing import Any, Iterable

from rich.console import Console
from rich.live import Live
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


def get_console() -> Console:
    return _console


def _preview_text(text: str, max_len: int = 70) -> str:
    one_line = " ".join((text or "").split())
    if len(one_line) <= max_len:
        return one_line
    return one_line[: max_len - 1] + "…"


def _fmt_int(v: Any) -> str:
    if v is None:
        return "[dim]—[/]"
    if isinstance(v, (int, float)):
        try:
            return f"{int(v):,}"
        except Exception:
            return str(v)
    return str(v)


def _fmt_dt_short(dt_str: Any) -> str:
    if not dt_str:
        return "[dim]—[/]"
    s = str(dt_str).strip()
    # Common forms: ISO with timezone, or RFC-ish strings.
    try:
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        dt = dt.astimezone(timezone.utc)
        return dt.strftime("%H:%M:%S")
    except Exception:
        # Fallback: try to extract HH:MM:SS fragment.
        if "T" in s and len(s) >= 19:
            return s[11:19]
        return s[:19]


def render_recent_posts_table(
    recent_posts: Iterable[dict[str, Any]], *, max_items: int = 10
) -> Table:
    posts = list(recent_posts)[-max_items:]
    # Show newest first.
    posts = list(reversed(posts))

    table = Table(
        show_header=True,
        header_style="bold cyan",
        box=None,
        padding=(0, 1),
        expand=True,
    )
    table.add_column("Kind", style="key", no_wrap=True, width=12)
    table.add_column("ID", style="id", no_wrap=True, width=16)
    table.add_column("Handle", style="target", no_wrap=True, width=12)
    table.add_column("Published", style="dim", no_wrap=True, width=10)
    table.add_column("Engagement", style="val", no_wrap=False, width=34)
    table.add_column("Text", style="val", no_wrap=False, max_width=44)

    def _eng_line(d: dict[str, Any]) -> str:
        # Keep a compact, predictable ordering.
        replies = d.get("replies")
        retweets = d.get("retweets")
        likes = d.get("likes")
        views = d.get("views")
        bookmarks = d.get("bookmarks")
        return (
            f"R:{_fmt_int(replies)} "
            f"RT:{_fmt_int(retweets)} "
            f"L:{_fmt_int(likes)} "
            f"V:{_fmt_int(views)} "
            f"B:{_fmt_int(bookmarks)}"
        )

    for d in posts:
        kind = d.get("kind") or "—"
        pid = d.get("id") or "—"
        handle = d.get("handle") or "—"
        published_at = d.get("published_at")
        table.add_row(
            str(kind),
            str(pid),
            str(handle),
            _fmt_dt_short(published_at),
            _eng_line(d),
            _preview_text(d.get("text") or "", max_len=70),
        )
    return table


def render_recent_posts_panel(
    *,
    targets: list[str],
    recent_posts: Iterable[dict[str, Any]],
    cycle: int,
    new_posts_this_cycle: int,
    next_sleep_seconds: float,
    clamped: bool,
    rate_floor_seconds: float,
    cap_per_minute: int,
) -> Panel:
    t = ", ".join(targets)
    subtitle = (
        f"targets=[{t}] | cycle={cycle} | new={new_posts_this_cycle} | next="
        f"{next_sleep_seconds:.1f}s"
    )
    if clamped:
        subtitle += f" (clamped: floor={rate_floor_seconds:.1f}s cap={cap_per_minute}/min)"

    return Panel(
        render_recent_posts_table(recent_posts),
        title=Text.assemble(
            (" last fetched posts (", "title"), (f"{10}", "count"), (")", "title")
        ),
        subtitle=subtitle,
        border_style="bright_cyan",
        padding=(0, 1),
    )


def create_live_dashboard(initial_renderable: Panel | Table) -> Live:
    """
    Minimal Rich Live wrapper for in-place updates.
    Caller should create/own the Live context.
    """
    return Live(initial_renderable, console=_console, auto_refresh=True, refresh_per_second=4)


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
