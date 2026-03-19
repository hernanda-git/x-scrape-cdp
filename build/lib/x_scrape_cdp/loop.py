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
from .session import is_logged_in
from .stealth import StealthProfile, apply_stealth
from .storage import append_posts_jsonl, load_seen, save_seen_atomic

logger = logging.getLogger("x_scrape_cdp.loop")


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
    seen = load_seen(settings.seen_ids_file)
    extractor = get_extractor(settings)
    new_total = 0

    conn = await connect_playwright(settings.cdp_http_url)
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

        for target in settings.targets:
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
        sleep_seconds = random.uniform(settings.interval_seconds_min, settings.interval_seconds_max)
        logger.info("event=sleep seconds=%.2f", sleep_seconds)
        await asyncio.sleep(sleep_seconds)
