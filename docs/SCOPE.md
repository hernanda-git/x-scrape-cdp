# Project Scope

## In Scope

- Poll one or more public X profile timelines at a controlled interval.
- Detect new posts by stable tweet ID extraction.
- Append new records to JSONL and maintain local seen-ID state.
- Optionally send lightweight webhooks for new posts.

## Out of Scope

- Private account access or unauthorized data collection.
- High-volume scraping, historical backfill at scale, or data resale.
- Circumventing platform security controls.
- Production-grade cloud orchestration beyond documented multi-instance templates.

## Operational Limits

- Start with one account and one browser profile.
- Default poll range should stay conservative (for example 4-10 minutes).
- Scroll rounds should remain low and capped.

## Data Retention

- Keep only required fields (id, url, timestamp, text, metadata).
- Store local files under `data/`.
- Define retention and backup procedures before long-term operation.
