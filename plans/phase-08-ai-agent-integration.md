# Phase 8 — AI agent integration (optional)

## Goal

Reduce hand-maintained selectors by delegating navigation/extraction to an agent when useful.

## Inputs

- CDP WebSocket / endpoint exposed by Chrome.
- Prompt describing target profile and output schema.

## Ecosystem (examples)

Tools that often support CDP in 2026 include browser-use-style agents, Playwright + LangChain stacks, or Firecrawl-like products—validate current docs before locking in.

## Prompt example

> Go to `https://x.com/elonmusk`, extract the 10 latest posts as JSON with `id`, `text`, `timestamp`. Only return posts newer than the last run.

## Output

- Agent-produced structured data (e.g. merged into your `posts.jsonl` pipeline).

## When to use

- UI shifts break fixed selectors; LLM can parse HTML/DOM with guidance.
- Higher cost/latency vs deterministic Playwright—use as fallback or hybrid.

## Acceptance criteria

- [ ] Agent path is optional in config; core listener still runs without it.

## Dependencies

- [Phase 7 — Data extraction](./phase-07-data-extraction.md)

## Next phase

→ [Phase 9 — Loop & scheduling](./phase-09-loop-scheduling.md)
