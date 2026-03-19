# Phase 10 — Multi-instance scaling

## Goal

Monitor many accounts with lower correlation and blast radius.

## Approach

1. **Separate Chrome instances** on different debug ports (`9222`, `9223`, …).
2. **Isolation:** unique `user-data-dir` or cookie sets per instance.
3. **Dashboard (optional):** FastAPI + WebSocket to start/stop instances and stream logs.
4. **Proxies:** ideally one residential proxy per instance via Playwright context proxy settings.
5. **Orchestration:** Docker Compose, PM2, or similar.

## Acceptance criteria

- [ ] Port/dir/proxy mapping documented per instance.
- [ ] Failure on one instance does not take down others.

## Dependencies

- [Phase 9 — Loop & scheduling](./phase-09-loop-scheduling.md)

## Next phase

→ [Reference — Flow, skeleton, maintenance](./phase-99-reference-flow-maintenance.md)
