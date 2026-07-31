# Techletes Engineering Cockpit

This directory is reserved for the Engineering Cockpit application and its implementation-ready planning documents.

The application must be bootstrapped here from the **current `TECHLETES/full-stack-template`**. Do not create an independent empty scaffold and do not execute the superseded monolithic plan.

## Start implementation here

1. [`CODEX_RUNBOOK.md`](CODEX_RUNBOOK.md) — exact one-time setup, kickoff, resume, fresh-clone, and closeout instructions.
2. [`PROJECT_STATE.md`](PROJECT_STATE.md) — current subsystem, verified checkpoint, blocker, and next action.
3. [`IMPLEMENTATION.md`](IMPLEMENTATION.md) — implementation entry point.
4. [`superpowers/INDEX.md`](superpowers/INDEX.md) — all subsystem specification/plan pairs.
5. [`SESSION_LOG.md`](SESSION_LOG.md) — append-only portable handoffs.
6. [`superpowers/00-engineering-cockpit-master-specification.md`](superpowers/00-engineering-cockpit-master-specification.md)
7. [`superpowers/00-engineering-cockpit-master-implementation-roadmap.md`](superpowers/00-engineering-cockpit-master-implementation-roadmap.md)

Repository files and Git history are the implementation memory. Saved Codex sessions are optional convenience only.

The split planning set contains a dedicated specification and task-by-task implementation plan for template bootstrap, repository registration, task persistence, worktrees, devcontainers, linked-worktree Git metadata, app-server transport and protocol, authentication/skills/permissions, interactive controls, events/recovery, validation/review/commit, GitHub delivery, dashboard UX, security/operations/cleanup, and release testing/rollout.

## Non-negotiable architecture

```text
Windows browser
  ↕ REST + replayable WebSocket
FastAPI control plane running host-native in WSL
  ↕ owned JSON-RPC stdio through `devcontainer exec`
`codex app-server` inside one isolated task devcontainer
  ↳ linked Git worktree + canonical Git common-directory mount
  ↳ one persistent Codex thread
```

PostgreSQL stores durable orchestration/events/audit and Redis carries live event wakeups. Delivery and cleanup remain explicit human-controlled operations. There is no automatic merge, auto-merge, or deployment.

The GitHub tracking issue is `TECHLETES/techletes-tooling#7`.
