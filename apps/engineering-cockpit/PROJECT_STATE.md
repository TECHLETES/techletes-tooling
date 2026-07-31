---
schema_version: 1
project: techletes-engineering-cockpit
planning_issue: TECHLETES/techletes-tooling#7
updated_at: 2026-07-31T18:25:00+02:00
updated_by: controller
current_phase: "Phase 0 - bootstrap"
current_subsystem: "01"
current_plan: "superpowers/implementation/2026-07-31-01-template-bootstrap-runtime-topology-implementation-plan.md"
current_status: verification_pending
working_branch: feature/cockpit-01-bootstrap
working_worktree: /home/thom/worktrees/techletes-tooling/cockpit-01-bootstrap
last_verified_commit: 1c4321c
next_action: "Run final whole-branch review, then hand off the verified subsystem branch for local merge/push."
blockers: []
---

# Engineering Cockpit Project State

This file is the compact, durable handoff for the entire implementation. It must make a fresh Codex session or fresh clone productive without access to previous conversation history.

Git history, the current child implementation plan, `.superpowers/sdd/progress.md`, and test/review evidence remain authoritative. When these sources disagree, reconcile them from Git evidence before implementation continues.

## Current checkpoint

| Field | Value |
| --- | --- |
| Phase | Phase 0 — bootstrap |
| Active subsystem | 01 — Template bootstrap and WSL runtime topology |
| Status | In progress |
| Branch | `feature/cockpit-01-bootstrap` |
| Worktree | `/home/thom/worktrees/techletes-tooling/cockpit-01-bootstrap` |
| Last verified commit | `1c4321c` |
| Last verification | Host full baseline and focused final-fix checks — PASS; fresh Luna re-review found no code defect |
| Immediate next action | Resolve the subsystem 05a Git-metadata mount dependency, then rerun Task 6 in-container pre-commit |
| Blockers | Task 6 in-container pre-commit needs the later 05a linked-worktree Git metadata mount |

## Subsystem progress

Status values: `not_started`, `in_progress`, `blocked`, `verification_pending`, `complete`.

| ID | Subsystem | Status | Branch/PR | Evidence or next gate |
| --- | --- | --- | --- | --- |
| 01 | Template bootstrap and WSL runtime topology | blocked | `feature/cockpit-01-bootstrap` | All code and host checks pass; Task 6 in-container pre-commit awaits subsystem 05a Git-metadata mount |
| 02 | Repository registry, configuration, and diagnostics | not_started | — | Requires 01 |
| 03 | Task domain, PostgreSQL persistence, state, and locking | not_started | — | Requires 01–02 |
| 04 | Git worktrees, branches, synchronization, overlap, and removal | not_started | — | Requires 03 |
| 05 | Devcontainer lifecycle, Docker isolation, caching, paths, and ports | not_started | — | Requires 03; coordinates with 04 |
| 05a | Linked-worktree Git metadata mount compatibility | not_started | — | Requires 04–05; mandatory runtime gate |
| 06 | Process supervision and JSON-RPC transport | not_started | — | Requires 05 and 05a |
| 07 | Codex app-server schemas, threads, turns, and events | not_started | — | Requires 06 |
| 08 | Codex authentication, skills, context, and permissions | not_started | — | Requires 07 |
| 09 | Interactive turn control | not_started | — | Requires 07–08 |
| 10 | Events, reconnect, and recovery | not_started | — | Requires 09 |
| 11 | Validation, change review, and explicit local commit | not_started | — | Requires 04, 05a, 09–10 |
| 12 | GitHub issue, push, draft PR, CI, and review lifecycle | not_started | — | Requires 11 |
| 13 | Dashboard UX and notifications | not_started | — | API shell may start earlier; full flow requires 09–12 |
| 14 | Security, audit, quotas, cleanup, and operations | not_started | — | Cross-cutting; final gate requires earlier subsystems |
| 15 | Test harness, acceptance, rollout, and release | not_started | — | Fake tools begin earlier; final gate requires all subsystems |

## Current subsystem details

### Specification

`superpowers/spec/2026-07-31-01-template-bootstrap-runtime-topology-design.md`

### Implementation plan

`superpowers/implementation/2026-07-31-01-template-bootstrap-runtime-topology-implementation-plan.md`

### Current unchecked task

Start at the first unchecked task in the subsystem 01 implementation plan. The canonical subsystem branch is `feature/cockpit-01-bootstrap`; do not infer completion from the planning commits.

The Sol/Terra controller must initialize the task rows in `.superpowers/sdd/progress.md`, then dispatch fresh Luna Medium implementers and reviewers according to `DEVELOPMENT_ORCHESTRATION.md`.

### Required checkpoint evidence

Before this state advances beyond subsystem 01, record:

- exact `TECHLETES/full-stack-template` source commit;
- bootstrap method and resulting file layout;
- updated cockpit-specific `AGENTS.md` and `README.md`;
- backend/frontend/devcontainer baseline verification commands and results;
- host-native WSL startup proof;
- single-instance locking proof;
- per-task implementer/reviewer evidence in `.superpowers/sdd/progress.md`;
- final whole-branch review result;
- clean working tree and verified commit SHA.

## Active decisions and assumptions

### Repository implementation workflow

- Every human-started implementation session uses GPT-5.6 Sol or GPT-5.6 Terra as the controller.
- The controller uses `techletes-superpowers:subagent-driven-development` for the active child plan after explicit user authorization.
- Every exploration, implementation, review, fix, and final-review subagent uses `gpt-5.6-luna` with medium reasoning.
- The controller owns planning, integration, review adjudication, state files, and exit-gate decisions.
- This Sol/Terra/Luna policy is only for implementing the repository. It is not Engineering Cockpit product functionality.
- Evidence may justify resequencing the roadmap: move the smallest safe
  prerequisite earlier, update the affected spec/plan and durable evidence,
  and preserve the later subsystem's remaining scope and all requirements.

### Product and architecture

- The application remains under `apps/engineering-cockpit/` in `TECHLETES/techletes-tooling`.
- The source baseline is the current `TECHLETES/full-stack-template` at implementation time, recorded by exact commit.
- The operational control plane runs host-native in WSL with one process and one Uvicorn worker.
- Codex task execution uses `codex app-server` inside each target devcontainer over backend-owned stdio.
- PostgreSQL is durable truth; Redis is a live wakeup mechanism only.
- A saved Codex conversation is not implementation state.

## Blockers

None known. Add only blockers with concrete evidence, owner, and unblock condition.

## Working-tree handoff

Controller model: Sol/Terra
Active plan consent: confirmed
Branch: feature/cockpit-01-bootstrap
Worktree path: /home/thom/worktrees/techletes-tooling/cockpit-01-bootstrap
HEAD: 1c4321c
Working tree: dirty (controller state, Task 6 verification evidence, plan/spec correction)
Uncommitted files: `PROJECT_STATE.md`, `SESSION_LOG.md`, `.superpowers/sdd/progress.md`, `docs/bootstrap-verification.md`, active 01 spec/plan
Current plan task: Task 6 — Complete baseline verification
Active subagent role/task: None
Last reviewed task: Final whole-branch Luna re-review — code findings resolved
Last command run: focused identity/preflight/concurrent-launch/runtime-lock checks
Last command result: PASS
Next exact command/action: Implement the approved subsystem 05a Git-metadata mount, then rerun `devcontainer exec ... pre-commit run --all-files`.

For future checkpoints, replace this section with current values in this form:

```text
Controller model: Sol|Terra
Active plan consent: confirmed|not confirmed
Branch:
Worktree path:
HEAD:
Working tree: clean|dirty
Uncommitted files:
Current plan task:
Active subagent role/task:
Last reviewed task:
Last command run:
Last command result:
Next exact command/action:
```

## Update protocol

Update this file at every verified checkpoint and before ending a controller session.

Required changes:

1. Update front matter timestamp, status, branch/worktree, last verified commit, next action, and blockers.
2. Update the active subsystem row.
3. Reconcile `.superpowers/sdd/progress.md` with task reports, reviews, and child-plan checkboxes.
4. Record verification evidence and current handoff.
5. Ensure the matching child-plan checkboxes agree.
6. Append a session entry to `SESSION_LOG.md`.
7. Commit the state with the verified implementation checkpoint when authorized.

Do not store secrets, copied credentials, raw environment dumps, large terminal output, or private chain-of-thought here.
