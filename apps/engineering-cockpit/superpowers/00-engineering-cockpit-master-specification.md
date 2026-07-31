# Techletes Engineering Cockpit — Master Specification

## Status and authority

This document is the architectural entry point for the Engineering Cockpit. It replaces the original single-document design as the authoritative overview.

Detailed requirements live in the child specifications under `superpowers/spec/`. When a child specification is more specific, the child wins. Implementation sequencing lives in `00-engineering-cockpit-master-implementation-roadmap.md` and the child plans under `superpowers/implementation/`.

The original broad documents remain historical context only:

- `spec/2026-07-31-engineering-cockpit-design.md`
- `implementation/2026-07-31-engineering-cockpit-implementation-plan.md`

An implementation agent must not execute the historical monolithic plan task-by-task.

## Product goal

Build a local-first WSL engineering cockpit from the current `TECHLETES/full-stack-template` that lets a Techletes developer launch, monitor, interact with, review, validate, and deliver multiple Codex development tasks across multiple repositories from one authenticated browser interface.

Each task is isolated as:

```text
registered trusted repository
  -> task branch + linked Git worktree
  -> repository devcontainer for that worktree
  -> codex app-server inside that devcontainer
  -> one persistent Codex thread
  -> one active turn at a time
  -> durable events, questions, approvals, validation, review, commit, push, draft PR
```

## Primary architecture

```text
Windows browser
  ↕ same-origin REST + authenticated replayable WebSocket
FastAPI control plane running host-native in WSL
  ├─ PostgreSQL: orchestration, event, audit, validation, delivery truth
  ├─ Redis: live event wakeups only
  ├─ Git/worktree control on WSL filesystem
  ├─ Dev Container CLI + narrow Docker inspection/control
  ├─ owned `devcontainer exec ... codex app-server` child per active task
  ├─ JSON-RPC-like stdio transport using pinned generated Codex schemas
  └─ host GitHub CLI for issue/push/PR/check/review lifecycle

Task devcontainer
  ├─ mounted task worktree
  ├─ mounted canonical Git common directory at exact linked-worktree path
  ├─ persistent authenticated CODEX_HOME under trust policy
  ├─ Techletes skills configured and verified
  └─ task-specific app/runtime mutable state
```

## Non-negotiable decisions

### Bootstrap and topology

- Start from the current `TECHLETES/full-stack-template`; adapt its actual current files and conventions.
- Keep the application under `apps/engineering-cockpit/` in `TECHLETES/techletes-tooling` for now.
- Operational backend runs host-native in WSL, one process and one Uvicorn worker.
- The inherited devcontainer remains the cockpit development environment, not the production control-plane owner.
- PostgreSQL and Redis remain inherited support services; do not introduce SQLite.

### Agent integration

- `codex app-server` inside each task devcontainer is the primary runtime from the first real vertical slice.
- The WSL backend owns the `devcontainer exec` process and stdin/stdout/stderr.
- Use generated schemas from the exact pinned Codex version; unsupported protocol drift blocks execution.
- Do not use TUI scraping, tmux as protocol, the experimental app-server WebSocket listener, or `codex exec --json` as the normal workflow.
- One task owns one logical thread and at most one active turn.

### Worktree and devcontainer isolation

- Repositories/worktrees live under approved WSL paths, not `/mnt/c`.
- Each task has a unique branch, worktree, devcontainer runtime, app-server process/connection, thread, mutable application volumes, and event/request ownership.
- Images and safe package download caches may be shared; `.venv`, `node_modules`, database/search/object-store data, and runtime state are task-specific.
- Normal resume never rebuilds a devcontainer.
- Linked worktrees require the canonical Git common directory mounted read-write at the exact absolute path referenced by the worktree `.git` file. The mechanism must be supported and tested against the pinned Dev Container CLI.

### Persistence and events

- `CockpitTask` is the aggregate root; all state transitions are explicit and validated.
- State plus matching event commits atomically.
- PostgreSQL is durable event truth; Redis carries event-ID wakeups only.
- Browser closure never stops work.
- Backend restart cannot reattach old stdio and must reconcile conservatively.
- Ambiguous in-flight work becomes `RECOVERY_REQUIRED`; no automatic prompt or approval replay.

### Permissions and delivery

- Only reviewed trusted repositories may execute host/container code with credential/Git metadata mounts.
- Techletes skills, repository instructions, context fingerprints, and execution profiles are verified before a turn starts.
- No automatic merge, auto-merge, production deployment, broad Docker/Git cleanup, plain force push, hook bypass, or signing bypass.
- Commit, push, force-with-lease, draft PR, PR-ready transition, cleanup, branch deletion, and volume deletion are explicit, versioned, authorized, idempotent, and audited actions.

### Testing and release

- CI uses deterministic external-tool fakes and real PostgreSQL/Redis; no real credentials.
- Fakes are child processes/adapters that exercise production boundaries.
- Real local acceptance proves two concurrent task devcontainers/app-servers, browser question/approval handling, reconnect/recovery, validation/commit, draft PR delivery, overlap warning, and safe cleanup.
- Capabilities roll out in backend-enforced stages.

## Domain state and overlays

The persisted task lifecycle is defined by subsystem 03. Current quality/delivery/attention information is represented as related durable records and a backend-derived view:

- lifecycle state controls legal transitions;
- pending protocol requests derive input/approval attention;
- latest validation has status and freshness;
- delivery has local/remote/PR/check/review status;
- Git has dirty/divergence/overlap status;
- runtime has container/process/connection/recovery status.

The frontend receives one authoritative task projection containing lifecycle, overlays, and `allowed_actions`. It does not duplicate the transition rules.

## Subsystem specifications

### 01 — Template bootstrap and runtime topology

[Specification](spec/2026-07-31-01-template-bootstrap-runtime-topology-design.md)

Owns template adoption, application placement, development/operational topology, support services, one-worker rule, and bootstrapping acceptance.

### 02 — Repository registry, configuration, and diagnostics

[Specification](spec/2026-07-31-02-repository-registry-configuration-diagnostics-design.md)

Owns canonical repository identity, strict `.techletes/cockpit.yaml`, roots/trust inputs, static/active diagnostics, instructions, and required tool/version checks.

### 03 — Task domain, PostgreSQL persistence, state, and locking

[Specification](spec/2026-07-31-03-task-domain-persistence-state-design.md)

Owns SQLModel entities, explicit lifecycle, atomic events, command idempotency, short-lived sessions, task locks, and global semaphores.

### 04 — Git worktrees, branches, overlap, and safe removal

[Specification](spec/2026-07-31-04-git-worktrees-branches-concurrency-design.md)

Owns Techletes-compliant branch names, remote-base worktree creation, NUL-safe status/diff, divergence, overlap evidence, synchronization advice, and host-side safe worktree removal.

### 05 — Devcontainer lifecycle and Docker isolation

[Specification](spec/2026-07-31-05-devcontainer-runtime-isolation-design.md)

Owns official CLI configuration/up/exec, runtime identity, reuse/rebuild, Compose/resource diagnostics, caches/volumes/ports, and exact runtime stop/control.

### 05a — Linked-worktree Git metadata mount compatibility

[Specification](spec/2026-07-31-05a-linked-worktree-git-metadata-mount-design.md)

Owns the additional canonical Git common-directory mount, container Git readiness, per-repository metadata locks, hooks/signing diagnostics, shared-metadata audit, and cleanup ordering.

### 06 — Process supervision and JSON-RPC transport

[Specification](spec/2026-07-31-06-process-supervisor-jsonrpc-transport-design.md)

Owns child process/pipes, bounded diagnostics/queues, framing, request correlation, server requests, transport lifecycle, and process registry.

### 07 — Codex app-server core

[Specification](spec/2026-07-31-07-codex-app-server-core-design.md)

Owns pinned generated protocol schemas, initialization/capabilities, thread/turn operations, exact IDs, event normalization, delta coalescing, and fake app-server.

### 08 — Codex auth, skills, context, and permissions

[Specification](spec/2026-07-31-08-codex-auth-skills-permissions-design.md)

Owns shared authenticated `CODEX_HOME`, trust implications, account diagnostics, Techletes skill roots/listing, deterministic task context, execution profiles, and approval-profile acceptance.

### 09 — Interactive turn control

[Specification](spec/2026-07-31-09-interactive-turn-control-design.md)

Owns durable clarification/approval requests, exact response delivery, follow-up, steering, interruption, graceful stop/resume, force-stop, races, and interaction audit.

### 10 — Events, reconnect, and recovery

[Specification](spec/2026-07-31-10-events-reconnect-recovery-design.md)

Owns database-first events, Redis wakeups, cursor WebSocket replay/backpressure, backend instance identity, exact orphan detection, thread-history reconciliation, and recovery outcomes.

### 11 — Validation, review, and commit

[Specification](spec/2026-07-31-11-validation-review-commit-design.md)

Owns strict repository validation profiles, mutation/freshness, artifacts, safe diffs, secret warnings, exact staging, hook/signing-respecting local commit, and Git-in-container prerequisite.

### 12 — GitHub delivery lifecycle

[Specification](spec/2026-07-31-12-github-delivery-lifecycle-design.md)

Owns issue snapshot intake, host Git push, explicit force-with-lease, idempotent draft PR, CI/review polling, external divergence, and failure/review context.

### 13 — Dashboard UX and notifications

[Specification](spec/2026-07-31-13-dashboard-ux-notifications-design.md)

Owns generated-client/service architecture, three-pane dashboard, event client, repository/task flows, interactions, review/validation/delivery/runtime panels, accessibility, and private notifications.

### 14 — Security, operations, and cleanup

[Specification](spec/2026-07-31-14-security-operations-cleanup-design.md)

Owns trust, RBAC, origin/CSRF/CORS, command/path/env policy, redaction/secret scan, audit, quotas, retention, staged cleanup, branch deletion, same-origin build, and WSL service.

### 15 — Test harness, rollout, and release

[Specification](spec/2026-07-31-15-test-harness-rollout-release-design.md)

Owns the strict scenario harness, compatibility and fault matrix, backend/browser golden paths, real acceptance, rollout gates, release evidence, backup, and rollback.

## Cross-subsystem contracts

### Snapshot types

Long-running async code consumes immutable snapshots/dataclasses, not live SQLModel session objects. Every external operation takes exact IDs/versions/SHAs/fingerprints.

### Operation pattern

```text
validate + authorize + acquire locks
-> persist intent/event
-> perform external action outside DB transaction
-> inspect authoritative external result
-> persist result/state/event
-> publish event ID
```

No ambiguous external action is automatically retried unless its child contract proves idempotency and exact state is inspected first.

### Lock hierarchy

To prevent deadlock, acquire in this order and release as soon as possible:

1. host single-instance ownership (process lifetime);
2. global quota/semaphore reservation;
3. task operation lock;
4. repository Git metadata lock when required;
5. Codex-home mutation lock only for global home changes;
6. short database transaction;
7. external process operation outside database transaction.

Child plans must not introduce an inverse order.

### Identifiers

Persist exact:

- repository and Git common-dir identity;
- task/workspace/branch/base/head;
- container and task labels;
- app-server session generation;
- thread/turn/item/request IDs;
- event/recovery/audit IDs;
- validation profile/config/status hashes;
- review snapshot and commit SHA;
- remote branch/PR/check/review identifiers.

Never correlate by title, prompt text, process name alone, short container ID, or directory naming alone.

### Error model

Every subsystem returns stable machine code, safe user summary, and optional diagnostic reference. Raw stack traces, stderr, protocol payloads, environment values, local credential details, and unlimited external content are not public API errors.

### Generated artifacts

Generated files are version-controlled and drift-checked:

- Codex app-server schemas and compatibility manifest;
- Alembic migrations;
- OpenAPI client;
- TanStack route tree if generated;
- i18n key parity;
- compatibility and release evidence checksums.

## Product non-goals

The MVP does not provide:

- merge, auto-merge, or production deployment;
- public/multi-tenant remote service;
- arbitrary coding-agent/plugin marketplace;
- autonomous multi-agent collaboration within one task;
- automatic CI/review repair loops;
- automatic semantic conflict resolution;
- unrestricted agent host/Docker access;
- background work while Windows/WSL is suspended;
- transparent continuation of an in-flight turn after backend process death.

## Master acceptance

The product is ready for internal rollout only when:

- current full-stack template bootstrap and one-worker WSL service are reproducible;
- two concurrent real tasks have isolated branches, worktrees, containers, mutable state, app-server connections, and threads;
- linked-worktree Git works in both devcontainers;
- required Techletes skills/auth/permission profiles are verified;
- questions/approvals are answered exactly once from browser;
- browser reconnect works and backend restart recovers conservatively;
- validation/review/commit and draft PR delivery are explicit and evidence-based;
- overlap/divergence warnings work;
- cleanup cannot lose unreviewed work or unrelated resources;
- security/adversarial/chaos/golden-path tests and real acceptance pass;
- no prohibited merge/deploy/broad cleanup/bypass code path exists;
- release evidence, backup, rollback, onboarding, operations, and known limitations are reviewed.
