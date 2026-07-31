# Engineering Cockpit Agent Instructions

These instructions apply to everything under `apps/engineering-cockpit/`.

## Repository state is the memory

Do not rely on the current Codex conversation, previous Codex sessions, or local `$CODEX_HOME` as the source of implementation state.

The durable sources are:

1. [`PROJECT_STATE.md`](PROJECT_STATE.md) for the current checkpoint and next action;
2. the active child implementation plan for detailed verified checkboxes;
3. [`.superpowers/sdd/progress.md`](../../.superpowers/sdd/progress.md) for task-level subagent execution and reviews;
4. [`SESSION_LOG.md`](SESSION_LOG.md) for append-only handoffs and findings;
5. Git branches, commits, status, and test artifacts for objective evidence.

At the start of every session, compare these sources. If they disagree, reconcile them from Git evidence before changing application code.

## Implementation controller and subagents

This section governs how Codex implements this repository. It is **not Engineering Cockpit product functionality**.

- Every human-started implementation session uses GPT-5.6 Sol or GPT-5.6 Terra as the controller.
- The controller is responsible for planning, context, task selection, review adjudication, integration, verification, and durable state.
- The controller must use `techletes-superpowers:subagent-driven-development` for the active child implementation plan.
- The user's kickoff prompt provides explicit consent to use that skill for the active plan. A new child plan requires fresh explicit consent.
- Every exploration, implementer, reviewer, fixer, and final-review subagent must be dispatched explicitly with:

```yaml
model: gpt-5.6-luna
reasoning_effort: medium
```

- Use a fresh Luna Medium implementer per task and a fresh Luna Medium task reviewer after each implementation.
- Dispatch Luna Medium fix subagents for Critical or Important findings and re-review the task.
- Dispatch one fresh Luna Medium final reviewer over the complete subsystem branch before declaring it complete.
- Sequential subagents use the current subsystem checkout. Parallel implementers require separate assigned worktrees and may never share a checkout.
- The controller owns `PROJECT_STATE.md`, `.superpowers/sdd/progress.md`, child-plan checkboxes, and `SESSION_LOG.md`. Subagents report through task-specific report files.
- The controller should not perform normal feature implementation itself while the subagent workflow is available. Coordination edits, plan corrections, conflict resolution, integration, and progress updates remain controller work.

Read [`DEVELOPMENT_ORCHESTRATION.md`](DEVELOPMENT_ORCHESTRATION.md) for the complete workflow.

Do not add Sol/Terra model selection, Luna dispatch policy, or this implementation ledger to the cockpit product unless a separate approved product specification requires it.

## Required planning workflow

Before changing application code:

1. Read [`CODEX_RUNBOOK.md`](CODEX_RUNBOOK.md).
2. Read [`DEVELOPMENT_ORCHESTRATION.md`](DEVELOPMENT_ORCHESTRATION.md).
3. Read [`PROJECT_STATE.md`](PROJECT_STATE.md).
4. Read [`.superpowers/sdd/progress.md`](../../.superpowers/sdd/progress.md).
5. Read [`IMPLEMENTATION.md`](IMPLEMENTATION.md).
6. Read [`superpowers/INDEX.md`](superpowers/INDEX.md).
7. Read the [master specification](superpowers/00-engineering-cockpit-master-specification.md).
8. Read the [master implementation roadmap](superpowers/00-engineering-cockpit-master-implementation-roadmap.md).
9. Read the exact child specification and matching implementation plan for the subsystem recorded in `PROJECT_STATE.md`.
10. Inspect `git status --short --branch`, the current branch/worktree, and recent commits.
11. Use `techletes-superpowers:using-superpowers` and then `techletes-superpowers:subagent-driven-development`.

Do not implement from the historical unnumbered monolithic design or implementation plan. They are superseded background.

## Session scope

- Work on one active child subsystem implementation plan per controller session.
- Decompose that plan into small, reviewable subagent tasks as defined by the plan.
- Once the user has explicitly confirmed Subagent-Driven Development for the active plan, continue through tasks without asking whether to proceed between them.
- Stop only when the user interrupts, a genuine blocker or plan contradiction prevents progress, the environment prevents safe continuation, or the child plan and final review are complete.
- Never continue into the next subsystem in the same branch or under the previous plan's consent.
- Continue on the same subsystem branch across interrupted sessions until its exit criteria pass.
- Start the next subsystem from the updated integration branch after the current subsystem is reviewed and merged.

## Mandatory session closeout

Before ending any implementation session:

1. Stop dispatching new tasks.
2. Let an active subagent reach a safe conclusion or record it as interrupted.
3. Run or confirm the exact verification required for completed work.
4. Review the integrated diff for scope, generated artifacts, migrations, secrets, and prohibited shortcuts.
5. Check only plan boxes whose stated verification and task review passed.
6. Update `.superpowers/sdd/progress.md` with task commits, reports, reviews, findings, and next action.
7. Update `PROJECT_STATE.md` with the branch, worktree, HEAD, status, evidence, blockers, and one exact next action.
8. Append a concise entry to `SESSION_LOG.md` using its required format.
9. Commit only at a plan-defined boundary or when the user has authorized a verified progress/handoff commit.
10. Leave the working tree clean, or explicitly record every uncommitted file and why it remains.
11. Do not begin another task after closeout is requested.

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
- Complete the child plan's tests, commits, manual/real acceptance where required, task reviews, final branch review, and exit criteria before marking it done.

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

Use the exact commands and expected outcomes in the child implementation plan. Preserve generated schemas, migrations, OpenAPI client, route tree, i18n, compatibility manifests, progress state, review artifacts, and release evidence as reviewed version-controlled artifacts.
