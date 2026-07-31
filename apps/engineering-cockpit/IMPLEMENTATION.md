# Engineering Cockpit Implementation Entry Point

The application will be implemented under this directory, bootstrapped from the current `TECHLETES/full-stack-template`.

Do not start from an empty scaffold and do not execute the historical monolithic plan.

## Development workflow boundary

The Sol/Terra controller and Luna Medium subagent workflow is how this repository is implemented. It is not Engineering Cockpit product functionality.

Do not add model selection, subagent-role orchestration, or the repository's SDD progress ledger to the cockpit application merely because this implementation workflow uses them.

Read [`DEVELOPMENT_ORCHESTRATION.md`](DEVELOPMENT_ORCHESTRATION.md) for the binding development-role contract.

## Start and resume here

For every new Codex controller session, including a session on another machine or fresh clone:

1. Start the main session with GPT-5.6 Sol or GPT-5.6 Terra.
2. Read [`CODEX_RUNBOOK.md`](CODEX_RUNBOOK.md).
3. Read [`DEVELOPMENT_ORCHESTRATION.md`](DEVELOPMENT_ORCHESTRATION.md).
4. Read [`PROJECT_STATE.md`](PROJECT_STATE.md).
5. Read [`.superpowers/sdd/progress.md`](../../.superpowers/sdd/progress.md).
6. Inspect the current branch, worktree, HEAD, and working tree.
7. Read [`SESSION_LOG.md`](SESSION_LOG.md), especially the latest entry.
8. Continue with the active subsystem recorded in `PROJECT_STATE.md`.

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

- `PROJECT_STATE.md` contains the compact current project/subsystem checkpoint and one next action.
- `.superpowers/sdd/progress.md` contains task-level implementer/reviewer/fixer progress for the active child plan.
- The current child implementation plan contains the detailed verified checklist.
- `SESSION_LOG.md` contains append-only controller-session handoffs and findings.
- Git commits are the portable recovery boundary.
- Tests, reports, review packages, and generated artifacts are the evidence.

These files must be updated at every verified checkpoint. Do not mark work complete based only on a Codex response or an unverified diff.

## Controller/subagent workflow

Use `techletes-superpowers:using-superpowers` first, then `techletes-superpowers:subagent-driven-development` for the active child plan.

The user kickoff prompt explicitly authorizes Subagent-Driven Development for that plan. The Sol/Terra controller must then:

1. pre-flight the plan for contradictions;
2. initialize or reconcile `.superpowers/sdd/progress.md`;
3. dispatch a fresh implementer per task;
4. dispatch a fresh task reviewer after each implementation;
5. dispatch fix subagents for Critical/Important findings and re-review;
6. continue without asking between tasks;
7. dispatch one final whole-branch reviewer when the child plan is complete;
8. close out or stop only under the conditions in `DEVELOPMENT_ORCHESTRATION.md`.

Every subagent dispatch must explicitly specify:

```yaml
model: gpt-5.6-luna
reasoning_effort: medium
```

The Sol/Terra controller owns architecture, integration, review adjudication, progress files, and exit-gate decisions. Luna Medium subagents own bounded implementation, review, and fix work.

Each child plan has its own tests, commits, integration gate, risks, and exit criteria. A subsystem is not complete merely because its unit tests pass.

Recommended structure:

```text
one subsystem
-> one dedicated branch/worktree
-> one or more Sol/Terra controller sessions
-> fresh Luna Medium implementer per plan task
-> fresh Luna Medium reviewer per task
-> fix/re-review loop when required
-> durable ledger and state updates
-> final Luna Medium whole-branch review
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

Before a Sol/Terra controller session ends, it must:

1. stop dispatching new tasks;
2. record any active subagent as completed, blocked, or interrupted;
3. run or confirm the current plan tasks' required verification;
4. update only verified and reviewed plan checkboxes;
5. update `.superpowers/sdd/progress.md`;
6. update `PROJECT_STATE.md`;
7. append `SESSION_LOG.md`;
8. record exact branch, HEAD, tests, reviewer status, blockers, working-tree state, and next action;
9. commit at an authorized plan boundary;
10. stop without beginning another task after closeout is requested.

Use the exact kickoff, resume, and closeout prompts in `CODEX_RUNBOOK.md`.
