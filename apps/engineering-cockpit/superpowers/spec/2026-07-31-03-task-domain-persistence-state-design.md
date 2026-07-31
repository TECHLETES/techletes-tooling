# 03 — Task Domain, PostgreSQL Persistence, State Machine, and Execution Locking Specification

## Purpose

Define the durable domain model and concurrency rules that every other cockpit subsystem relies on. This subsystem owns orchestration truth: which task exists, what state it is in, which worktree/container/thread belongs to it, what external operation is currently active, and what events or pending requests have been observed.

It does **not** own Git, Docker, Codex, or GitHub truth. Those external systems remain authoritative for their own resources and are reconciled through adapters. PostgreSQL stores the cockpit's durable intent, identifiers, and normalized history.

## Template alignment

The full-stack template uses:

- PostgreSQL;
- SQLModel table and public models in `backend/models.py`;
- synchronous `sqlmodel.Session` instances from `backend.core.db.get_engine()`;
- Alembic migrations;
- UUID primary keys and timezone-aware timestamps;
- authenticated users and RBAC.

The cockpit follows those conventions. It does not introduce SQLite or a second ORM. Database operations from long-running asyncio code use short-lived synchronous sessions and never keep a session or transaction open while awaiting a subprocess, WebSocket, timer, or network call.

## Naming

The template already contains a generic `Task` model for RQ jobs. Cockpit entities therefore use explicit names:

- `CockpitRepository`
- `CockpitTask`
- `CockpitWorkspace`
- `CockpitAgentSession`
- `CockpitProtocolRequest`
- `CockpitEvent`
- `CockpitValidationRun`
- `CockpitDelivery`

API schemas follow the existing Base/Create/Update/Public/List convention.

## Aggregate boundary

`CockpitTask` is the aggregate root. A task owns exactly zero or one current workspace and may own multiple historical agent sessions, protocol requests, events, validation runs, and delivery records.

Deletion of application users must not silently delete source worktrees or containers. For MVP, task records use `owner_id` with `ondelete="RESTRICT"`; user deletion is refused while retained cockpit tasks reference the user. Runtime cleanup is a separate explicit operation.

## Durable entities

### CockpitRepository

Introduced in subsystem 02 and referenced here. It identifies the canonical clone from which worktrees are created.

### CockpitTask

Required fields:

- `id: UUID`
- `repository_id: UUID`
- `owner_id: UUID`
- `title: str`
- `prompt: str`
- `source_type: manual | github_issue | preset`
- `source_reference: str | None`
- `state: CockpitTaskState`
- `branch_name: str | None`
- `base_ref: str`
- `execution_profile: str`
- `operation_version: int`
- `active_operation: str | None`
- `failure_code: str | None`
- `failure_summary: str | None`
- timestamps for creation, update, start, stop, completion, and cleanup.

`operation_version` increments on every state-changing command. Commands may supply `expected_version`; stale commands receive HTTP 409 instead of overwriting newer state.

### CockpitWorkspace

One current row per task:

- worktree path and canonical real path;
- Git common directory;
- base SHA and current head SHA;
- devcontainer config path and input hash;
- container ID and remote workspace folder;
- Compose project identity when available;
- Codex-home strategy identifier;
- runtime status and last inspection timestamp;
- cleanup status.

A unique constraint prevents two active tasks from claiming the same worktree path or branch within one repository.

### CockpitAgentSession

One row per app-server process generation:

- task ID;
- generation number;
- protocol name and supported Codex version;
- process start metadata, not secrets;
- initialization state;
- thread ID;
- active turn ID;
- last item ID;
- capability/schema fingerprint;
- connection state;
- start/end timestamps and exit reason.

A backend restart creates a new session generation. It may resume the same Codex thread but must not pretend the old stdio connection is still owned.

### CockpitProtocolRequest

Durable server-to-client request:

- task/session IDs;
- exact app-server JSON-RPC request ID as a string;
- request method/kind;
- normalized prompt, options, and safe metadata;
- status: `pending`, `answering`, `answered`, `rejected`, `expired`, or `delivery_failed`;
- sanitized response;
- version and timestamps.

`(agent_session_id, external_request_id)` is unique. The request is inserted and committed before the browser is notified.

### CockpitEvent

Append-only normalized event:

- integer primary key used as replay cursor;
- task ID;
- optional session/turn/item IDs;
- stable cockpit event type;
- schema version;
- sanitized JSON payload;
- creation timestamp.

Events are never updated. Corrections are represented by later events. Raw app-server lines are not stored in this table; bounded diagnostic logs are stored separately on disk with rotation.

### CockpitValidationRun

Records one execution of one configured validation command, including command identifier, attempt, timestamps, exit code, sanitized output tails, cancellation state, and worktree head SHA.

### CockpitDelivery

Records explicit commit/push/PR lifecycle metadata: commit SHA, remote branch, PR number/URL, expected head SHA, CI state, review state, and last synchronization time.

## Task state model

The persisted lifecycle is intentionally explicit:

```text
CREATED
PREPARING_WORKTREE
WORKTREE_READY
STARTING_CONTAINER
CONTAINER_READY
STARTING_APP_SERVER
INITIALIZING_APP_SERVER
STARTING_THREAD
RESUMING_THREAD
STARTING_TURN
RUNNING
WAITING_FOR_INPUT
WAITING_FOR_APPROVAL
INTERRUPTING
VALIDATING
READY_FOR_REVIEW
COMMITTING
PUSHING
CREATING_PR
WAITING_FOR_CI
READY_TO_MERGE
STOPPING
STOPPED
RECOVERY_REQUIRED
CLEANUP_PENDING
CLEANED
COMPLETED
FAILED
CANCELLED
```

Terminal states are `CLEANED`, `COMPLETED`, `FAILED`, and `CANCELLED`. `STOPPED` is resumable. `RECOVERY_REQUIRED` is a safe holding state, not an error alias.

The state machine is defined in one module as an explicit map. Route handlers and adapters cannot assign `state` directly. They call `TaskStore.transition(...)`, which:

1. acquires the per-task operation lock;
2. verifies current state and optional expected version;
3. writes state, version, timestamps, and event in one database transaction;
4. commits;
5. publishes the committed event.

## State versus derived attention

The UI needs attention categories but they are derived, not separately persisted:

- `working`: active lifecycle states;
- `needs_input`: `WAITING_FOR_INPUT`;
- `needs_approval`: `WAITING_FOR_APPROVAL`;
- `needs_recovery`: `RECOVERY_REQUIRED`;
- `ready`: `READY_FOR_REVIEW` or `READY_TO_MERGE`;
- `ended`: terminal states.

This prevents state and attention flags from contradicting each other.

## Command idempotency

Every mutating API command accepts an optional `Idempotency-Key` header. The cockpit stores the key, command type, task ID, normalized request hash, result status, and response reference.

Rules:

- repeating the same key with the same body returns the original result;
- reusing a key with a different body returns HTTP 409;
- commands without a key remain protected by expected task version and state validation;
- external operations record a durable intent event before execution and a result event afterward.

The intent/result pair allows recovery to distinguish “never started,” “started but result unknown,” and “completed.”

## Concurrency model

### Single control-plane instance

Subsystem 01 provides a host file lock. Only one operational backend instance may own live task processes. Uvicorn runs with one worker.

### Per-task lock

A singleton `TaskOperationLocks` maintains one `asyncio.Lock` per active task. All lifecycle-changing operations for one task serialize through it. Different tasks may progress concurrently.

### Global semaphores

Separate semaphores bound expensive operations:

- worktree creation/removal;
- devcontainer build/start;
- app-server start;
- validation commands.

Limits come from settings and are visible in diagnostics.

### Database protection

The in-memory lock is the primary protection in the supported single-process topology. PostgreSQL constraints and `operation_version` remain the durable protection against duplicate paths, stale browser commands, and accidental future multi-process execution.

## Persistence transaction rules

- No SQLModel `Session` survives across `await`.
- Each store method creates or receives a short-lived session, commits, refreshes, and closes.
- State transition and matching event insertion are atomic.
- Protocol request insertion and corresponding task transition are atomic.
- External commands are never executed inside a database transaction.
- Output streams are buffered in memory only up to configured limits; persistent events contain bounded payloads.
- JSON payloads carry a schema version.

## Event publication rule

Database first, broadcast second:

```text
begin transaction
  update task / insert domain record
  insert event
commit
publish event ID to local/Redis subscribers
```

If broadcast fails, the event remains replayable from PostgreSQL. Redis pub/sub is an optimization for live fan-out, never the source of truth.

## Error taxonomy

Errors use stable machine codes, for example:

- `INVALID_TRANSITION`
- `STALE_TASK_VERSION`
- `TASK_OPERATION_BUSY`
- `WORKTREE_PATH_CONFLICT`
- `CONTAINER_START_FAILED`
- `APP_SERVER_INCOMPATIBLE`
- `APP_SERVER_CONNECTION_LOST`
- `PROTOCOL_REQUEST_STALE`
- `RECOVERY_AMBIGUOUS`

User-visible summaries are sanitized. Detailed diagnostics may reference a local log file ID, not raw secrets.

## Retention

Task, event, validation, protocol request, and delivery history is retained after runtime cleanup. Runtime identifiers are marked inactive rather than deleted. Retention and pruning policy is implemented in subsystem 14.

## Risks and mitigations

### Generic Task name collision

Mitigation: use `CockpitTask` everywhere and explicit API tags.

### Long database transactions blocking orchestration

Mitigation: short store calls, no session across await, and tests that instrument transaction duration.

### State explosion

Mitigation: persist only externally meaningful lifecycle states; derive UI attention and progress. Add a state only when it changes allowed commands or recovery behavior.

### Duplicate browser commands

Mitigation: idempotency keys, expected version, per-task lock, and state validation.

### Crash between intent and external result

Mitigation: durable intent event followed by reconciliation. Never infer success from the intended state alone.

### Event replay gaps

Mitigation: global monotonic event IDs and database-first publication.

## Verification strategy

- migration upgrade and downgrade against PostgreSQL;
- model relationship and cascade/restrict tests;
- exhaustive parameterized state transition tests;
- atomic state/event transaction tests;
- stale version and idempotency tests;
- two concurrent commands against one task produce one success and one typed conflict;
- operations on different tasks run concurrently;
- no open SQL transaction while awaiting a fake long-running process;
- event IDs replay in committed order;
- backend restart can load all non-terminal task/session metadata without requiring live process objects.

## Research basis

- [Techletes full-stack template backend conventions](https://github.com/TECHLETES/full-stack-template/blob/main/docs/backend.instructions.md)
- [SQLModel](https://sqlmodel.tiangolo.com/)
- [Alembic](https://alembic.sqlalchemy.org/)
- [PostgreSQL constraints and transactions](https://www.postgresql.org/docs/current/ddl-constraints.html)
- [Python asyncio synchronization primitives](https://docs.python.org/3/library/asyncio-sync.html)
