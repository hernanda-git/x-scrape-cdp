from __future__ import annotations

import asyncio
import logging
import random
from collections import deque
from contextlib import suppress

from . import rich_log
from .cdp import connect_playwright, load_cookies_if_configured
from .config import Settings
from .extract import get_extractor
from .navigation import gentle_scroll_for_fresh_posts, human_warmup, open_profile
from .notify import post_webhook
from .session import get_logged_in_profile_handle, is_logged_in
from .state import (
    compute_config_fingerprint,
    load_scrape_state,
    save_scrape_state,
    should_reset_listener_data,
)
from .stealth import StealthProfile, apply_stealth
from .storage import (
    append_posts_jsonl,
    load_recent_posts_jsonl,
    load_seen,
    reset_listener_data_files,
    save_seen_atomic,
)

logger = logging.getLogger("x_scrape_cdp.loop")


def _sleep_between_cycles_seconds(settings: Settings) -> tuple[float, float, bool]:
    """
    Random sleep from config, floored by max_refreshes_per_minute safety cap.
    Returns (sleep_seconds, floor_seconds_or_zero, was_clamped).
    """
    low = float(settings.interval_seconds_min)
    high = float(settings.interval_seconds_max)
    if high < low:
        low, high = high, low
    sampled = random.uniform(low, high)
    floor = settings.min_seconds_between_cycles
    if floor <= 0 or sampled >= floor:
        return sampled, floor, False
    return floor, floor, True


def _preview_text(text: str, max_len: int = 100) -> str:
    one_line = " ".join((text or "").split())
    if len(one_line) <= max_len:
        return one_line
    return one_line[: max_len - 1] + "…"


async def validate_session(settings: Settings) -> bool:
    conn = await connect_playwright(settings.cdp_http_url)
    try:
        await load_cookies_if_configured(conn.context, settings.session_cookie_file)
        await conn.page.goto("https://x.com/home", wait_until=settings.wait_until)
        return await is_logged_in(conn.page)
    finally:
        with suppress(Exception):
            await conn.close()


async def run_once(settings: Settings) -> tuple[int, list[dict[str, object]]]:
    config_fingerprint = compute_config_fingerprint(settings)
    stored_state = load_scrape_state(settings.scrape_state_file)

    conn = await connect_playwright(settings.cdp_http_url)
    new_total = 0
    new_posts_flat: list[dict[str, object]] = []
    session_handle: str | None = None

    try:
        await load_cookies_if_configured(conn.context, settings.session_cookie_file)
        await apply_stealth(
            conn.page,
            StealthProfile(
                viewport_width=settings.viewport_width,
                viewport_height=settings.viewport_height,
                user_agent=settings.stealth_user_agent,
                jitter_percent=settings.jitter_percent,
            ),
        )

        await conn.page.goto("https://x.com/home", wait_until=settings.wait_until)
        if settings.session_validate_on_startup and not await is_logged_in(conn.page):
            raise RuntimeError("Session invalid. Re-login using the configured user-data-dir.")

        session_handle = await get_logged_in_profile_handle(conn.page)

        if settings.reset_data_on_config_or_session_change and should_reset_listener_data(
            stored_state,
            config_fingerprint,
            session_handle,
        ):
            reset_listener_data_files(settings.posts_file, settings.seen_ids_file)
            logger.info("event=data_reset reason=config_or_session_change")

        seen = load_seen(settings.seen_ids_file)

        for target in settings.targets:
            extractor = get_extractor(settings, listened_target=target)
            try:
                await open_profile(
                    conn.page,
                    target,
                    replies=settings.include_replies,
                    wait_until=settings.wait_until,
                )
                await conn.page.wait_for_selector(
                    '[data-testid="tweet"]', timeout=settings.tweet_timeout_ms
                )
                await human_warmup(conn.page)
                await gentle_scroll_for_fresh_posts(
                    conn.page,
                    settings.scroll_rounds,
                    (settings.pause_seconds_min, settings.pause_seconds_max),
                )

                posts = await extractor(conn.page)
                fresh = [p for p in posts if p.id not in seen]
                if fresh:
                    seen.update(p.id for p in fresh)
                    append_posts_jsonl(settings.posts_file, fresh)
                    save_seen_atomic(settings.seen_ids_file, seen)
                    new_total += len(fresh)
                    logger.info("event=new_posts target=%s count=%s", target, len(fresh))
                    for p in fresh:
                        d = p.to_dict()
                        new_posts_flat.append(d)
                        logger.info(
                            "event=new_post target=%s id=%s kind=%s url=%s text=%s",
                            target,
                            p.id,
                            d.get("kind"),
                            p.url,
                            _preview_text(d.get("text") or ""),
                        )
                    if settings.webhook_enabled and settings.webhook_url:
                        await post_webhook(
                            settings.webhook_url,
                            {
                                "target": target,
                                "count": len(fresh),
                                "posts": [p.to_dict() for p in fresh],
                            },
                        )
                else:
                    # In live TTY mode, the dashboard is the UX; avoid per-cycle
                    # "no new posts" spam.
                    if not rich_log.use_rich_stdout():
                        logger.info("event=no_new_posts target=%s", target)
                    else:
                        logger.debug("event=no_new_posts target=%s", target)
            except Exception as exc:
                logger.exception("event=target_error target=%s error=%s", target, exc)

        save_scrape_state(
            settings.scrape_state_file,
            config_fingerprint=config_fingerprint,
            session_handle=session_handle,
        )
        return new_total, new_posts_flat
    finally:
        with suppress(Exception):
            await conn.close()


async def run_listener(settings: Settings) -> None:
    targets = settings.targets
    rich_tty = rich_log.use_rich_stdout()
    logger.info(
        "event=listener_start targets=%s schedule=random_%s_%s_s rate_floor=%.2fs "
        "(max_%s/min caps minimum sleep only)",
        ",".join(targets),
        settings.interval_seconds_min,
        settings.interval_seconds_max,
        settings.min_seconds_between_cycles,
        settings.max_refreshes_per_minute,
    )
    if rich_tty:
        rich_log.print_listener_start(targets)

    recent_posts: deque[dict[str, object]] = deque(maxlen=10)
    cycle = 0

    def _render_dashboard(
        new_total: int, sleep_seconds: float, rate_floor: float, clamped: bool
    ):
        # Rich Live uses a single renderable; keep it purely based on current state.
        return rich_log.render_recent_posts_panel(
            targets=targets,
            recent_posts=recent_posts,
            cycle=cycle,
            new_posts_this_cycle=new_total,
            next_sleep_seconds=sleep_seconds,
            clamped=clamped,
            rate_floor_seconds=rate_floor,
            cap_per_minute=settings.max_refreshes_per_minute,
        )

    if rich_tty:
        # Preload last records from disk so the table is never empty.
        try:
            for d in load_recent_posts_jsonl(settings.posts_file, limit=10):
                recent_posts.append(d)
        except Exception as exc:
            logger.debug("event=dashboard_preload_failed error=%s", exc)

        initial = rich_log.render_recent_posts_panel(
            targets=targets,
            recent_posts=recent_posts,
            cycle=0,
            new_posts_this_cycle=0,
            next_sleep_seconds=0.0,
            clamped=False,
            rate_floor_seconds=0.0,
            cap_per_minute=settings.max_refreshes_per_minute,
        )

        with rich_log.create_live_dashboard(initial) as live:
            while True:
                cycle += 1
                new_total = 0
                new_posts: list[dict[str, object]] = []
                try:
                    new_total, new_posts = await run_once(settings)
                except Exception as exc:
                    logger.exception("event=loop_error error=%s", exc)

                # Update rolling window (newest at the end, reversed in renderer).
                for d in new_posts:
                    recent_posts.append(d)

                sleep_seconds, rate_floor, clamped = _sleep_between_cycles_seconds(settings)
                # In live (TTY) mode, avoid printing per-cycle sleep lines.
                # The dashboard subtitle already provides cycle timing UX.
                if not rich_tty:
                    if clamped:
                        logger.info(
                            "event=sleep seconds=%.2f cap=max_%s_per_min floor=%.2f",
                            sleep_seconds,
                            settings.max_refreshes_per_minute,
                            rate_floor,
                        )
                    else:
                        logger.info("event=sleep seconds=%.2f", sleep_seconds)

                # Single table refresh (no new lines per interval).
                live.update(_render_dashboard(new_total, sleep_seconds, rate_floor, clamped))

                await asyncio.sleep(sleep_seconds)
    else:
        while True:
            try:
                await run_once(settings)
            except Exception as exc:
                logger.exception("event=loop_error error=%s", exc)
            sleep_seconds, _, _ = _sleep_between_cycles_seconds(settings)
            logger.info("event=sleep seconds=%.2f", sleep_seconds)
            await asyncio.sleep(sleep_seconds)
