# Engineering Cockpit Planning Index

This directory is the authoritative planning package for `TECHLETES/techletes-tooling#7`.

The application is deliberately decomposed into subsystem specifications and matching implementation plans. An implementation agent must not treat the original broad issue body as the implementation contract. It must read this index, the system overview, and the documents for the subsystem it is implementing.

## Global architecture

```text
Windows browser
  <-> REST and authenticated WebSocket
Techletes full-stack application running locally in WSL
  -> PostgreSQL persistence and short-lived Redis notifications
  -> single control-plane process owning live task runtimes
  -> Git worktree adapter
  -> official Dev Container CLI
  -> one target devcontainer per task
  -> one `codex app-server` stdio connection per active task
  -> GitHub issue, pull-request, CI, and review integration
```

The application source is bootstrapped from `TECHLETES/full-stack-template` into `apps/engineering-cockpit/`. The inherited devcontainer is the reproducible development environment. The operational control plane runs as one WSL-local process so it owns Docker-daemon host paths and every long-lived child-process pipe. PostgreSQL and Redis may run as local Docker services bound to loopback.

## Non-negotiable decisions

- Use the current `TECHLETES/full-stack-template` as the starting codebase.
- Preserve its FastAPI, SQLModel, Alembic, React, TanStack Router/Query, generated-client, i18n, Playwright, devcontainer, and quality conventions.
- Run one control-plane process. Do not use multiple Uvicorn workers for the interactive runtime.
- Do not hand live app-server ownership to RQ or another process pool.
- Create one branch, Git worktree, devcontainer runtime, app-server process, and Codex thread per task.
- Start `codex app-server --listen stdio://` inside the target repository devcontainer through the official Dev Container CLI.
- Generate and pin app-server schemas from the exact supported Codex version. Do not maintain a guessed handwritten protocol model.
- Use structured app-server messages. Do not infer state from the Codex TUI, terminal control sequences, or text regexes.
- Persist state and protocol request identity before notifying the browser.
- Browser closure must not stop a task.
- Backend restart does not promise transparent continuation of an in-flight turn; it performs conservative recovery and marks ambiguity explicitly.
- Commit, push, draft pull request, force operations, merge, deployment, and destructive cleanup remain explicit actions.
- Bind all local control-plane and supporting service ports to loopback by default.

## Dependency graph

```text
01 Bootstrap and runtime topology
  -> 02 Repository registry and diagnostics
  -> 03 Task domain, persistence, state, and locking
      -> 04 Git worktrees, branches, and overlap
      -> 05 Devcontainer runtime and isolation
          -> 06 Process supervisor and JSON-RPC transport
              -> 07 Codex app-server core adapter
                  -> 08 Codex auth, skills, and permissions
                  -> 09 Interactive turn control
                      -> 10 Events, reconnect, and recovery
                          -> 11 Validation and change review
                          -> 12 GitHub delivery
                              -> 13 Dashboard and notifications
                                  -> 14 Security, cleanup, and operations
                                      -> 15 Test harness and rollout
```

Some implementation can proceed in parallel after its dependencies are stable:

- Subsystems 04 and 05 can be implemented in parallel after 03.
- The frontend shell in 13 can begin after API schemas from 02 and 03 exist, but its live-task controls depend on 09 and 10.
- Fake-tool infrastructure from 15 should be introduced alongside 04–07 rather than postponed until the end.

## Specifications and plans

| # | Subsystem | Specification | Implementation plan |
|---|---|---|---|
| 01 | Template bootstrap and WSL runtime topology | [Spec](spec/2026-07-31-01-template-bootstrap-runtime-topology-design.md) | [Plan](implementation/2026-07-31-01-template-bootstrap-runtime-topology-implementation-plan.md) |
| 02 | Repository registry, configuration, diagnostics, and instruction discovery | [Spec](spec/2026-07-31-02-repository-registry-configuration-diagnostics-design.md) | [Plan](implementation/2026-07-31-02-repository-registry-configuration-diagnostics-implementation-plan.md) |
| 03 | Task domain, PostgreSQL persistence, state machine, and execution locking | [Spec](spec/2026-07-31-03-task-domain-persistence-state-design.md) | [Plan](implementation/2026-07-31-03-task-domain-persistence-state-implementation-plan.md) |
| 04 | Git worktrees, branches, synchronization, overlap, and safe removal | [Spec](spec/2026-07-31-04-git-worktrees-branches-concurrency-design.md) | [Plan](implementation/2026-07-31-04-git-worktrees-branches-concurrency-implementation-plan.md) |
| 05 | Devcontainer lifecycle, Docker isolation, caching, paths, and ports | [Spec](spec/2026-07-31-05-devcontainer-runtime-isolation-design.md) | [Plan](implementation/2026-07-31-05-devcontainer-runtime-isolation-implementation-plan.md) |
| 06 | Owned process supervision and app-server JSON-RPC transport | [Spec](spec/2026-07-31-06-process-supervisor-jsonrpc-transport-design.md) | [Plan](implementation/2026-07-31-06-process-supervisor-jsonrpc-transport-implementation-plan.md) |
| 07 | Codex app-server schema compatibility, threads, turns, and events | [Spec](spec/2026-07-31-07-codex-app-server-core-design.md) | [Plan](implementation/2026-07-31-07-codex-app-server-core-implementation-plan.md) |
| 08 | Codex authentication, `CODEX_HOME`, Techletes skills, instructions, and permissions | [Spec](spec/2026-07-31-08-codex-auth-skills-permissions-design.md) | [Plan](implementation/2026-07-31-08-codex-auth-skills-permissions-implementation-plan.md) |
| 09 | Clarification, approvals, follow-up, steering, interruption, and force-stop | [Spec](spec/2026-07-31-09-interactive-turn-control-design.md) | [Plan](implementation/2026-07-31-09-interactive-turn-control-implementation-plan.md) |
| 10 | Durable events, WebSocket replay, browser reconnect, and backend recovery | [Spec](spec/2026-07-31-10-events-reconnect-recovery-design.md) | [Plan](implementation/2026-07-31-10-events-reconnect-recovery-implementation-plan.md) |
| 11 | Validation, quality gates, change review, and commit preparation | [Spec](spec/2026-07-31-11-validation-change-review-design.md) | [Plan](implementation/2026-07-31-11-validation-change-review-implementation-plan.md) |
| 12 | GitHub issue intake, push, draft PR, CI, and review monitoring | [Spec](spec/2026-07-31-12-github-delivery-design.md) | [Plan](implementation/2026-07-31-12-github-delivery-implementation-plan.md) |
| 13 | Dashboard UX, generated API client, live activity, and notifications | [Spec](spec/2026-07-31-13-dashboard-notifications-design.md) | [Plan](implementation/2026-07-31-13-dashboard-notifications-implementation-plan.md) |
| 14 | Security boundary, audit trail, quotas, retention, cleanup, and operations | [Spec](spec/2026-07-31-14-security-cleanup-operations-design.md) | [Plan](implementation/2026-07-31-14-security-cleanup-operations-implementation-plan.md) |
| 15 | Fake tools, contract tests, end-to-end acceptance, rollout, and release | [Spec](spec/2026-07-31-15-test-harness-rollout-design.md) | [Plan](implementation/2026-07-31-15-test-harness-rollout-implementation-plan.md) |

## Execution rules for coding agents

1. Read `apps/engineering-cockpit/AGENTS.md` and the inherited template instructions first.
2. Read the system overview plus the relevant subsystem spec and plan.
3. Check the dependency table in the plan. Do not implement against an unstabilized interface from an earlier subsystem.
4. Use `techletes-superpowers:using-git-worktrees` when execution begins on a broad or risky branch.
5. Use `techletes-superpowers:subagent-driven-development` or `techletes-superpowers:executing-plans` as stated by each implementation plan.
6. Follow test-first steps where behavior is introduced.
7. Regenerate the frontend OpenAPI client after backend schema changes; never hand-edit generated client files.
8. Keep PostgreSQL sessions short. Never hold a SQLModel session across a long-running subprocess or await loop.
9. Never add a second in-process owner for the same app-server connection.
10. Update checkboxes only after the stated verification command succeeds.
11. Stop when a plan's exit criteria fail; record the exact evidence instead of guessing.

## Research baseline

The plans were validated against current primary sources:

- [OpenAI Codex app-server protocol](https://github.com/openai/codex/blob/main/codex-rs/app-server/README.md)
- [OpenAI app-server test client](https://github.com/openai/codex/blob/main/codex-rs/app-server-test-client/README.md)
- [Dev Container CLI](https://github.com/devcontainers/cli)
- [Development Containers specification](https://containers.dev/)
- [Git worktree documentation](https://git-scm.com/docs/git-worktree)
- [JSON-RPC 2.0 specification](https://www.jsonrpc.org/specification)
- [Docker bind mount documentation](https://docs.docker.com/engine/storage/bind-mounts/)
- [Docker daemon access security](https://docs.docker.com/engine/security/protect-access/)
- [GitHub REST API documentation](https://docs.github.com/en/rest)

Protocol and CLI behavior is version-sensitive. The implementation records supported binary versions and fails diagnostics when the current environment falls outside the tested compatibility range.