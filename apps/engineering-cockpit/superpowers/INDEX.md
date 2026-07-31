# Engineering Cockpit Planning Index

## Start here

1. [Master specification](00-engineering-cockpit-master-specification.md)
2. [Master implementation roadmap](00-engineering-cockpit-master-implementation-roadmap.md)
3. Read the child specification and implementation plan for the subsystem being implemented.

The historical monolithic design/plan files are superseded and retained only as background. Do not execute them as the current plan.

## Authoritative child pairs

| ID | Subsystem | Specification | Implementation plan |
| --- | --- | --- | --- |
| 01 | Template bootstrap and WSL runtime topology | [Spec](spec/2026-07-31-01-template-bootstrap-runtime-topology-design.md) | [Plan](implementation/2026-07-31-01-template-bootstrap-runtime-topology-implementation-plan.md) |
| 02 | Repository registry, configuration, and diagnostics | [Spec](spec/2026-07-31-02-repository-registry-configuration-diagnostics-design.md) | [Plan](implementation/2026-07-31-02-repository-registry-configuration-diagnostics-implementation-plan.md) |
| 03 | Task domain, PostgreSQL persistence, state, and locking | [Spec](spec/2026-07-31-03-task-domain-persistence-state-design.md) | [Plan](implementation/2026-07-31-03-task-domain-persistence-state-implementation-plan.md) |
| 04 | Git worktrees, branches, synchronization, overlap, and safe removal | [Spec](spec/2026-07-31-04-git-worktrees-branches-concurrency-design.md) | [Plan](implementation/2026-07-31-04-git-worktrees-branches-concurrency-implementation-plan.md) |
| 05 | Devcontainer lifecycle, Docker isolation, caching, paths, and ports | [Spec](spec/2026-07-31-05-devcontainer-runtime-isolation-design.md) | [Plan](implementation/2026-07-31-05-devcontainer-runtime-isolation-implementation-plan.md) |
| 05a | Linked-worktree Git metadata mount compatibility | [Spec](spec/2026-07-31-05a-linked-worktree-git-metadata-mount-design.md) | [Plan](implementation/2026-07-31-05a-linked-worktree-git-metadata-mount-implementation-plan.md) |
| 06 | Owned process supervision and app-server JSON-RPC transport | [Spec](spec/2026-07-31-06-process-supervisor-jsonrpc-transport-design.md) | [Plan](implementation/2026-07-31-06-process-supervisor-jsonrpc-transport-implementation-plan.md) |
| 07 | Codex app-server schema compatibility, threads, turns, and events | [Spec](spec/2026-07-31-07-codex-app-server-core-design.md) | [Plan](implementation/2026-07-31-07-codex-app-server-core-implementation-plan.md) |
| 08 | Codex authentication, skills, task context, and permission profiles | [Spec](spec/2026-07-31-08-codex-auth-skills-permissions-design.md) | [Plan](implementation/2026-07-31-08-codex-auth-skills-permissions-implementation-plan.md) |
| 09 | Clarification, approvals, follow-up, steering, interruption, and force-stop | [Spec](spec/2026-07-31-09-interactive-turn-control-design.md) | [Plan](implementation/2026-07-31-09-interactive-turn-control-implementation-plan.md) |
| 10 | Durable events, browser reconnect, and backend recovery | [Spec](spec/2026-07-31-10-events-reconnect-recovery-design.md) | [Plan](implementation/2026-07-31-10-events-reconnect-recovery-implementation-plan.md) |
| 11 | Validation, quality gates, change review, and explicit local commit | [Spec](spec/2026-07-31-11-validation-review-commit-design.md) | [Plan](implementation/2026-07-31-11-validation-review-commit-implementation-plan.md) |
| 12 | GitHub issue intake, push, draft PR, CI, and review monitoring | [Spec](spec/2026-07-31-12-github-delivery-lifecycle-design.md) | [Plan](implementation/2026-07-31-12-github-delivery-lifecycle-implementation-plan.md) |
| 13 | Dashboard UX, generated client, live activity, and notifications | [Spec](spec/2026-07-31-13-dashboard-ux-notifications-design.md) | [Plan](implementation/2026-07-31-13-dashboard-ux-notifications-implementation-plan.md) |
| 14 | Security, audit, quotas, retention, cleanup, and WSL operations | [Spec](spec/2026-07-31-14-security-operations-cleanup-design.md) | [Plan](implementation/2026-07-31-14-security-operations-cleanup-implementation-plan.md) |
| 15 | Deterministic test harness, acceptance matrix, rollout, and release | [Spec](spec/2026-07-31-15-test-harness-rollout-release-design.md) | [Plan](implementation/2026-07-31-15-test-harness-rollout-release-implementation-plan.md) |

## Required reading by implementation phase

### Before writing code

- master specification;
- master roadmap;
- subsystem 01 spec/plan;
- current `TECHLETES/full-stack-template` and its `AGENTS.md`;
- `TECHLETES/techletes-tooling/AGENTS.md`;
- `techletes-superpowers:using-superpowers` and the workflow skill selected for the task.

### Before any Dev Container/Codex implementation

Read 04, 05, 05a, 06, 07, and 08 together. The linked-worktree Git common-directory mount is not optional.

### Before any browser question/approval implementation

Read 07, 08, 09, and 10 together. Requests must persist before notification and cannot be retried automatically after an ambiguous connection loss.

### Before commit/GitHub delivery

Read 04, 05a, 11, 12, and 14 together. Git hooks/signing, secret scanning, expected SHAs, force-with-lease, and explicit audit/confirmation boundaries all apply.

### Before release

Read 14 and 15 plus every child plan's exit criteria. A child implementation is not complete merely because its unit tests pass.

## Cross-cutting implementation invariants

- Bootstrap from current full-stack template; no competing scaffold.
- Operational control plane is host-native WSL, one process/worker.
- PostgreSQL is durable truth; Redis is live wakeup only.
- Official Dev Container CLI is runtime source of truth.
- Every task gets its own branch/worktree/runtime/app-server/thread/mutable state.
- Linked-worktree Git common directory is mounted and verified inside each task container.
- Codex protocol is generated and validated from the exact pinned version.
- Techletes skills/auth/permission profile are verified before work.
- Browser disconnect never stops a task; backend restart never reattaches an old pipe.
- Ambiguous work becomes `RECOVERY_REQUIRED`; prompts/approvals are not replayed.
- Validation/commit/push/PR/cleanup are explicit, exact-state, idempotent, and audited.
- No merge, auto-merge, deployment, broad prune, plain force, hook bypass, or TUI scraping.
- CI uses strict fakes; real credentials only appear in explicit local acceptance.

## Planning changes

When implementation research invalidates a requirement:

1. stop the affected implementation task;
2. update the child specification first;
3. update the child implementation plan and downstream contracts;
4. document evidence and risks;
5. obtain review before continuing;
6. never silently weaken a safety invariant in code.
