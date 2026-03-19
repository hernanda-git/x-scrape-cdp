# ADR-001: Session Strategy

## Status

Accepted

## Decision

Use a persistent Chrome `user-data-dir` as the primary session strategy for the MVP.

## Context

The listener depends on a real authenticated browser session. While cookie export/import is possible, it is fragile and can drift from browser state.

## Consequences

- Simpler operator workflow: log in once in the same profile.
- Better compatibility with modern anti-bot/session checks.
- Larger local profile directory and machine affinity.

Cookie-file injection remains supported as an optional fallback path.
