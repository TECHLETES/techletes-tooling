# Engineering Cockpit Agent Instructions

These instructions apply to everything under `apps/engineering-cockpit/`.

## Repository state is the memory

Do not rely on the current Codex conversation, previous Codex sessions, or local `$CODEX_HOME` as the source of implementation state.

The durable sources are:

1. [`PROJECT_STATE.md`](PROJECT_STATE.md) for the current checkpoint and next action;
2. the active child implementation plan for detailed verified checkboxes;
3. [`SESSION_LOG.md`](SESSION_LOG.md) for append-only handoffs and findings;
4. Git branches, commits, status, and test artifacts for objective evidence.

At the start of every session, compare these sources. If they disagree, reconcile them from Git evidence before changing application code.

## Required planning workflow

Before changing application code:

1. Read [`CODEX_RUNBOOK.md`](CODEX_RUNBOOK.md).
2. Read [`PROJECT_STATE.md`](PROJECT_STATE.md).
3. Read [`IMPLEMENTATION.md`](IMPLEMENTATION.md).
4. Read [`superpowers/INDEX.md`](superpowers/INDEX.md).
5. Read the [master specification](superpowers/00-engineering-cockpit-master-specification.md).
6. Read the [master implementation roadmap](superpowers/00-engineering-cockpit-master-implementation-roadmap.md).
7. Read the exact child specification and matching implementation plan for the subsystem recorded in `PROJECT_STATE.md`.
8. Inspect `git status --short --branch`, the current branch/worktree, and recent commits.
9. Use `techletes-superpowers:using-superpowers` to select the workflow.
10. For child-plan execution, use `techletes-superpowers:subagent-driven-development` where available or `techletes-superpowers:executing-plans`.

Do not implement from the historical unnumbered monolithic design or implementation plan. They are superseded background.

## Session scope

- Implement one smallest coherent unchecked child-plan task at a time.
- Do not implement the whole application or multiple dependent subsystems in one session.
- Stop at the plan-defined verification or commit boundary.
- Continue on the same subsystem branch across sessions until its exit criteria pass.
- Start the next subsystem from the updated integration branch after the current subsystem is reviewed and merged.

## Mandatory session closeout

Before ending any implementation session:

1. Run the exact verification required for the completed child-plan step.
2. Review the diff for scope, generated artifacts, migrations, secrets, and prohibited shortcuts.
3. Check only plan boxes whose stated verification passed.
4. Update `PROJECT_STATE.md` with the branch, worktree, HEAD, status, evidence, blockers, and one exact next action.
5. Append a concise entry to `SESSION_LOG.md` using its required format.
6. Commit only at a plan-defined boundary or when the user has authorized a verified progress/handoff commit.
7. Leave the working tree clean, or explicitly record every uncommitted file and why it remains.
8. Do not begin the next plan task after closeout is requested.

A handoff is portable to another clone only after the implementation and state files are committed and pushed explicitly.

## Bootstrap requirement

The application must be bootstrapped from the **current `TECHLETES/full-stack-template`**. Inspect that repository and its `AGENTS.md` at implementation time, then preserve/adapt its actual current backend, frontend, devcontainer, Compose, PostgreSQL, Redis, authentication/RBAC, generated-client, testing, typing, linting, pre-commit, and CI conventions.

Do not create a competing independent scaffold beside the template-derived application.

## Scope discipline

- Implement only the assigned subsystem plan and prerequisite contract corrections.
- Keep public interfaces exactly consistent with downstream child specifications.
- When implementation research invalidates a requirement, stop and update the child specification and child plan before changing the architecture.
- Record the evidence and impact in `PROJECT_STATE.md` and `SESSION_LOG.md`.
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

Use the exact commands and expected outcomes in the child implementation plan. Preserve generated schemas, migrations, OpenAPI client, route tree, i18n, compatibility manifests, progress state, and release evidence as reviewed version-controlled artifacts.
