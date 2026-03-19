from __future__ import annotations

import asyncio
import logging
import random
from contextlib import suppress

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
from .storage import append_posts_jsonl, load_seen, reset_listener_data_files, save_seen_atomic

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


async def run_once(settings: Settings) -> int:
    config_fingerprint = compute_config_fingerprint(settings)
    stored_state = load_scrape_state(settings.scrape_state_file)

    conn = await connect_playwright(settings.cdp_http_url)
    new_total = 0
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
                        logger.info(
                            "event=new_post target=%s id=%s kind=%s url=%s text=%s",
                            target,
                            p.id,
                            d.get("classification", {}).get("kind"),
                            p.url,
                            _preview_text(d.get("content", {}).get("text") or ""),
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
                    logger.info("event=no_new_posts target=%s", target)
            except Exception as exc:
                logger.exception("event=target_error target=%s error=%s", target, exc)

        save_scrape_state(
            settings.scrape_state_file,
            config_fingerprint=config_fingerprint,
            session_handle=session_handle,
        )
        return new_total
    finally:
        with suppress(Exception):
            await conn.close()


async def run_listener(settings: Settings) -> None:
    logger.info("event=listener_start targets=%s", ",".join(settings.targets))
    while True:
        try:
            await run_once(settings)
        except Exception as exc:
            logger.exception("event=loop_error error=%s", exc)
        sleep_seconds, rate_floor, clamped = _sleep_between_cycles_seconds(settings)
        if clamped:
            logger.info(
                "event=sleep seconds=%.2f cap=max_%s_per_min floor=%.2f",
                sleep_seconds,
                settings.max_refreshes_per_minute,
                rate_floor,
            )
        else:
            logger.info("event=sleep seconds=%.2f", sleep_seconds)
        await asyncio.sleep(sleep_seconds)
