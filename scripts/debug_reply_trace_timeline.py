from __future__ import annotations

import asyncio
import json
import logging

from playwright.async_api import Page

from x_scrape_cdp.cdp import connect_playwright
from x_scrape_cdp.config import load_settings
from x_scrape_cdp.extract import TWEET_ARTICLE_EXTRACT_JS
from x_scrape_cdp.navigation import gentle_scroll_for_fresh_posts, human_warmup, open_profile
from x_scrape_cdp.stealth import StealthProfile, apply_stealth


async def _timeline_debug_for_ids(page: Page, *, target_ids: list[str], label: str) -> None:
    nodes = page.locator('[data-testid="tweet"]')
    count = await nodes.count()
    if count == 0:
        print(f"[{label}] no [data-testid='tweet'] on page")
        return

    # Find candidate tweet nodes that contain any of the target ids in any /status/<id> link.
    # (Time-based canonical-id heuristics can fail depending on DOM/layout state.)
    indices_and_ids: list[dict] = await page.evaluate(
        """
        (targetIds) => {
          const els = Array.from(document.querySelectorAll('[data-testid="tweet"]'));

          const statusIdFromHref = (h) => {
            if (!h) return null;
            const m = String(h).match(/\\/status\\/(\\d+)/);
            return m ? m[1] : null;
          };

          const out = [];
          for (let i = 0; i < els.length; i++) {
            const el = els[i];
            const quoteRoot = el.querySelector('[data-testid="quoteTweet"]');
            const links = Array.from(el.querySelectorAll('a[href*="/status/"]'))
              .map(a => a.getAttribute('href'))
              .filter(Boolean);
            const ids = links
              .map(h => statusIdFromHref(h))
              .filter(Boolean)
              .filter(sid => targetIds.includes(sid));
            // de-dup
            const uniq = Array.from(new Set(ids));
            if (uniq.length) out.push({ index: i, ids: uniq });
          }
          return out;
        }
        """,
        target_ids,
    )
    indices = [x["index"] for x in indices_and_ids]

    if not indices:
        # Print sample ids from whatever is currently loaded.
        currentIdsSample = await page.evaluate(
            """
            () => {
              const els = Array.from(document.querySelectorAll('[data-testid="tweet"]'));
              const statusIdFromHref = (h) => {
                if (!h) return null;
                const m = String(h).match(/\\/status\\/(\\d+)/);
                return m ? m[1] : null;
              };
              const out = [];
              for (let i = 0; i < Math.min(20, els.length); i++) {
                const el = els[i];
                const links = Array.from(el.querySelectorAll('a[href*="/status/"]'))
                  .map(a => a.getAttribute('href'))
                  .filter(Boolean);
                const ids = links
                  .map(h => statusIdFromHref(h))
                  .filter(Boolean);
                if (ids.length) out.push(ids[0]);
              }
              return out;
            }
            """,
        )
        print(f"[{label}] target ids not found among current DOM tweets. tweet_count={count} sample_ids={currentIdsSample}")
        return

    print(f"[{label}] found candidate tweet nodes indices={indices} tweet_count={count}")

    # Extract full debug on those exact nodes.
    for i in indices:
        handle = await nodes.nth(i).element_handle()
        if not handle:
            continue
        try:
            extracted = await page.evaluate(TWEET_ARTICLE_EXTRACT_JS, handle)
            dom_debug = await page.evaluate(
                """
                (el) => {
                  const q = (root, sel) => root.querySelector(sel);
                  const qa = (root, sel) => Array.from(root.querySelectorAll(sel));

                  const quoteRoot = q(el, '[data-testid="quoteTweet"]');
                  const socialEl = q(el, '[data-testid="socialContext"]');
                  const socialText = socialEl ? (socialEl.textContent || '').trim() : null;

                  const statusHrefsInRow = qa(el, 'a[href*="/status/"]').map(a => a.getAttribute('href')).filter(Boolean);
                  const statusHrefsInSocial = socialEl ? qa(socialEl, 'a[href*="/status/"]').map(a => a.getAttribute('href')).filter(Boolean) : [];

                  const times = qa(el, 'time').map(t => {
                    if (quoteRoot && quoteRoot.contains(t)) return null;
                    const parentA = t.closest('a');
                    const href = parentA ? parentA.getAttribute('href') : null;
                    const sid = href ? String(href).match(/\\/status\\/(\\d+)/)?.[1] ?? null : null;
                    return { datetime: t.getAttribute('datetime'), href, sid };
                  }).filter(Boolean);

                  return { socialText, statusHrefsInRow, statusHrefsInSocial, timeAnchors: times };
                }
                """,
                handle,
            )

            print("\n---")
            print(f"[{label}] node_index={i}")
            print("extracted:", json.dumps(extracted, ensure_ascii=False))
            print("dom_debug:", json.dumps(dom_debug, ensure_ascii=False))
        finally:
            await handle.dispose()


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    settings = load_settings("config/test_0xvalarion.yaml")
    conn = await connect_playwright(settings.cdp_http_url)

    try:
        target_ids = ["2034767814800941353", "2034770435108479460"]
        target = settings.targets[0]

        await apply_stealth(
            conn.page,
            StealthProfile(
                viewport_width=settings.viewport_width,
                viewport_height=settings.viewport_height,
                user_agent=settings.stealth_user_agent,
                jitter_percent=settings.jitter_percent,
            ),
        )

        # For debugging reply-parent extraction we want replies included.
        await open_profile(
            conn.page,
            target,
            replies=True,
            wait_until=settings.wait_until,
        )

        await human_warmup(conn.page)

        # Use extra scroll rounds so the tweet IDs are likely present.
        # Scroll further down than the normal presets.
        for _ in range(22):
            await conn.page.mouse.wheel(0, 1800)
            await asyncio.sleep(0.9)
        await _timeline_debug_for_ids(conn.page, target_ids=target_ids, label="reply_trace")
    except Exception:
        # If navigation/stealth fails, still attempt extraction with whatever DOM exists.
        await asyncio.sleep(3)
        await _timeline_debug_for_ids(
            conn.page,
            target_ids=["2034767814800941353", "2034770435108479460"],
            label="reply_trace",
        )
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())

