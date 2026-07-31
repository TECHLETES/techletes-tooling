# Techletes Engineering Cockpit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `techletes-superpowers:subagent-driven-development` (recommended) or `techletes-superpowers:executing-plans` to implement this plan task-by-task. Track progress with the checkboxes in this document.

**Goal:** Build a WSL-hosted web cockpit that creates isolated Git worktrees, starts repository devcontainers, runs `codex app-server` inside them, relays structured interaction to a browser, validates changes, and supports explicit draft-PR delivery.

**Architecture:** Start from `TECHLETES/full-stack-template`. The FastAPI backend owns task lifecycle, Git/devcontainer subprocesses, one app-server JSON-RPC connection per active task, persistence, recovery, and WebSocket event replay. The React frontend renders server-owned state and resolves structured user-input/approval requests.

**Tech stack:** Use the current full-stack template versions and conventions. Expected components include FastAPI, Pydantic, SQLAlchemy/Alembic, SQLite for local persistence, asyncio subprocesses, React/TypeScript, the Dev Container CLI, Git, GitHub CLI/API, and Codex app-server.

## Global constraints

- Bootstrap from the current `TECHLETES/full-stack-template` before feature implementation.
- Inspect and follow all current template and repository `AGENTS.md` instructions.
- Keep the application under `apps/engineering-cockpit/` for now.
- Use Linux filesystem paths under WSL for repositories/worktrees.
- `.devcontainer/devcontainer.json` is the runtime source of truth.
- The backend must launch `codex app-server` inside the task devcontainer through `devcontainer exec`.
- Communicate through newline-delimited JSON-RPC over owned stdin/stdout pipes.
- Do not use terminal/TUI scraping, tmux, or the experimental app-server WebSocket transport as the primary integration.
- Persist exact thread, turn, item, event, and server-request identifiers.
- No automatic merge or deployment.
- Force operations and destructive cleanup require explicit approval.

---

## Task 1: Bootstrap the application from the full-stack template

**Files:**
- Populate: `apps/engineering-cockpit/` from the current `TECHLETES/full-stack-template`
- Preserve: template backend, frontend, devcontainer, CI, tests, typing, linting, and pre-commit files
- Update: `apps/engineering-cockpit/README.md`

**Interfaces:**
- Existing template health endpoints and frontend shell remain functional.
- Add no cockpit-specific architecture until the template baseline passes.

- [ ] Inspect the current template repository, default branch, `AGENTS.md`, setup scripts, devcontainer, and test commands.
- [ ] Copy/bootstrap the template into `apps/engineering-cockpit/`, excluding template Git history and project-specific generated state.
- [ ] Rename package/application identifiers consistently to `engineering-cockpit`.
- [ ] Open/build the inherited devcontainer.
- [ ] Run the complete inherited preflight without feature changes.
- [ ] Record exact backend/frontend paths and commands at the top of this plan if they differ from later assumptions.
- [ ] Commit: `feat: bootstrap engineering cockpit from full-stack template`.

## Task 2: Add persistent domain models and task transitions

**Files:**
- Create/modify according to template layout: domain enums, SQLAlchemy models, migration, and tests

**Interfaces:**
- `TaskState` includes all states from the specification.
- Models: repository, task, workspace, agent session, protocol request, event, validation, pull request.
- `assert_transition(current, target)` rejects invalid transitions.

- [ ] Write failing tests for model creation, relationships, event ordering, and valid/invalid transitions.
- [ ] Implement async database/session setup using the template's existing patterns.
- [ ] Add the initial migration.
- [ ] Run migration and focused tests.
- [ ] Commit: `feat: add cockpit task persistence`.

## Task 3: Implement safe subprocess ownership

**Files:**
- Add process runner, process registry, output capture, redaction, and tests in template-appropriate locations

**Interfaces:**
- `ProcessRunner.run(...) -> ProcessResult`
- `ProcessRunner.spawn(...) -> OwnedProcess`
- `OwnedProcess` exposes stdin writer, stdout/stderr async iterators, wait, terminate, and kill.
- `ProcessRegistry` correlates known child processes to task/session IDs.

- [ ] Write tests for exit status, streaming, stdin writes, timeout, cancellation, graceful termination, force kill, and orphan metadata.
- [ ] Implement with asyncio subprocess APIs and argument arrays; no `shell=True`.
- [ ] Sanitize command metadata and output before persistence.
- [ ] Commit: `feat: add owned subprocess runtime`.

## Task 4: Register and diagnose repositories

**Interfaces:**
- Repository CRUD/list endpoints.
- `RepositoryDiagnostics` reports Git, remote, base branch, devcontainer config, Codex/app-server, auth status, and required binary versions.

- [ ] Write API tests against a temporary Git repository.
- [ ] Parse `.techletes/cockpit.yaml` with strict versioned schemas.
- [ ] Validate absolute WSL/Linux paths and reject unsupported/missing inputs clearly.
- [ ] Detect `git`, `gh`, `docker`, `devcontainer`, and `codex` versions.
- [ ] Detect whether `codex app-server` is available without exposing credentials.
- [ ] Commit: `feat: add repository registry and diagnostics`.

## Task 5: Implement Git worktree lifecycle

**Interfaces:**
- `fetch(repository_path)`
- `create_worktree(repository_path, worktree_path, branch_name, base_ref)`
- `status(worktree_path)`
- `diff(worktree_path)`
- `remove_worktree(repository_path, worktree_path, force=False)`

- [ ] Contract-test against temporary bare/local repositories.
- [ ] Create branches from explicit remote base refs.
- [ ] Return typed conflicts for duplicate branch/path.
- [ ] Refuse dirty, unpushed, or otherwise unsafe removal by default.
- [ ] Persist head SHA and worktree metadata.
- [ ] Commit: `feat: add git worktree adapter`.

## Task 6: Create tasks and provision workspaces

**Interfaces:**
- Create/list/detail/start task API.
- Deterministic collision-safe task slug and branch naming.

- [ ] Test manual prompts, presets, and GitHub issue references.
- [ ] Fetch the base branch before worktree creation.
- [ ] Persist every lifecycle transition and event.
- [ ] Move failures to `FAILED` with sanitized diagnostics.
- [ ] Stop the first implementation at a prepared worktree.
- [ ] Commit: `feat: provision isolated task worktrees`.

## Task 7: Implement the Dev Container CLI adapter

**Interfaces:**
- `up(workspace_folder, rebuild=False) -> DevcontainerInfo`
- `exec_process(workspace_folder, command, env=None) -> OwnedProcess`
- `inspect(workspace_folder) -> DevcontainerInfo | None`
- `stop(workspace_folder)`

- [ ] Create a fake `devcontainer` executable for contract tests.
- [ ] Test first start, reuse, explicit rebuild, lifecycle-hook failure, inspect, exec stdin/stdout, and stopped container.
- [ ] Invoke the official CLI with the task worktree as `--workspace-folder`.
- [ ] Capture container ID and remote workspace folder from structured output.
- [ ] Ensure normal resume never forces rebuild.
- [ ] Calculate and persist a diagnostic devcontainer input hash.
- [ ] Commit: `feat: add devcontainer runtime adapter`.

## Task 8: Implement JSON-RPC framing and correlation

**Interfaces:**
- `JsonRpcConnection.send_request(method, params) -> result`
- `send_notification(method, params)`
- incoming request callback for server-to-client requests
- notification callback
- typed protocol error and connection-closed exceptions

- [ ] Test fragmented lines, multiple messages per read, responses, notifications, incoming requests, errors, unknown IDs, duplicate responses, and closure.
- [ ] Allocate unique request IDs and correlate futures safely.
- [ ] Parse stdout only as JSON-RPC; keep stderr separate.
- [ ] Bound pending request memory and fail pending futures on disconnect.
- [ ] Commit: `feat: add app-server JSON-RPC transport`.

## Task 9: Build a fake Codex app-server

**Files:**
- Add a deterministic executable/test fixture implementing the required protocol subset

**Capabilities:**
- initialization;
- thread start/resume/read;
- turn start/steer/interrupt;
- status/item/message/command/file-change/diff events;
- user-input request;
- command/patch approval request;
- errors and turn completion.

- [ ] Script controllable scenarios for success, clarification, approval, rejection, interruption, crash, and resume.
- [ ] Verify tests can run without a Codex account or network.
- [ ] Commit: `test: add fake Codex app-server`.

## Task 10: Implement the Codex app-server adapter

**Interfaces:**
- `start_server(workspace) -> AppServerSession`
- `initialize(session) -> CapabilitySnapshot`
- `start_thread(session, config) -> thread_id`
- `resume_thread(session, thread_id)`
- `read_thread(session, thread_id)`
- `start_turn(session, thread_id, input) -> turn_id`
- `steer_turn(session, thread_id, turn_id, input)`
- `interrupt_turn(session, thread_id, turn_id)`
- `resolve_server_request(session, request_id, response)`

- [ ] Launch `codex app-server` through `DevcontainerAdapter.exec_process`; never launch it directly on WSL for task execution.
- [ ] Perform the initialization handshake and capture version/capabilities.
- [ ] Implement current v2 thread/turn methods, isolating protocol names in one adapter.
- [ ] Normalize app-server notifications into stable cockpit events.
- [ ] Persist exact thread, turn, item, and request IDs.
- [ ] Return typed compatibility failures when required methods are unavailable.
- [ ] Test all behavior against the fake app-server.
- [ ] Commit: `feat: integrate Codex app-server in devcontainers`.

## Task 11: Implement task runner vertical slice

**Flow:**

```text
create task
-> worktree
-> devcontainer up
-> app-server process
-> initialize
-> thread/start
-> turn/start
-> structured events
-> terminal turn completion
```

- [ ] Write an integration test for the entire fake-tool flow.
- [ ] Enforce one active runner operation per task.
- [ ] Persist database state before broadcasting events.
- [ ] Reach `READY_FOR_REVIEW` after a successful completed turn.
- [ ] Reach `FAILED` with actionable diagnostics on startup/protocol failure.
- [ ] Commit: `feat: run Codex tasks through app-server`.

## Task 12: Add durable event broker and WebSocket replay

**Interfaces:**
- Persisted event publishing and task subscriptions.
- `WS /api/events` supports `after_event_id` replay.

- [ ] Test ordering, reconnect replay, slow consumers, disconnect, and duplicate avoidance.
- [ ] Persist first, then fan out.
- [ ] Keep raw protocol payload only where needed; expose normalized sanitized payloads to clients.
- [ ] Commit: `feat: stream persistent task events`.

## Task 13: Implement clarification and approval requests

**Interfaces:**
- Protocol request entity and resolution endpoint.
- UI-ready schema for options, free text, approval, and rejection.

- [ ] Persist incoming server request before notification.
- [ ] Transition to `WAITING_FOR_INPUT` or `WAITING_FOR_APPROVAL`.
- [ ] Correlate browser response to the exact JSON-RPC request ID.
- [ ] Reject stale, duplicate, wrong-task, and already-resolved responses.
- [ ] Resume `RUNNING` only after response delivery succeeds.
- [ ] Test clarification, free-text response, approval, rejection, and server disconnect while pending.
- [ ] Commit: `feat: relay Codex questions and approvals`.

## Task 14: Add follow-up, steering, and interruption

- [ ] Add a follow-up endpoint that starts a new turn on the same thread when no turn is active.
- [ ] Add steering for supported active turns with expected turn ID checks.
- [ ] Add protocol interruption and wait for terminal completion.
- [ ] Add explicit force-stop that terminates the owned process only after confirmation.
- [ ] Test race conditions around completion, steering, interruption, and stale turn IDs.
- [ ] Commit: `feat: control active Codex turns`.

## Task 15: Configure Codex authentication and persistent home

- [ ] Inspect the full-stack template devcontainer user and mount conventions.
- [ ] Implement and document a persistent host-controlled `CODEX_HOME` mount strategy.
- [ ] Validate target ownership and permissions.
- [ ] Add diagnostics for app-server availability and authentication status without exposing secrets.
- [ ] Test concurrent task containers; if shared writable home is unsafe, implement isolated runtime homes with narrow authentication handoff.
- [ ] Persist non-secret strategy/path metadata.
- [ ] Commit: `feat: persist Codex authentication and threads`.

## Task 16: Implement validation inside the task devcontainer

- [ ] Parse repository-specific validation commands.
- [ ] Default to current Techletes preflight conventions when absent.
- [ ] Execute sequentially through the devcontainer adapter.
- [ ] Persist command result, exit code, sanitized tails, and events.
- [ ] Test success, early failure, cancellation, and retry.
- [ ] Commit: `feat: run task validation in devcontainers`.

## Task 17: Add GitHub issue and draft-PR lifecycle

- [ ] Fetch issue title/body/labels before task execution.
- [ ] Include issue context and repository instructions in the initial turn input.
- [ ] Add explicit commit, push, and draft-PR actions.
- [ ] Require approval according to execution profile.
- [ ] Persist PR metadata and poll CI/review status with bounded intervals.
- [ ] Never merge automatically.
- [ ] Contract-test using fake `gh` or mocked HTTP transport.
- [ ] Commit: `feat: add GitHub issue to draft PR flow`.

## Task 18: Implement browser/backend recovery

- [ ] On startup, load non-terminal tasks and verify worktree/container/process state.
- [ ] Detect known orphaned app-server processes without pretending the old pipe remains controllable.
- [ ] Add explicit orphan cleanup logic.
- [ ] Start a fresh app-server process and initialize it.
- [ ] Resume the persisted thread and read history.
- [ ] Reconcile completed turns and current diff.
- [ ] Mark ambiguous lost in-flight turns `RECOVERY_REQUIRED`.
- [ ] Test browser reconnect independently from backend restart.
- [ ] Commit: `feat: recover interrupted app-server sessions`.

## Task 19: Build the dashboard UI

**Required screens/components:**
- repository registry and diagnostics;
- task creation from prompt/preset/issue;
- task list with state/attention filters;
- activity and agent conversation;
- structured input/approval dialog;
- changes/current diff;
- validation;
- PR/CI;
- runtime/recovery diagnostics.

- [ ] Build on the inherited template design system and patterns.
- [ ] Use REST for commands/queries and WebSocket for events.
- [ ] Never infer task state from display strings.
- [ ] Reconnect with last event ID and replay missed events.
- [ ] Render protocol-provided input options and free-text fields.
- [ ] Add follow-up, steer, interrupt, resume, and force-stop controls with state-based availability.
- [ ] Test critical interactions with the template's frontend test stack.
- [ ] Commit: `feat: add engineering cockpit dashboard`.

## Task 20: Add overlap detection and synchronization warnings

- [ ] Compare changed-file sets for active tasks in the same repository.
- [ ] Detect shared files and, where available, overlapping diff hunks.
- [ ] Recalculate after file-change/diff events and PR merges.
- [ ] Show risk and recommended merge/sync order.
- [ ] Do not automatically resolve semantic conflicts.
- [ ] Commit: `feat: warn about overlapping task changes`.

## Task 21: Add safe cleanup and retention

- [ ] Refuse cleanup for dirty/unpushed/unmerged worktrees by default.
- [ ] Stop or retain the devcontainer according to repository policy.
- [ ] Stop the owned app-server gracefully before container/worktree cleanup.
- [ ] Require explicit force confirmation for destructive cleanup.
- [ ] Retain task/event/PR history after runtime removal.
- [ ] Test all safe and forced variants.
- [ ] Commit: `feat: add safe task cleanup`.

## Task 22: Add notifications

- [ ] Notify only on meaningful transitions: input required, approval required, validation failure, recovery required, and PR ready.
- [ ] Use browser notifications with permission handling.
- [ ] Deduplicate replayed events.
- [ ] Keep sound disabled by default.
- [ ] Commit: `feat: notify users about task attention states`.

## Task 23: Complete acceptance testing and documentation

- [ ] Automate a fake end-to-end flow from repository registration through draft PR metadata.
- [ ] Test clarification, approval, steering, interruption, crash, backend restart, thread resume, and event replay.
- [ ] Run a manual real-Codex test in one repository bootstrapped from `TECHLETES/full-stack-template`.
- [ ] Run two real tasks concurrently and verify separate branch, worktree, devcontainer, app-server process, JSON-RPC connection, thread, and mutable runtime data.
- [ ] Document installation, repository onboarding, Codex authentication, runtime diagnostics, recovery, cleanup, and known limitations.
- [ ] Run full inherited template preflight.
- [ ] Commit: `docs: complete cockpit acceptance and operations guide`.

---

## Delivery phases

### Phase 1: Technical proof

Tasks 1–11.

Proves the highest-risk chain:

```text
full-stack template
-> worktree
-> devcontainer
-> app-server over stdio
-> thread and turn
-> structured completion
```

Do not proceed to broad UI work until this succeeds against both fake tools and one real repository.

### Phase 2: Interactive workflow

Tasks 12–19.

Adds event replay, questions, approvals, follow-up, steering, interruption, authentication persistence, validation, GitHub lifecycle, recovery, and the usable browser UI.

### Phase 3: Operational reliability

Tasks 20–23.

Adds overlap warnings, cleanup, notifications, end-to-end coverage, and operational documentation.

## Definition of done

The implementation is complete when a developer can start two concurrent real Codex tasks from the browser; each task runs app-server inside its own devcontainer and worktree; questions and approvals can be resolved from the browser; browser closure does not stop work; backend restart results in safe thread/worktree recovery; validation and draft-PR creation work through explicit actions; and cleanup is guarded against data loss.
