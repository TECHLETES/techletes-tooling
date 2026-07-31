# Techletes Engineering Cockpit — Master Implementation Roadmap

> **For the primary implementation agent:** Start here, then read the matching child specification and implementation plan before each subsystem. Use `techletes-superpowers:using-superpowers` to select the workflow. For implementation, use `techletes-superpowers:subagent-driven-development` where available or `techletes-superpowers:executing-plans`. Do not execute the historical monolithic implementation plan.

## Goal

Implement the Engineering Cockpit from the current `TECHLETES/full-stack-template` as a sequence of independently reviewable subsystem contracts, with early proof of the riskiest Dev Container/Codex boundaries and no delivery capability enabled before isolation, recovery, and security are proven.

## Authoritative documents

- [Master specification](00-engineering-cockpit-master-specification.md)
- Child specs: `spec/2026-07-31-<id>-*.md`
- Child implementation plans: `implementation/2026-07-31-<id>-*.md`
- [Planning index](INDEX.md)

Historical broad files are reference only and must not drive execution.

## Bootstrap rule

Before any cockpit feature code:

1. inspect the current `TECHLETES/full-stack-template` main branch and its `AGENTS.md`;
2. copy/adopt the template into `apps/engineering-cockpit/` following subsystem 01;
3. preserve and adapt its actual current backend/frontend/devcontainer/Compose/CI structure;
4. run the inherited preflight before the first feature commit;
5. never create a second competing application scaffold beside the template layout.

## Dependency graph

```text
01 Template/bootstrap/runtime topology
 ├── 02 Repository registry/config/diagnostics
 ├── 03 Task domain/PostgreSQL/state/locks
 │    └── 04 Git worktrees/branches/overlap
 │         └── 05 Devcontainer lifecycle/isolation
 │              └── 05a Linked-worktree Git metadata mount
 │                   └── 06 Process supervisor/JSON-RPC transport
 │                        └── 07 Codex app-server core
 │                             └── 08 Codex auth/skills/permissions
 │                                  └── 09 Interactive turn control
 │                                       └── 10 Events/reconnect/recovery
 │                                            ├── 11 Validation/review/commit
 │                                            │    └── 12 GitHub delivery
 │                                            └── 13 Dashboard UX/notifications
 │                                                 └── 14 Security/ops/cleanup
 └─────────────────────────────────────────────────────└── 15 Test/rollout/release
```

This diagram shows the primary path. Some later tasks can be parallelized after their contracts stabilize; the execution phases below define safe review boundaries.

## Contract-first rules

For each subsystem:

1. read its specification completely;
2. inspect current implemented dependencies and template conventions;
3. execute child plan tasks in order unless the plan explicitly allows parallelism;
4. write failing tests before behavior where the child plan requires them;
5. commit at the child plan's commit boundaries;
6. run the subsystem exit checks;
7. review public interfaces against downstream child documents;
8. update a child document only through a reviewed planning change if implementation research invalidates an assumption;
9. do not silently weaken security, isolation, recovery, approval, or delivery boundaries to make a test pass.

## Phase 0 — Research locks and bootstrap

### Subsystem 01

- [Specification](spec/2026-07-31-01-template-bootstrap-runtime-topology-design.md)
- [Plan](implementation/2026-07-31-01-template-bootstrap-runtime-topology-implementation-plan.md)

Deliverables:

- template-derived application under `apps/engineering-cockpit/`;
- inherited Postgres/Redis/auth/RBAC/devcontainer/frontend conventions;
- host-native WSL one-worker operational launcher;
- development/production path translation contract;
- baseline preflight and bootstrap evidence.

Gate:

- clean template-derived app runs in development;
- host-native backend can reach support services;
- second operational instance is refused;
- no feature-specific parallel scaffold exists.

## Phase 1 — Durable control-plane foundation

### Subsystem 02 — Repository registry/config/diagnostics

- [Spec](spec/2026-07-31-02-repository-registry-configuration-diagnostics-design.md)
- [Plan](implementation/2026-07-31-02-repository-registry-configuration-diagnostics-implementation-plan.md)

### Subsystem 03 — Task domain/state/persistence/locking

- [Spec](spec/2026-07-31-03-task-domain-persistence-state-design.md)
- [Plan](implementation/2026-07-31-03-task-domain-persistence-state-implementation-plan.md)

### Subsystem 04 — Git worktrees/branches/overlap

- [Spec](spec/2026-07-31-04-git-worktrees-branches-concurrency-design.md)
- [Plan](implementation/2026-07-31-04-git-worktrees-branches-concurrency-implementation-plan.md)

Recommended execution:

- 02 and 03 may begin after 01 and can be reviewed in parallel only if shared `backend/models.py` migrations are coordinated.
- 04 begins after repository snapshots, task locks, and persistence interfaces are stable.

Gate:

- repository can be registered/diagnosed under WSL roots;
- task state/event/idempotency rules are durable in Postgres;
- two host worktrees can be created from exact fetched base SHAs;
- overlap/divergence and unsafe removal tests pass;
- no devcontainer or Codex is involved yet.

## Phase 2 — Runtime and Git-in-container technical proof

### Subsystem 05 — Devcontainer lifecycle/isolation

- [Spec](spec/2026-07-31-05-devcontainer-runtime-isolation-design.md)
- [Plan](implementation/2026-07-31-05-devcontainer-runtime-isolation-implementation-plan.md)

### Subsystem 05a — Linked-worktree Git metadata mount

- [Spec](spec/2026-07-31-05a-linked-worktree-git-metadata-mount-design.md)
- [Plan](implementation/2026-07-31-05a-linked-worktree-git-metadata-mount-implementation-plan.md)

Execution order is strict: complete 05's CLI/runtime contracts, then 05a, then rerun 05's two-worktree acceptance with Git commands inside both containers. Subsystem 05 is not considered fully accepted until 05a passes.

Gate:

- pinned Dev Container CLI reads/starts/reuses both task configurations;
- no rebuild on normal resume;
- distinct containers and mutable volumes;
- shared caches only where approved;
- exact Git common-dir mount exists in both containers;
- status/hooks/signing diagnostics work inside each container;
- stopping/removing one runtime does not affect the other.

This is the first major go/no-go checkpoint. Do not continue to app-server implementation if this gate fails.

## Phase 3 — App-server transport and protocol proof

### Subsystem 06 — Process supervision/JSON-RPC

- [Spec](spec/2026-07-31-06-process-supervisor-jsonrpc-transport-design.md)
- [Plan](implementation/2026-07-31-06-process-supervisor-jsonrpc-transport-implementation-plan.md)

### Subsystem 07 — Codex app-server core

- [Spec](spec/2026-07-31-07-codex-app-server-core-design.md)
- [Plan](implementation/2026-07-31-07-codex-app-server-core-implementation-plan.md)

### Subsystem 08 — Auth/skills/permissions

- [Spec](spec/2026-07-31-08-codex-auth-skills-permissions-design.md)
- [Plan](implementation/2026-07-31-08-codex-auth-skills-permissions-implementation-plan.md)

Gate:

- exact pinned Codex schema generated/committed/reproducible;
- app-server process opens over stdio and all queues/output are bounded;
- initialize/thread/turn/terminal event works through fake and real disposable target;
- shared `CODEX_HOME` supports two concurrent threads or release is blocked;
- required Techletes skills are configured/listed after every process start;
- permission profile matrix proves expected approvals/denials;
- no TUI/tmux/protocol guessing path exists.

This is the second major go/no-go checkpoint.

## Phase 4 — Interactive orchestration and recovery

### Subsystem 09 — Interactive turn controls

- [Spec](spec/2026-07-31-09-interactive-turn-control-design.md)
- [Plan](implementation/2026-07-31-09-interactive-turn-control-implementation-plan.md)

### Subsystem 10 — Events/reconnect/recovery

- [Spec](spec/2026-07-31-10-events-reconnect-recovery-design.md)
- [Plan](implementation/2026-07-31-10-events-reconnect-recovery-implementation-plan.md)

Gate:

- clarification/approval persists before notify and resolves exactly once;
- follow-up/steer/interrupt/stop/resume/force-stop semantics pass race tests;
- browser disconnect does not affect the child process;
- event replay works through Redis loss/slow consumer/retention reset;
- backend hard restart never claims old stdio ownership;
- exact tagged orphan handling and thread-history reconciliation pass;
- lost in-flight turn becomes `RECOVERY_REQUIRED` without replay.

At this gate, Stage 1 read-only internal analysis may begin for approved developers/repositories, subject to subsystem 14 security controls being applied before any broader rollout.

## Phase 5 — Quality and explicit local delivery

### Subsystem 11 — Validation/review/commit

- [Spec](spec/2026-07-31-11-validation-review-commit-design.md)
- [Plan](implementation/2026-07-31-11-validation-review-commit-implementation-plan.md)

Gate:

- validation commands come only from strict repository config;
- mutation/freshness and artifacts are durable;
- review endpoints are path-safe and escaped;
- secret findings block delivery;
- exact selected-path commit runs inside task devcontainer;
- hooks and signing are respected;
- local commit is verified by head/parent/path evidence.

At this gate, Stage 2 local-development rollout may begin after security review.

## Phase 6 — GitHub issue-to-draft-PR lifecycle

### Subsystem 12

- [Spec](spec/2026-07-31-12-github-delivery-lifecycle-design.md)
- [Plan](implementation/2026-07-31-12-github-delivery-lifecycle-implementation-plan.md)

Gate:

- issue preview/snapshot treats content as untrusted data;
- push is SHA-safe and no-force by default;
- force-with-lease is separate/confirmed/audited;
- draft PR creation is idempotent after ambiguous result;
- CI/review polling respects rate limits and external divergence;
- no merge/auto-merge/deploy endpoint or invocation exists.

At this gate, Stage 3 draft-PR delivery may begin for a disposable repository, then approved internal repositories.

## Phase 7 — Integrated browser product

### Subsystem 13

- [Spec](spec/2026-07-31-13-dashboard-ux-notifications-design.md)
- [Plan](implementation/2026-07-31-13-dashboard-ux-notifications-implementation-plan.md)

The shell/event-client/service-layer foundation may begin once backend API schemas from 02–10 stabilize. Detailed review/delivery panels wait for 11/12.

Gate:

- authenticated three-pane UI operates two tasks without separate terminals;
- backend-derived `allowed_actions` controls every action;
- WebSocket cursor/instance/replay behavior is correct;
- requests, changes, validation, commit, delivery, runtime, and recovery are accessible and integrated;
- notifications are opt-in, private, and deduplicated;
- keyboard, responsive, and accessibility suites pass.

## Phase 8 — Security, operations, and cleanup hardening

### Subsystem 14

- [Spec](spec/2026-07-31-14-security-operations-cleanup-design.md)
- [Plan](implementation/2026-07-31-14-security-operations-cleanup-implementation-plan.md)

Security controls such as trust and authorization should be introduced as early as their dependent routes exist; the phase gate represents complete hardening, not the first security work.

Gate:

- repository trust/fingerprint blocks changed/untrusted code;
- RBAC/origin/CSRF/CORS/WebSocket security passes;
- command/path/environment policy and redaction/secret scan are centralized;
- audit, quotas, retention, cleanup, branch deletion, and exact-resource identity pass adversarial/chaos tests;
- built frontend is same-origin/loopback-only;
- WSL user service runs one worker and restarts into recovery;
- no global cleanup or root service.

## Phase 9 — Full-system proof and staged release

### Subsystem 15

- [Spec](spec/2026-07-31-15-test-harness-rollout-release-design.md)
- [Plan](implementation/2026-07-31-15-test-harness-rollout-release-implementation-plan.md)

Some test-harness tasks begin earlier: the unified scenario models/fakes should replace subsystem-specific fakes as soon as interfaces stabilize. Final golden paths, chaos matrix, real acceptance, rollout rehearsal, evidence, and release gates occur here.

Gate:

- all child exit criteria complete;
- complete test/compatibility matrix has evidence;
- fake-tool CI and real local acceptance pass;
- two concurrent real Codex tasks pass all identity/isolation checks;
- reconnect/recovery, validation/commit, issue/push/draft PR, overlap, and cleanup pass;
- threat model reviewed by second Techletes developer;
- backup and rollback rehearsed;
- Stage 0–3 rollout rehearsal succeeds;
- Stage 4 internal release approved.

## Safe parallelism during implementation

After interfaces stabilize, these task groups can run in parallel in separate development worktrees:

- backend repository diagnostics (02) and task-domain persistence (03), coordinated around models/migrations;
- frontend event-client shell (13 tasks 1–6) while backend detail APIs (11/12) finish;
- security tests/policies (14 tasks 1–5) alongside late feature routes, provided route owners integrate them before merge;
- scenario harness foundations (15 tasks 1–5) while subsystem fakes are still being built;
- documentation and compatibility matrix after exact commands/versions are proven.

Do not parallelize overlapping changes to:

- `backend/models.py` migrations without one integration owner;
- `backend/main.py` lifespan/runtime context;
- generated Codex schema/client artifacts;
- task transition map;
- Dev Container adapter launch argv;
- cleanup/recovery state machines;
- generated frontend client/route tree.

## Integration review checkpoints

After every phase:

1. compare implemented public interfaces with all downstream specs;
2. run one Alembic-head check;
3. regenerate/check Codex schema and OpenAPI client where touched;
4. run security/path/redaction smoke tests;
5. inspect prohibited command journal for merge/deploy/global cleanup/bypass flags;
6. update compatibility/known limitations only with evidence;
7. merge only after phase gate review.

## Prohibited shortcuts

An implementation is rejected if it:

- starts Codex directly on WSL instead of inside the task devcontainer;
- uses terminal/TUI text to infer task/request state;
- uses tmux as the app-server protocol;
- runs multiple operational Uvicorn workers;
- uses SQLite for control-plane state;
- rebuilds on resume;
- omits the linked-worktree Git metadata mount;
- copies guessed Codex credential files;
- auto-approves or retries an ambiguous protocol request;
- retries a lost in-flight turn automatically;
- accepts arbitrary browser/model commands or paths;
- uses `git add .`, `--no-verify`, plain `--force`, broad Docker filters/prune, or recursive worktree deletion;
- merges, enables auto-merge, or deploys;
- marks unknown CI/review evidence ready;
- exposes non-loopback service or secrets in logs/events/notifications/PR body;
- calls a phase complete without its real/manual acceptance gate.

## Overall definition of done

Implementation is complete only when the master acceptance criteria in the master specification and all child plan exit criteria are met, the complete subsystem 15 release checklist/evidence is approved, and the product is promoted to the intended rollout stage through backend-enforced policy.
