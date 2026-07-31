# 15 — Deterministic Test Harness, Acceptance Matrix, Rollout, and Release Specification

## Purpose

Define how the Engineering Cockpit is proven safe and useful before it controls real repositories, credentials, containers, and GitHub delivery. This subsystem turns the preceding fourteen subsystem contracts into one executable verification strategy, release evidence package, staged rollout, and rollback procedure.

The test architecture must exercise real process, pipe, filesystem, database, WebSocket, and recovery boundaries. It may replace external products with deterministic fake executables, but it must not bypass the adapters or transport being tested.

## Verification principles

1. **Fakes at external boundaries, not inside domain services.** Git, Dev Container CLI, Docker, Codex app-server, and GitHub CLI fakes run as child processes or API-compatible adapters so command construction, stdio, timeouts, parsing, and cancellation remain under test.
2. **Real PostgreSQL and Redis in integration tests.** Persistence, transactions, replay, locking, and recovery are not validated against SQLite or in-memory substitutes.
3. **Exact-version contract suites.** Supported Git, Docker, Dev Container CLI, Codex, app-server schema, GitHub CLI, PostgreSQL, Redis, Python, Bun, and browser versions are recorded and tested.
4. **Fault injection around durable boundaries.** Every flow is tested for failure before intent persistence, after intent persistence, during external execution, after external success but before result persistence, and during recovery.
5. **Disposable real acceptance.** Real Codex/GitHub tests use disposable branches, worktrees, devcontainers, issues, and draft pull requests in a non-production Techletes repository.
6. **No credentials in CI.** CI uses fakes and generated protocol fixtures. Real authenticated acceptance is an explicit local release gate.
7. **No inferred success.** Assertions use exact Git SHAs, container IDs/labels/mounts, app-server thread/turn IDs, event IDs, request IDs, validation snapshots, and PR head SHAs.
8. **Evidence is retained.** Each release records versions, schema hashes, commands, outcomes, known limitations, and manual sign-off without retaining secrets.

## Test pyramid

### Unit tests

Pure or narrowly scoped behavior:

- state transitions and derived actions;
- configuration parsing and fingerprints;
- branch/ref/path validation;
- Git porcelain, app-server schema, and GitHub JSON normalization;
- event ordering and coalescing;
- permission profiles and context assembly;
- overlap, validation freshness, delivery readiness, recovery planning, cleanup planning;
- redaction, quotas, retention, and UI reducers/services.

Unit tests do not shell out unless testing a parser against a checked-in fixture.

### Adapter contract tests

Exercise the same public adapter interface used in production:

- real temporary Git repositories and worktrees;
- fake `devcontainer` executable;
- fake Docker inspection adapter/CLI;
- fake app-server child process over stdio;
- fake `gh` executable and fake remote Git repository;
- fake editor command;
- real filesystem permission/path/symlink behavior.

Each fake records argv, cwd, selected environment names, stdin messages, timing, and scenario state. It never logs secret environment values.

### Backend integration tests

Run FastAPI against real disposable PostgreSQL and Redis support services with fake external tools. Cover complete task flows through HTTP/WebSocket APIs, database commits, event fan-out, process supervision, and recovery.

### Frontend component tests

Use Vitest, Testing Library, mocked typed services, and a deterministic WebSocket harness for accessibility, forms, allowed actions, event cursor behavior, stale commands, safe rendering, and notifications.

### Browser end-to-end tests

Run Playwright against the full built application plus real PostgreSQL/Redis and fake external tools. Browser tests verify the user workflow and generated client contract, not only component rendering.

### Real local acceptance tests

Run from WSL with Docker Desktop integration, real Dev Container CLI, real pinned Codex app-server, authenticated `CODEX_HOME`, host Git/GitHub CLI, and a disposable Techletes repository.

## Unified scenario harness

All fake external tools use one versioned scenario format under:

```text
backend/tests/cockpit/fakes/scenarios/
```

A scenario contains:

```yaml
version: 1
name: two-task-success
initial:
  git: {}
  docker: {}
  devcontainer: {}
  app_server: {}
  github: {}
steps:
  - expect:
      tool: devcontainer
      argv: [up, --workspace-folder, "${WORKTREE_A}"]
    result:
      exit_code: 0
      stdout_fixture: devcontainer/up-a.jsonl
  - expect:
      tool: app_server
      request_method: initialize
    result:
      response_fixture: app-server/initialize.json
faults: []
assertions: []
```

Requirements:

- strict schema validation and scenario version;
- deterministic variable substitution from a test-owned context only;
- explicit expected invocation order or declared concurrency groups;
- no arbitrary Python/shell execution embedded in scenarios;
- reusable response fixtures generated from supported external schemas;
- fault steps for delay, timeout, process exit, malformed output, connection close, duplicate event, and ambiguous external success;
- one append-only invocation journal for assertions and debugging;
- secret values replaced by test tokens and redacted in failure output.

Fakes must fail on an unexpected command or message. A fake that accepts anything would hide adapter drift.

## Compatibility matrix

The release evidence records:

| Component | Supported/tested value |
| --- | --- |
| Windows | Current Techletes Windows 11 baseline |
| WSL | Ubuntu distribution and kernel version |
| Docker Desktop/Engine | Exact tested versions |
| Git | Minimum and exact acceptance version |
| Dev Container CLI | Pinned supported range |
| Codex CLI/app-server | Exact pinned version |
| App-server schema | Manifest SHA-256 |
| GitHub CLI | Tested supported range |
| Python | Template-pinned version |
| uv | Template-pinned version |
| Bun/Node | Template-pinned versions |
| PostgreSQL | Template version |
| Redis | Template version |
| Browsers | Playwright Chromium plus supported daily browser |

An unrecognized app-server version is blocked. Other tool versions follow their subsystem's compatibility policy. Updating a version requires its contract suite, generated artifacts, manual acceptance where applicable, and compatibility matrix change in the same PR.

## Required scenario matrix

### Repository and Git

- repository path under WSL with spaces and Unicode;
- invalid `/mnt/c`, symlink escape, wrong remote, missing base branch;
- two tasks from one repository and tasks across two repositories;
- no overlap, same file/different hunk, same hunk, delete/edit, binary, lockfile, migration conflict;
- remote base advancing and external branch push;
- dirty, conflicted, unpushed, pushed, merged, squash-merged, protected branch cleanup.

### Devcontainer and Docker

- first create, reuse, stopped, missing, drifted, explicit rebuild;
- initialize/post-create/post-start failure and timeout;
- fixed `container_name`, project name, host port, external volume, Docker socket, privileged/host mount;
- two worktrees with distinct containers, mutable volumes, and dynamic ports;
- shared caches only;
- linked-worktree Git common-directory mount and Git commands inside both containers;
- target remote user other than `vscode`;
- runtime stop/removal identity mismatch.

### Process and app-server

- initialize, capability matrix, thread start/resume/read, turn start/completion;
- message, command, file-change, diff, usage, warning, and error events;
- clarification, command approval, file approval, multiple pending requests;
- follow-up, steering, interruption, graceful stop/resume, force-stop;
- malformed/oversized JSON, stderr flood, response reordering, backpressure;
- process exit before/after external result;
- unknown notification versus unknown request;
- unsupported Codex version/schema drift;
- shared `CODEX_HOME` with two concurrent app-server processes.

### Events and recovery

- browser close/reopen while task continues;
- duplicate/gapped/reordered Redis envelopes;
- Redis unavailable and later replay;
- slow WebSocket consumer and retention reset;
- graceful backend restart and hard kill;
- tagged orphan app-server, untagged manual Codex process, ambiguous orphan;
- container stopped/missing/mismatched;
- thread history gains terminal event after crash;
- lost in-flight turn and unresolved approval;
- crash after every recovery stage and idempotent rerun.

### Validation, review, and delivery

- validation pass/fail/timeout/cancel/retry;
- expected and unexpected workspace mutation;
- stale validation after edit/commit/config change;
- safe diff/binary/oversized/generated/sensitive content;
- hooks and commit signing success/failure;
- exact-path subset/all commit;
- issue open/closed/changed/oversized/untrusted content;
- first/idempotent/diverged push and force-with-lease;
- PR create success/existing/ambiguous result;
- checks pending/success/failure/cancelled/action required/unknown;
- review approved/changes requested/required;
- external head/base/PR state changes;
- no merge, auto-merge, or deployment call.

### Security and operations

- owner/RBAC isolation and unauthorized event replay;
- CSRF/origin/CORS/WebSocket-origin;
- path/ref/argv/env injection and malicious lifecycle configuration;
- prompt injection/XSS/ANSI/secret leakage;
- quota, disk, log, artifact, event, queue, and process limits;
- trust fingerprint change;
- retention boundaries;
- cleanup stage crashes, exact-resource survival, force and volume confirmations;
- one-worker/one-instance service lock and WSL service restart.

## Fault-injection checkpoints

Every external operation is modeled as:

```text
validate preconditions
-> persist intent
-> invoke external action
-> externally complete or fail
-> inspect resulting truth
-> persist result/state/event
-> publish event
```

The harness can stop/crash/fail at each arrow. For every mutation, tests answer:

- what durable evidence exists;
- whether repeating is safe;
- how reconciliation distinguishes not-started, unknown, and completed;
- whether unrelated resources remain untouched;
- what the user sees after reconnect.

Failpoints are enabled only in test builds through dependency injection. Production cannot activate arbitrary named failpoints through a public endpoint.

## Golden vertical-slice scenarios

### Golden path A — one manual task

```text
register/trust repository
-> create task
-> worktree
-> devcontainer
-> app-server initialize
-> thread/turn
-> agent changes
-> clarification
-> validation
-> review
-> local commit
-> stop/retain
```

### Golden path B — two concurrent tasks

```text
same repository
-> separate branches/worktrees/containers/app-servers/threads
-> concurrent progress
-> overlap warning
-> one task completes/commits
-> second receives base/overlap warning
-> no cross-task files, events, requests, volumes, or process control
```

### Golden path C — GitHub delivery

```text
issue preview/snapshot
-> task implementation
-> passed delivery validation
-> exact commit
-> push
-> draft PR
-> pending/success/failure checks
-> review update
-> explicit follow-up repair context
-> no automatic merge
```

### Golden path D — reconnect and recovery

```text
active task
-> browser closes/reopens and replays
-> backend is killed
-> new instance detects exact orphan
-> resumes thread/read history
-> terminal or lost-in-flight outcome
-> user reviews and explicitly continues
```

### Golden path E — cleanup

```text
completed/delivered task
-> cleanup assessment
-> stop exact runtime
-> remove worktree
-> preserve volumes/history by default
-> optional separately confirmed branch/runtime/volume cleanup
-> unrelated resources survive
```

## Real acceptance repository

Use a disposable repository created from the **current** `TECHLETES/full-stack-template`, or a dedicated internal cockpit acceptance repository regularly refreshed from it.

Requirements:

- non-production GitHub repository and base branch;
- no real client data/secrets;
- a small controlled issue set;
- template devcontainer with Git-common-dir compatibility;
- CI fast enough for repeated release tests;
- test cleanup procedure;
- repository owner approval before force-with-lease or branch deletion tests.

Real acceptance must not run against the cockpit planning/tooling repository's main branch.

## Manual release acceptance

An operator records evidence for:

1. fresh WSL clone/install/bootstrap from the full-stack template;
2. support services and one-worker backend start;
3. repository diagnostics and trust approval;
4. two concurrent real Codex tasks in one repository;
5. separate worktrees, containers, mutable volumes, app-server processes, and thread IDs;
6. required Techletes skill discovery;
7. clarification and approval resolved from browser;
8. browser close/reopen without task interruption;
9. backend restart with conservative recovery;
10. validation, safe review, hooks/signing, local commit;
11. issue snapshot, push, draft PR, CI/review monitoring;
12. overlap/base-divergence warning;
13. normal cleanup and unrelated-resource survival;
14. service restart and loopback/network verification.

Evidence captures IDs/hashes in sanitized form, timestamps, versions, screenshots where useful, and pass/fail notes. It does not capture prompts, secrets, source diffs, tokens, or credential files unless a specific approved test needs sanitized synthetic content.

## Rollout stages

### Stage 0 — Protocol and runtime spike

Audience: implementers only.

Enabled:

- repository diagnostics;
- worktree/devcontainer/app-server initialize/thread/turn against fake and disposable repositories;
- activity events.

Disabled:

- authenticated real repository delivery;
- commit/push/PR;
- cleanup beyond disposable resources.

Gate: subsystems 01–10 technical proofs and no unresolved protocol/runtime blocker.

### Stage 1 — Read-only/internal analysis

Audience: one or two Techletes developers.

Enabled:

- trusted repository registration;
- analysis profile;
- real app-server turns;
- questions/interrupt/stop/recovery;
- Git status/diff review.

Disabled:

- workspace-write profiles unless explicitly enabled per repository;
- commit/push/PR;
- force operations.

Gate: shared-home, two-worktree, reconnect/recovery, security-origin/RBAC acceptance.

### Stage 2 — Local development

Enabled:

- development/dependency profiles;
- validation;
- explicit local commit;
- guarded cleanup.

Disabled by default:

- push/PR except acceptance repository;
- force-with-lease and volume deletion except manager tests.

Gate: subsystem 11 and cleanup/security acceptance.

### Stage 3 — Draft PR delivery

Enabled:

- issue intake;
- push;
- draft PR;
- CI/review monitoring;
- ready/draft transitions.

Still disabled:

- merge, auto-merge, deployment, automatic CI repair.

Gate: subsystem 12, disposable GitHub acceptance, operational sign-off.

### Stage 4 — Team internal release

Audience: approved Techletes developers.

Enabled only for trusted onboarded repositories. Quotas and compatibility manifests remain enforced.

Gate: all subsystem exit criteria, full release checklist, security review, documented rollback, and owner approval.

Feature availability is controlled by backend settings and repository policy, not hidden frontend-only flags.

## Release gates

A release candidate is blocked unless:

- all subsystem implementation-plan exit criteria are complete;
- database migrations have one head and tested downgrade/upgrade;
- generated Codex schema/OpenAPI client/route tree/i18n files are current;
- unit/contract/integration/frontend/E2E/security suites pass;
- exact version compatibility matrix is current;
- real two-worktree Git/devcontainer/Codex acceptance passes;
- shared `CODEX_HOME` concurrency passes;
- approval profile matrix passes;
- browser reconnect and backend restart acceptance passes;
- validation/commit/GitHub delivery acceptance passes;
- cleanup chaos/adversarial tests pass;
- no merge/deploy code path exists;
- threat model/residual risks are reviewed by a second Techletes developer;
- operator, repository onboarding, troubleshooting, update, and rollback docs are complete.

## Release evidence package

Store under a release-specific, non-secret directory or attached CI artifact:

```text
release-evidence/<version>/
  compatibility.json
  automated-summary.json
  manual-acceptance.md
  security-review.md
  known-limitations.md
  migration-report.md
  rollback-test.md
  checksums.txt
```

Do not commit machine-specific local paths or sensitive logs to the public repository. The committed release notes link to internal evidence where needed.

## Backup and rollback

Before upgrade:

- stop/drain the control plane;
- backup PostgreSQL cockpit data;
- record current application version, migration head, compatibility manifests, and retained runtime/task list;
- do not remove worktrees, containers, branches, or volumes.

Rollback:

1. stop the new service;
2. restore the previous application build/config;
3. downgrade database only when the migration explicitly supports it and after backup; otherwise restore the database backup;
4. start one previous-version instance;
5. run read-only reconciliation/diagnostics before enabling mutations;
6. preserve `RECOVERY_REQUIRED` tasks for manual review.

Rollback never replays a model turn automatically and never deletes an incompatible new runtime. A failed upgrade can be abandoned while worktrees and commits remain available for manual use.

## Version update procedure

For Codex, Dev Container CLI, GitHub CLI, Docker, Git, Python/Bun/uv, PostgreSQL/Redis, or major dependencies:

1. open a dedicated update task/branch;
2. update the pinned version/manifest;
3. regenerate protocol/client artifacts;
4. run affected contract matrix;
5. run security/dependency review;
6. run real acceptance where the boundary changed;
7. document behavior/limitations and rollback;
8. do not combine unrelated major updates.

## Known-limitations policy

Known limitations must be explicit, reproducible, scoped to a compatibility manifest/release, and paired with mitigation. A limitation cannot silently weaken sandbox, approvals, auth, cleanup, or recovery guarantees.

## Acceptance criteria

- One scenario harness drives all fake external boundaries without bypassing production adapters.
- CI proves deterministic behavior without real credentials.
- Fault injection demonstrates idempotent/recoverable behavior around every external mutation.
- Golden paths pass through REST/WebSocket/UI using real PostgreSQL/Redis.
- Real local acceptance proves two concurrent task devcontainers/app-servers and GitHub draft delivery.
- Rollout gates keep risky capabilities disabled until their subsystem is proven.
- Release evidence and rollback procedure are complete and tested.

## Research basis

- [Pytest](https://docs.pytest.org/)
- [Playwright](https://playwright.dev/)
- [GitHub Actions security hardening](https://docs.github.com/en/actions/security-for-github-actions/security-guides/security-hardening-for-github-actions)
- [PostgreSQL backup and restore](https://www.postgresql.org/docs/current/backup.html)
- [OpenAI Codex app-server](https://github.com/openai/codex/blob/main/codex-rs/app-server/README.md)
- [Dev Container CLI](https://github.com/devcontainers/cli)
