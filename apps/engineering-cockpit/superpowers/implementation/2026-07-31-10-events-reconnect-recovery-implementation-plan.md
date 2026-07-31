# 10 — Durable Events, WebSocket Replay, Browser Reconnect, and Backend Recovery Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `techletes-superpowers:subagent-driven-development` or `techletes-superpowers:executing-plans`. Subsystems 03, 05–09 are prerequisites.

**Goal:** Provide durable task-event replay and conservative backend restart recovery without coupling task execution to any browser connection.

**Architecture:** PostgreSQL is the event source of truth; Redis carries event-ID wakeups; authenticated WebSockets replay/fan out events. Startup reconciliation verifies Git/container identity, terminates only positively tagged orphan app-server processes, resumes thread history on a fresh connection, and marks ambiguous turns for human recovery.

**Tech stack:** Existing SQLModel/PostgreSQL/Redis/JWT WebSocket patterns, FastAPI, asyncio, Docker/devcontainer/Codex adapters, Pytest and Playwright integration fixtures.

## Global constraints

- Persist before publish.
- Browser state never owns or stops a task.
- WebSocket backpressure closes/replays rather than dropping events silently.
- Backend restart cannot reattach old stdio.
- Never recreate missing worktrees, rebuild containers, restart prompts, or resend approvals automatically.
- Orphan termination requires exact task container plus environment/session identity.

---

### Task 1: Finalize durable event storage and replay queries

**Files:**
- Modify: `apps/engineering-cockpit/backend/models.py`
- Modify: `apps/engineering-cockpit/backend/cockpit/persistence/store.py`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/events/test_event_store.py`
- Add migration only if final indexes/schema differ from subsystem 03.

**Interfaces:**

```python
class CockpitEventStore:
    def append_in_transaction(... ) -> CockpitEvent: ...
    def get(self, event_id: int) -> CockpitEvent | None: ...
    def list_authorized(
        self,
        *,
        user_id: UUID,
        after_id: int,
        task_ids: set[UUID] | None,
        limit: int,
    ) -> list[CockpitEventPublic]: ...
    def current_id(self) -> int: ...
    def retention_floor_id(self) -> int: ...
```

- [ ] Add indexes on `(task_id, id)`, owner/task authorization joins, and creation time.
- [ ] Test ascending replay, page boundary, nonexistent cursor, unauthorized task, admin permission, global current ID, and empty table.
- [ ] Keep schema version and bounded JSON payload mandatory.
- [ ] Commit: `feat: query durable cockpit events`.

### Task 2: Implement Redis event envelopes

**Files:**
- Create: `apps/engineering-cockpit/backend/cockpit/events/redis.py`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/events/test_redis.py`

**Interfaces:**

```python
@dataclass(frozen=True)
class EventEnvelope:
    event_id: int
    task_id: UUID
    owner_id: UUID

class EventEnvelopePublisher:
    async def publish(self, envelope: EventEnvelope) -> None: ...
```

- [ ] Reuse the template Redis connection factory but use dedicated versioned channels.
- [ ] Publish only IDs/ownership routing metadata, not event payload.
- [ ] Test serialization, publish failure, reconnect, duplicate envelope, and Redis unavailable.
- [ ] A publish error records a safe warning and returns; it cannot roll back domain state.
- [ ] Commit: `feat: publish cockpit event envelopes`.

### Task 3: Add a database-first event broker

**Files:**
- Create: `apps/engineering-cockpit/backend/cockpit/events/broker.py`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/events/test_broker.py`

**Interfaces:**

```python
class CockpitEventBroker:
    async def publish_committed(self, event: CockpitEventSnapshot) -> None: ...
    async def subscribe_user(self, user_id: UUID) -> AsyncIterator[EventEnvelope]: ...
```

- [ ] Make store/domain code return a committed event snapshot; broker never inserts the row itself after the fact.
- [ ] Add local wakeup fast path only if it cannot change ordering semantics; Redis remains the shared wakeup path.
- [ ] Test commit-before-envelope with spies, Redis failure, duplicate envelope, and broker shutdown.
- [ ] Wire subsystem 03/07/09 event emissions through the broker after commit.
- [ ] Commit: `feat: broadcast committed cockpit events`.

### Task 4: Define WebSocket frame schemas

**Files:**
- Modify: `apps/engineering-cockpit/backend/models.py`
- Create: `apps/engineering-cockpit/backend/cockpit/events/websocket_models.py`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/events/test_websocket_models.py`

**Frames:**

```text
hello
cockpit_event
heartbeat
replay_complete
replay_reset_required
server_draining
error
```

Client frames:

```text
ping
subscribe
ack
```

- [ ] Define versioned Pydantic/SQLModel public schemas and strict size/count limits.
- [ ] Include server instance ID, current event ID, retention floor, and heartbeat interval in hello.
- [ ] Test unknown frame type, invalid cursor, oversized task subscription, and serialization.
- [ ] Commit: `feat: define cockpit event websocket protocol`.

### Task 5: Implement authenticated replay WebSocket

**Files:**
- Create: `apps/engineering-cockpit/backend/api/routes/cockpit_events.py`
- Modify: `apps/engineering-cockpit/backend/api/main.py`
- Create: `apps/engineering-cockpit/backend/cockpit/events/websocket.py`
- Create: `apps/engineering-cockpit/backend/tests/api/routes/test_cockpit_events_ws.py`

- [ ] Reuse/refactor the template notification route's JWT-cookie validation into a shared WebSocket auth helper without weakening existing behavior.
- [ ] Accept `after_event_id`, send hello, page authorized replay, send replay-complete, then subscribe to Redis.
- [ ] For each live envelope, fetch the database row and verify authorization before send.
- [ ] Handle replay/live overlap by tracking last sent ID and loading any gap from PostgreSQL.
- [ ] Support optional authorized task filter updates.
- [ ] Send heartbeat and drain incoming ping/ack frames.
- [ ] Test auth missing/expired, owner/admin, unauthorized filter, replay, live event, duplicate envelope, gap fill, and graceful close.
- [ ] Commit: `feat: stream replayable cockpit events`.

### Task 6: Add slow-consumer and retention-reset behavior

**Files:**
- Modify: `apps/engineering-cockpit/backend/cockpit/events/websocket.py`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/events/test_backpressure_retention.py`

- [ ] Use a bounded per-connection send queue.
- [ ] When full, close with 1013 and retain last successfully sent event ID only.
- [ ] If requested cursor is below retention floor, send `replay_reset_required` and no partial old replay.
- [ ] Test blocked socket, queue full, reconnect/replay, retention floor equal/below/above cursor, and concurrent prune snapshot.
- [ ] Never block the protocol/app-server reader on socket sends.
- [ ] Commit: `feat: handle cockpit event backpressure`.

### Task 7: Tag app-server launches for orphan identification

**Files:**
- Modify: `apps/engineering-cockpit/backend/cockpit/runtime/app_server_process.py`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/recovery/test_process_tagging.py`

- [ ] Launch the target command through the fixed executable `env` with:

```text
COCKPIT_AGENT_SESSION_ID=<uuid>
COCKPIT_TASK_ID=<uuid>
codex app-server --listen stdio://
```

- [ ] Build this as argv; do not use shell interpolation.
- [ ] Persist the exact session/task marker values and process generation.
- [ ] Test the fake target process receives markers while diagnostics/logs never print unrelated environment.
- [ ] Commit: `feat: tag task app-server processes`.

### Task 8: Implement exact-container orphan inspection

**Files:**
- Create: `apps/engineering-cockpit/backend/cockpit/recovery/orphan.py`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/recovery/test_orphan.py`

**Interfaces:**

```python
@dataclass(frozen=True)
class OrphanProcess:
    pid: int
    command_hash: str
    session_id: UUID
    task_id: UUID

class OrphanInspector:
    async def find_exact(... ) -> list[OrphanProcess]: ...
    async def terminate_exact(..., process: OrphanProcess) -> None: ...
```

- [ ] Execute a fixed inspection helper inside only the persisted task container to read `/proc` cmdline/environment for same-user processes.
- [ ] Match both task/session markers and `codex app-server`; name-only matches are insufficient.
- [ ] Test exact match, manual untagged Codex, wrong task/session, inaccessible `/proc`, multiple exact matches, PID reuse verification, TERM then KILL, and termination failure.
- [ ] Multiple exact matches or unverifiable identity yields `RECOVERY_ORPHAN_UNCONFIRMED`, not broad kill.
- [ ] Commit: `feat: inspect orphaned app-server processes`.

### Task 9: Model recovery observations and decisions

**Files:**
- Create: `apps/engineering-cockpit/backend/cockpit/recovery/models.py`
- Create: `apps/engineering-cockpit/backend/cockpit/recovery/planner.py`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/recovery/test_planner.py`

**Interfaces:**

```python
@dataclass(frozen=True)
class RecoveryObservation:
    worktree: WorktreeObservation
    container: ContainerObservation
    previous_session: SessionObservation
    orphan: OrphanObservation
    thread: ThreadObservation
    git: GitStatusObservation

@dataclass(frozen=True)
class RecoveryPlan:
    actions: tuple[RecoveryAction, ...]
    outcome_state: CockpitTaskState
    reason_code: str
```

- [ ] Encode every outcome matrix row from the spec as a pure planning function.
- [ ] Test missing worktree, Git mismatch, stopped/missing container, thread missing, terminal history found, lost active turn, unresolved request, clean stopped thread, and unconfirmed orphan.
- [ ] A plan never contains worktree recreation, rebuild, prompt replay, or approval resend.
- [ ] Commit: `feat: plan conservative cockpit recovery`.

### Task 10: Implement history reconciliation

**Files:**
- Create: `apps/engineering-cockpit/backend/cockpit/recovery/history.py`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/recovery/test_history.py`

**Interfaces:**

```python
class ThreadHistoryReconciler:
    def reconcile(
        self,
        *,
        persisted: PersistedThreadSnapshot,
        remote: CodexThreadSnapshot,
    ) -> ReconciliationResult: ...
```

- [ ] Match only exact thread/turn/item IDs.
- [ ] Add missing terminal/item events idempotently by source identity/hash.
- [ ] Detect conflicting status/content for an existing ID as `RECOVERY_HISTORY_MISMATCH`.
- [ ] Determine whether the last persisted active turn now has terminal evidence.
- [ ] Test duplicate remote events, missing items, terminal discovered, no terminal, ID conflict, and very large history paging.
- [ ] Commit: `feat: reconcile codex thread history`.

### Task 11: Implement the recovery service

**Files:**
- Create: `apps/engineering-cockpit/backend/cockpit/recovery/service.py`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/recovery/test_service.py`

**Interfaces:**

```python
class RecoveryService:
    async def reconcile_all(self) -> RecoveryReport: ...
    async def reconcile_task(self, task_id: UUID) -> RecoveryTaskResult: ...
```

- [ ] Load non-terminal tasks and process them with bounded concurrency and per-task locks.
- [ ] Persist recovery intent and unique recovery-run ID.
- [ ] Observe Git/container/previous session; terminate a proven orphan; ordinary-start a stopped/missing container without rebuild; start fresh app-server generation; reapply subsystem 08 policy; resume/read thread; reconcile history/Git; execute planner outcome.
- [ ] On any ambiguous step, transition `RECOVERY_REQUIRED` with evidence and preserve runtime/worktree.
- [ ] Make every action idempotent after crash and rerun.
- [ ] Test all outcome rows and crash after each major step.
- [ ] Commit: `feat: reconcile cockpit tasks after restart`.

### Task 12: Integrate startup/shutdown instance identity

**Files:**
- Modify: `apps/engineering-cockpit/backend/cockpit/runtime/context.py`
- Modify: `apps/engineering-cockpit/backend/main.py`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/recovery/test_startup.py`

- [ ] Generate/persist one `serverInstanceId` per backend process.
- [ ] After migrations and host lock, start event broker and run recovery before accepting mutating task commands.
- [ ] Permit read-only API/health with explicit `recovering` status during reconciliation.
- [ ] On graceful shutdown, broadcast `server_draining`, reject new mutating commands, and stop tasks per subsystem 09 policy.
- [ ] Test startup success, partial recovery failure, recovery timeout, and second process lock refusal.
- [ ] Commit: `feat: recover cockpit runtime on startup`.

### Task 13: Add recovery API and diagnostics

**Files:**
- Create: `apps/engineering-cockpit/backend/api/routes/cockpit_recovery.py`
- Modify: `apps/engineering-cockpit/backend/api/main.py`
- Create: `apps/engineering-cockpit/backend/tests/api/routes/test_cockpit_recovery.py`

**Endpoints:**

```text
GET  /api/v1/cockpit/recovery/status
POST /api/v1/cockpit/tasks/{id}/reconcile
POST /api/v1/cockpit/tasks/{id}/acknowledge-lost-turn
```

- [ ] Restrict manual reconcile/acknowledgement by owner/permission and expected task version.
- [ ] Acknowledge-lost-turn does not rerun it; it transitions to stopped-ready for an explicit follow-up after diff review.
- [ ] Return safe observations/actions, not raw `/proc`, credentials, or protocol history.
- [ ] Test auth, active recovery conflict, idempotent reconcile, and wrong recovery reason.
- [ ] Commit: `feat: expose cockpit recovery controls`.

### Task 14: Run browser/restart chaos integration tests

**Files:**
- Create: `apps/engineering-cockpit/backend/tests/integration/test_event_recovery_flow.py`
- Create: `apps/engineering-cockpit/backend/tests/integration/test_recovery_crash_matrix.py`

- [ ] Simulate browser disconnect/reconnect while fake app-server continues; verify replay.
- [ ] Kill/recreate the FastAPI app while fake app-server remains; detect/terminate exact orphan and resume thread.
- [ ] Simulate terminal history discovered and lost in-flight turn.
- [ ] Disable Redis and verify committed events replay.
- [ ] Crash during each recovery action and rerun idempotently.
- [ ] Recover two tasks concurrently within configured semaphores.
- [ ] Commit: `test: exercise cockpit reconnect and recovery`.

### Task 15: Complete subsystem verification

```bash
cd apps/engineering-cockpit
uv run pytest backend/tests/cockpit/events backend/tests/cockpit/recovery backend/tests/api/routes/test_cockpit_events_ws.py backend/tests/api/routes/test_cockpit_recovery.py backend/tests/integration/test_event_recovery_flow.py backend/tests/integration/test_recovery_crash_matrix.py -q
uv run mypy backend/cockpit/events backend/cockpit/recovery
uv run ruff check backend/cockpit/events backend/cockpit/recovery
```

- [ ] Manually close/reopen the browser during a real task and restart the backend during a harmless turn; record the conservative outcome.
- [ ] Commit: `test: verify durable events and recovery`.

## Exit criteria

Subsystem 10 is complete when event replay survives browser/Redis loss, slow clients reconnect without event loss, a new backend instance never claims an old pipe, exact orphan processes can be terminated narrowly, thread/Git history reconciles idempotently, and ambiguous in-flight work reliably enters `RECOVERY_REQUIRED` without automatic replay.
