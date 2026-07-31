# Engineering Cockpit Agent Instructions

These instructions apply to everything under `apps/engineering-cockpit/`.

## Required planning workflow

Before changing application code:

1. Read [`IMPLEMENTATION.md`](IMPLEMENTATION.md).
2. Read [`superpowers/INDEX.md`](superpowers/INDEX.md).
3. Read the [master specification](superpowers/00-engineering-cockpit-master-specification.md).
4. Read the [master implementation roadmap](superpowers/00-engineering-cockpit-master-implementation-roadmap.md).
5. Read the exact child specification and matching implementation plan for the subsystem assigned to you.
6. Use `techletes-superpowers:using-superpowers` to select the workflow.
7. For child-plan execution, use `techletes-superpowers:subagent-driven-development` where available or `techletes-superpowers:executing-plans`.

Do not implement from the historical unnumbered monolithic design or implementation plan. They are superseded background.

## Bootstrap requirement

The application must be bootstrapped from the **current `TECHLETES/full-stack-template`**. Inspect that repository and its `AGENTS.md` at implementation time, then preserve/adapt its actual current backend, frontend, devcontainer, Compose, PostgreSQL, Redis, authentication/RBAC, generated-client, testing, typing, linting, pre-commit, and CI conventions.

Do not create a competing independent scaffold beside the template-derived application.

## Scope discipline

- Implement only the assigned subsystem plan and prerequisite contract corrections.
- Keep public interfaces exactly consistent with downstream child specifications.
- When implementation research invalidates a requirement, stop and update the child specification and child plan before changing the architecture.
- Do not silently weaken trust, sandbox, approval, recovery, validation, delivery, cleanup, or audit requirements.
- Complete the child plan's tests, commits, manual/real acceptance where required, and exit criteria before marking it done.

## Core architecture constraints

- Operational backend runs host-native in WSL, one process and one Uvicorn worker.
- PostgreSQL is durable state/event/audit truth; Redis provides live event wakeups only.
- Each task owns a separate branch, linked worktree, devcontainer runtime, app-server process/connection, Codex thread, event/request ownership, and mutable application state.
- The canonical Git common directory must be mounted and verified inside linked-worktree task devcontainers as specified by subsystem 05a.
- `codex app-server` inside the task devcontainer, over backend-owned stdio, is the primary agent integration.
- Protocol traffic must match generated schemas from the exact pinned Codex version.
- Techletes skills, authentication, task context, and permission profile are verified before a turn starts.
- Questions/approvals persist before browser notification and map to exact protocol request IDs.
- Browser closure never stops work. Backend restart never claims ownership of an old stdio connection.
- Ambiguous in-flight work becomes `RECOVERY_REQUIRED` and is not automatically replayed.
- Validation, commit, push, PR, force, rebuild, cleanup, branch deletion, and volume deletion are explicit, exact-state, authorized, idempotent, and audited.

## Prohibited shortcuts

Do not add:

- Codex TUI/terminal scraping;
- tmux as the app-server protocol;
- `codex exec --json` as the normal runtime;
- multiple operational Uvicorn workers;
- SQLite control-plane persistence;
- automatic rebuild on resume;
- guessed/copy-based Codex credential handling;
- automatic question/approval response;
- automatic replay of a lost turn;
- arbitrary browser/model-provided host commands or paths;
- `git add .`, `--no-verify`, signing bypass, plain `--force`, broad Docker/Git prune, or recursive worktree deletion;
- merge, auto-merge, or production deployment;
- non-loopback service exposure in the MVP.

## Verification

Use the exact commands and expected outcomes in the child implementation plan. Preserve generated schemas, migrations, OpenAPI client, route tree, i18n, compatibility manifests, and release evidence as reviewed version-controlled artifacts.
