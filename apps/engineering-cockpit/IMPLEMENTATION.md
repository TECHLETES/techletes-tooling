# Engineering Cockpit Implementation Entry Point

The application will be implemented under this directory, bootstrapped from the current `TECHLETES/full-stack-template`.

Do not start from an empty scaffold and do not execute the historical monolithic plan.

## Start and resume here

For every new Codex session, including a session on another machine or fresh clone:

1. Read [`CODEX_RUNBOOK.md`](CODEX_RUNBOOK.md).
2. Read [`PROJECT_STATE.md`](PROJECT_STATE.md).
3. Inspect the current branch, worktree, HEAD, and working tree.
4. Read [`SESSION_LOG.md`](SESSION_LOG.md), especially the latest entry.
5. Continue with the active subsystem recorded in `PROJECT_STATE.md`.

Saved Codex session history is optional. The repository state must be sufficient to resume.

## Planning reading order

1. [`superpowers/INDEX.md`](superpowers/INDEX.md)
2. [`superpowers/00-engineering-cockpit-master-specification.md`](superpowers/00-engineering-cockpit-master-specification.md)
3. [`superpowers/00-engineering-cockpit-master-implementation-roadmap.md`](superpowers/00-engineering-cockpit-master-implementation-roadmap.md)
4. The specification for the active subsystem in `PROJECT_STATE.md`
5. The matching child implementation plan

For subsystem 01, start with:

- [`superpowers/spec/2026-07-31-01-template-bootstrap-runtime-topology-design.md`](superpowers/spec/2026-07-31-01-template-bootstrap-runtime-topology-design.md)
- [`superpowers/implementation/2026-07-31-01-template-bootstrap-runtime-topology-implementation-plan.md`](superpowers/implementation/2026-07-31-01-template-bootstrap-runtime-topology-implementation-plan.md)

For every later subsystem, read its child specification and implementation plan before changing code.

## Durable progress model

- `PROJECT_STATE.md` contains the compact current checkpoint and one next action.
- The current child implementation plan contains the detailed verified checklist.
- `SESSION_LOG.md` contains append-only session handoffs and findings.
- Git commits are the portable recovery boundary.
- Tests and generated artifacts are the evidence.

These files must be updated at every verified checkpoint. Do not mark work complete based only on a Codex response or an unverified diff.

## Workflow

Use `techletes-superpowers:using-superpowers` first. For the multi-step child plans, use `techletes-superpowers:subagent-driven-development` where available or `techletes-superpowers:executing-plans`.

Each child plan has its own tests, commits, integration gate, risks, and exit criteria. A subsystem is not complete merely because its unit tests pass.

Recommended structure:

```text
one subsystem
-> one dedicated branch/worktree
-> several small Codex sessions
-> one verified plan task/checkpoint per session
-> state and session-log update
-> reviewable commits
-> subsystem exit gate
-> review/merge
-> next subsystem branch from updated integration branch
```

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

## Session completion requirement

Before a Codex session ends, it must:

1. run the current plan step's required verification;
2. update only verified checkboxes;
3. update `PROJECT_STATE.md`;
4. append `SESSION_LOG.md`;
5. record exact branch, HEAD, tests, blocker, working-tree state, and next action;
6. commit at the authorized plan boundary;
7. stop without beginning another task.

Use the exact kickoff, resume, and closeout prompts in `CODEX_RUNBOOK.md`.
