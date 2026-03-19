# Modular plans — X CDP post listener

Phased breakdown of the full architecture. Execute in order unless noted.

**Implementation spec (concrete tasks, files, verification):** [development/concrete-work.md](./development/concrete-work.md)

| Phase | Document | Summary |
|-------|----------|---------|
| 0 | [phase-00-context-and-risks.md](./phase-00-context-and-risks.md) | Strategy, 2026 rationale, legal/detection warnings |
| 1 | [phase-01-preparation.md](./phase-01-preparation.md) | Chrome, Playwright, debug port, profile |
| 2 | [phase-02-authentication-capture.md](./phase-02-authentication-capture.md) | Manual login, cookies or persistent profile |
| 3 | [phase-03-session-injection.md](./phase-03-session-injection.md) | CDP session reuse, validation |
| 4 | [phase-04-cdp-connection.md](./phase-04-cdp-connection.md) | `connect_over_cdp` wiring |
| 5 | [phase-05-anti-detection.md](./phase-05-anti-detection.md) | Stealth, UA, viewport, scripts |
| 6 | [phase-06-navigation-listener.md](./phase-06-navigation-listener.md) | Profile navigation, human-like scroll |
| 7 | [phase-07-data-extraction.md](./phase-07-data-extraction.md) | Selectors, dedupe, JSONL |
| 8 | [phase-08-ai-agent-integration.md](./phase-08-ai-agent-integration.md) | Optional agent-driven extraction |
| 9 | [phase-09-loop-scheduling.md](./phase-09-loop-scheduling.md) | Listener loop, jitter, 24/7 ops |
| 10 | [phase-10-multi-instance-scaling.md](./phase-10-multi-instance-scaling.md) | Ports, proxies, orchestration |
| 99 | [phase-99-reference-flow-maintenance.md](./phase-99-reference-flow-maintenance.md) | Flow diagram, skeleton script, maintenance |

Parent index: [../full-plan.md](../full-plan.md)
