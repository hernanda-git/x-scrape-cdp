# Phase 0 — Context, strategy, and risks

## Purpose

Set expectations for the X (x.com) account post listener: what it does, why CDP + real Chrome is used in 2026, and what can go wrong legally and operationally.

## Strategy summary

Real-time polling of a profile timeline: every 3–10 minutes (randomized), load the profile in a fully authenticated real Chrome instance via CDP, mimic human behavior, extract latest posts with stable `data-testid` selectors, detect new tweets by ID, then store or log them.

## Why this approach (2026)

X has intensified bot detection (TLS fingerprinting, behavioral analysis, Cloudflare tooling, guest-token binding, IP reputation, AI-bot crackdowns). Pure API/GraphQL scrapers break often. Full-browser CDP + real cookies/session + stealth + human simulation remains one of the more resilient DIY options. `connect_over_cdp` gives deep control without launching a new browser every run.

## Critical warnings

| Area | Notes |
|------|--------|
| **TOS & legal** | X prohibits scraping in its ToS. Risk of suspension, shadow-bans, IP blocks. Public posts may be acceptable for personal/research use; avoid commercial resale or high volume without permission. Bypassing technical measures at scale can be legally gray (e.g. US CFAA). Use at your own risk. |
| **Detection** | Even with mitigations, X can flag mouse patterns, scroll velocity, or session anomalies. Success drops without residential proxies. Start small: one account, ~5-minute intervals. |
| **Reliability** | Cookie export is portable; `user-data-dir` is simpler but large (~100–500 MB). |
| **Edge cases** | UI changes (verify selectors periodically), 2FA/login walls, rate limits after many scrolls, lazy-loaded media, threads/replies, promoted tweets. |
| **Ethics** | Monitor public accounts only; minimize sensitive media retention. |
| **Cost** | Free for 1–3 instances; residential proxies and 24/7 VPS add cost. |

## Dependencies

- None (read first before any implementation phase).

## Outputs

- Shared understanding and risk acceptance; no code artifacts.

## Next phase

→ [Phase 1 — Preparation](./phase-01-preparation.md)
