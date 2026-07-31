# Engineering Cockpit Implementation Entry Point

The application will be implemented under this directory, bootstrapped from the current `TECHLETES/full-stack-template`.

Do not start from an empty scaffold and do not execute the historical monolithic plan.

## Required reading order

1. [`superpowers/INDEX.md`](superpowers/INDEX.md)
2. [`superpowers/00-engineering-cockpit-master-specification.md`](superpowers/00-engineering-cockpit-master-specification.md)
3. [`superpowers/00-engineering-cockpit-master-implementation-roadmap.md`](superpowers/00-engineering-cockpit-master-implementation-roadmap.md)
4. [`superpowers/spec/2026-07-31-01-template-bootstrap-runtime-topology-design.md`](superpowers/spec/2026-07-31-01-template-bootstrap-runtime-topology-design.md)
5. [`superpowers/implementation/2026-07-31-01-template-bootstrap-runtime-topology-implementation-plan.md`](superpowers/implementation/2026-07-31-01-template-bootstrap-runtime-topology-implementation-plan.md)

For every later subsystem, read its child specification and implementation plan before changing code.

## Workflow

Use `techletes-superpowers:using-superpowers` first. For the multi-step child plans, use `techletes-superpowers:subagent-driven-development` where available or `techletes-superpowers:executing-plans`.

Each child plan has its own tests, commits, integration gate, risks, and exit criteria. A subsystem is not complete merely because its unit tests pass.

## Critical implementation constraints

- Start from `TECHLETES/full-stack-template` and preserve/adapt its actual current conventions.
- Run the operational control plane host-native in WSL with one process/Uvicorn worker.
- Use PostgreSQL for durable state and Redis for live event wakeups.
- Run `codex app-server` inside each task devcontainer over backend-owned stdio.
- Use pinned generated app-server schemas; do not scrape the Codex TUI.
- Mount the linked worktree's canonical Git common directory into each task devcontainer at the exact referenced path.
- Keep each task's branch, worktree, devcontainer, app-server process, thread, requests, and mutable application state isolated.
- Persist questions/approvals before notifying the browser and answer exact protocol request IDs at most once.
- Never silently replay an ambiguous in-flight turn after backend restart.
- Delivery and cleanup actions are explicit, exact-state, authorized, idempotent, and audited.
- No merge, auto-merge, production deployment, broad prune, plain force, hook/signing bypass, or arbitrary command/path execution.
