from __future__ import annotations

import asyncio
import json
import logging

from playwright.async_api import Page

from x_scrape_cdp.cdp import connect_playwright
from x_scrape_cdp.config import load_settings
from x_scrape_cdp.extract import TWEET_ARTICLE_EXTRACT_JS
from x_scrape_cdp.navigation import human_warmup, open_profile


async def _scroll_until_found(page: Page, target_ids: list[str], *, max_steps: int) -> list[str]:
    target_set = set(target_ids)
    found: set[str] = set()

    for step in range(max_steps):
        await page.mouse.wheel(0, 2200)
        await asyncio.sleep(0.9)

        present = await page.evaluate(
            """
            (targetIds) => {
              const targetSet = new Set(targetIds);
              const links = Array.from(document.querySelectorAll('a[href*="/status/"]'));
              const ids = [];
              for (const a of links) {
                const href = a.getAttribute('href');
                if (!href) continue;
                const m = String(href).match(/\\/status\\/(\\d+)/);
                if (m && targetSet.has(m[1])) ids.push(m[1]);
              }
              return Array.from(new Set(ids));
            }
            """,
            target_ids,
        )
        found.update(present)
        print(f"[search] step={step+1}/{max_steps} present={sorted(present)} found_total={sorted(found)}")
        if found == target_set:
            break

    return sorted(found)


async def _extract_matching_nodes(page: Page, target_ids: list[str], label: str) -> None:
    nodes = page.locator('[data-testid="tweet"]')
    count = await nodes.count()

    indices_and_hits: list[dict] = await page.evaluate(
        """
        (targetIds) => {
          const targetSet = new Set(targetIds);
          const els = Array.from(document.querySelectorAll('[data-testid="tweet"]'));
          const statusIdFromHref = (h) => {
            if (!h) return null;
            const m = String(h).match(/\\/status\\/(\\d+)/);
            return m ? m[1] : null;
          };
          const out = [];
          for (let i = 0; i < els.length; i++) {
            const el = els[i];
            const links = Array.from(el.querySelectorAll('a[href*="/status/"]'));
            const ids = [];
            for (const a of links) {
              const href = a.getAttribute('href');
              const sid = statusIdFromHref(href);
              if (sid && targetSet.has(sid)) ids.push(sid);
            }
            const uniq = Array.from(new Set(ids));
            if (uniq.length) out.push({ index: i, ids: uniq });
          }
          return out;
        }
        """,
        target_ids,
    )

    print(f"[{label}] tweet_count={count} matching_nodes={indices_and_hits}")

    for hit in indices_and_hits:
        i = hit["index"]
        ids = hit["ids"]
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
            print(f"[{label}] node_index={i} ids={ids}")
            print("extracted:", json.dumps(extracted, ensure_ascii=False))
            print("dom_debug:", json.dumps(dom_debug, ensure_ascii=False))
        finally:
            await handle.dispose()


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    settings = load_settings("config/test_0xvalarion.yaml")
    conn = await connect_playwright(settings.cdp_http_url)
    try:
        target = settings.targets[0]
        target_ids = ["2034767814800941353", "2034770435108479460"]

        # Open with replies so reply-posts are present in timeline.
        await open_profile(page=conn.page, username=target, replies=True, wait_until=settings.wait_until)
        await human_warmup(conn.page)

        found = await _scroll_until_found(conn.page, target_ids, max_steps=80)
        print(f"[search] done found={found}")

        if found:
            await _extract_matching_nodes(conn.page, target_ids, label="reply_trace")
        else:
            print("[reply_trace] Neither target id appeared in DOM within scroll limit.")
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())

