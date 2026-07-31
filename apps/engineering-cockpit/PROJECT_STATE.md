---
schema_version: 1
project: techletes-engineering-cockpit
planning_issue: TECHLETES/techletes-tooling#7
updated_at: 2026-07-31T16:09:00+02:00
updated_by: planning
current_phase: "Phase 0 - bootstrap"
current_subsystem: "01"
current_plan: "superpowers/implementation/2026-07-31-01-template-bootstrap-runtime-topology-implementation-plan.md"
current_status: ready_to_start
working_branch: null
working_worktree: null
last_verified_commit: null
next_action: "Create the subsystem 01 branch/worktree and execute the first unchecked task in its implementation plan."
blockers: []
---

# Engineering Cockpit Project State

This file is the compact, durable handoff for the entire implementation. It must make a fresh Codex session or fresh clone productive without access to previous conversation history.

Git history, the current child implementation plan, and test evidence remain authoritative. When this file disagrees with Git, reconcile it before implementation continues.

## Current checkpoint

| Field | Value |
| --- | --- |
| Phase | Phase 0 — bootstrap |
| Active subsystem | 01 — Template bootstrap and WSL runtime topology |
| Status | Ready to start |
| Branch | Not created yet |
| Worktree | Not created yet |
| Last verified commit | Planning package on `main` |
| Last verification | Planning documents created and linked from issue #7 |
| Immediate next action | Create the subsystem 01 worktree/branch and execute the first unchecked task |
| Blockers | None known |

## Subsystem progress

Status values: `not_started`, `in_progress`, `blocked`, `verification_pending`, `complete`.

| ID | Subsystem | Status | Branch/PR | Evidence or next gate |
| --- | --- | --- | --- | --- |
| 01 | Template bootstrap and WSL runtime topology | not_started | — | Bootstrap from current full-stack template and pass baseline exit criteria |
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

Start at the first unchecked task in the subsystem 01 implementation plan. Do not infer completion from the planning commits.

### Required checkpoint evidence

Before this state advances beyond subsystem 01, record:

- exact `TECHLETES/full-stack-template` source commit;
- bootstrap method and resulting file layout;
- updated cockpit-specific `AGENTS.md` and `README.md`;
- backend/frontend/devcontainer baseline verification commands and results;
- host-native WSL startup proof;
- single-instance locking proof;
- clean working tree and verified commit SHA.

## Active decisions and assumptions

- The application remains under `apps/engineering-cockpit/` in `TECHLETES/techletes-tooling`.
- The source baseline is the current `TECHLETES/full-stack-template` at implementation time, recorded by exact commit.
- The operational control plane runs host-native in WSL with one process and one Uvicorn worker.
- Codex task execution uses `codex app-server` inside each target devcontainer over backend-owned stdio.
- PostgreSQL is durable truth; Redis is a live wakeup mechanism only.
- A saved Codex conversation is not implementation state.

## Blockers

None known. Add only blockers with concrete evidence, owner, and unblock condition.

## Working-tree handoff

No implementation worktree exists yet.

When implementation begins, replace this section with:

```text
Branch:
Worktree path:
HEAD:
Working tree: clean|dirty
Uncommitted files:
Current plan step:
Last command run:
Last command result:
Next exact command/action:
```

## Update protocol

Update this file at every verified checkpoint and before ending a Codex session.

Required changes:

1. Update front matter timestamp, status, branch/worktree, last verified commit, next action, and blockers.
2. Update the active subsystem row.
3. Record verification evidence and current handoff.
4. Ensure the matching child-plan checkboxes agree.
5. Append a session entry to `SESSION_LOG.md`.
6. Commit the state with the verified implementation checkpoint when authorized.

Do not store secrets, copied credentials, raw environment dumps, or large terminal output here.
