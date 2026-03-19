# Risks and Compliance Notes

## Purpose

This project listens for new posts on X profile timelines through a real Chrome session connected over CDP. It is intended for low-volume monitoring and research workflows.

## Legal and Policy Risk

- X terms may restrict scraping and automation.
- Account suspension, rate limiting, and IP blocking are possible.
- Do not use this project to bypass access controls, harvest private data, or run high-volume collection.

## Operational Risk

- UI changes can break selectors.
- Session expiry (logout, cookie invalidation, 2FA challenges) can stop collection.
- Aggressive polling can trigger anti-bot checks.

## Safety Limits

- Track only public profiles you are authorized to monitor.
- Use randomized interval windows and conservative scrolling.
- Keep credentials out of source control and logs.

## Data Handling

- Persist only the fields required for downstream processing.
- Review retention policy periodically and delete stale data.
- Treat collected output as potentially sensitive and store securely.
