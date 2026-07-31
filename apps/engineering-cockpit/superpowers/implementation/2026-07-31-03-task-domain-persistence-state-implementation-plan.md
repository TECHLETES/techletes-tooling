# 03 — Task Domain, PostgreSQL Persistence, State Machine, and Execution Locking Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `techletes-superpowers:subagent-driven-development` (recommended) or `techletes-superpowers:executing-plans`. Complete subsystem 01 and repository model work from subsystem 02 first.

**Goal:** Add the durable cockpit aggregate, explicit state machine, append-only event history, command idempotency, and single-process execution locks.

**Architecture:** Extend the inherited SQLModel/PostgreSQL model layer in `backend/models.py`; keep orchestration logic in `backend/cockpit/`; write state and matching events atomically; serialize task commands with in-memory locks plus durable version/constraint checks.

**Tech stack:** Current template Python, SQLModel, PostgreSQL 18, Alembic, Pytest, asyncio.

## Global constraints

- Use `CockpitTask`, never the existing generic `Task` model.
- Do not hold a SQLModel session or transaction across an `await`.
- Do not execute Git, Docker, Codex, or GitHub calls inside database transactions.
- Every state transition and its event must commit atomically.
- Public models never expose raw protocol payloads, process environment, or secrets.
- One Uvicorn worker and one operational control-plane instance remain mandatory.

---

### Task 1: Define lifecycle enums, commands, and transition rules

**Files:**
- Create: `apps/engineering-cockpit/backend/cockpit/domain/enums.py`
- Create: `apps/engineering-cockpit/backend/cockpit/domain/transitions.py`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/domain/test_transitions.py`

**Interfaces:**

```python
class CockpitTaskState(str, Enum): ...
class CockpitAttention(str, Enum): ...
class InvalidTaskTransition(ValueError): ...

def assert_transition(current: CockpitTaskState, target: CockpitTaskState) -> None: ...
def derive_attention(state: CockpitTaskState) -> CockpitAttention: ...
```

- [ ] Write a parameterized test containing every allowed edge from the specification and verify all unlisted edges raise `InvalidTaskTransition`.
- [ ] Write tests that `WAITING_FOR_INPUT`, `WAITING_FOR_APPROVAL`, `RECOVERY_REQUIRED`, ready states, and terminal states derive the correct attention category.
- [ ] Implement the enum values exactly as specified; do not use `auto()`.
- [ ] Implement one immutable transition map and one terminal-state set.
- [ ] Run:

```bash
cd apps/engineering-cockpit
uv run pytest backend/tests/cockpit/domain/test_transitions.py -q
```

Expected: all cases pass and every enum member occurs in at least one test.

- [ ] Commit: `feat: define cockpit task lifecycle`.

### Task 2: Add SQLModel entities and public schemas

**Files:**
- Modify: `apps/engineering-cockpit/backend/models.py`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/domain/test_models.py`

**Interfaces:**

Add the table models and Base/Create/Public/List schemas described in the spec:

```python
CockpitRepository
CockpitTask
CockpitWorkspace
CockpitAgentSession
CockpitProtocolRequest
CockpitEvent
CockpitValidationRun
CockpitDelivery
```

- [ ] Write model tests for defaults, UUIDs, UTC timestamps, enum serialization, payload schema version, and owner/repository relationships.
- [ ] Add `User.cockpit_tasks` and matching `CockpitTask.owner` relationships using `ondelete="RESTRICT"`.
- [ ] Add unique constraints for repository/path, repository/branch, session-generation, and session/external-request ID using SQLAlchemy table arguments.
- [ ] Store sanitized structured payloads in PostgreSQL JSON columns.
- [ ] Use `DateTime(timezone=True)` for all timestamps.
- [ ] Keep response models separate from `table=True` models.
- [ ] Run:

```bash
cd apps/engineering-cockpit
uv run pytest backend/tests/cockpit/domain/test_models.py -q
uv run mypy backend/cockpit backend/models.py
```

Expected: PASS with no untyped definitions.

- [ ] Commit: `feat: add cockpit persistence models`.

### Task 3: Create and verify the Alembic migration

**Files:**
- Create: `apps/engineering-cockpit/backend/alembic/versions/<revision>_add_cockpit_domain.py`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/domain/test_migration.py`

- [ ] Start the inherited PostgreSQL support service.
- [ ] Generate the migration:

```bash
cd apps/engineering-cockpit/backend
uv run alembic revision --autogenerate -m "add_cockpit_domain"
```

- [ ] Review the generated migration. Ensure enum/constraint/index names are deterministic and downgrade drops child tables before parent tables.
- [ ] Add a migration test that upgrades from the previous revision, inserts a minimal repository/task/event graph, downgrades one revision, and upgrades again.
- [ ] Run:

```bash
cd apps/engineering-cockpit/backend
uv run alembic upgrade head
uv run alembic downgrade -1
uv run alembic upgrade head
```

Expected: each command exits 0 and `uv run alembic heads` prints exactly one head.

- [ ] Commit: `feat: migrate cockpit domain tables`.

### Task 4: Implement the short-lived persistence store

**Files:**
- Create: `apps/engineering-cockpit/backend/cockpit/persistence/store.py`
- Create: `apps/engineering-cockpit/backend/cockpit/persistence/errors.py`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/persistence/test_store.py`

**Interfaces:**

```python
class CockpitStore:
    def create_task(... ) -> CockpitTask: ...
    def get_task(task_id: UUID) -> CockpitTask: ...
    def transition(
        task_id: UUID,
        target: CockpitTaskState,
        *,
        expected_version: int | None,
        event_type: str,
        payload: dict[str, Any],
    ) -> tuple[CockpitTask, CockpitEvent]: ...
    def append_event(...) -> CockpitEvent: ...
    def list_events(*, task_id: UUID, after_id: int, limit: int) -> list[CockpitEvent]: ...
```

- [ ] Write tests proving transition and event insertion roll back together when either fails.
- [ ] Write stale-version tests expecting `StaleTaskVersion`.
- [ ] Implement each method with a fresh `Session(get_engine())` context and explicit commit/refresh.
- [ ] Never return an attached session-bound object to long-running async code without materializing required fields.
- [ ] Add a maximum replay page size and stable ordering by event ID.
- [ ] Run focused tests and commit: `feat: add cockpit persistence store`.

### Task 5: Add task operation locks and global semaphores

**Files:**
- Create: `apps/engineering-cockpit/backend/cockpit/runtime/locks.py`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/runtime/test_locks.py`

**Interfaces:**

```python
class TaskOperationLocks:
    @asynccontextmanager
    async def hold(self, task_id: UUID) -> AsyncIterator[None]: ...

@dataclass(frozen=True)
class RuntimeLimits:
    max_active_tasks: int
    max_container_starts: int
    max_validations: int
```

- [ ] Test same-task operations serialize and different-task operations overlap.
- [ ] Test cancelled waiters are removed and lock entries are pruned after inactivity.
- [ ] Add named global semaphores from settings; expose current/limit counts for diagnostics.
- [ ] Do not use PostgreSQL row locks as a substitute for the supported single-process owner.
- [ ] Commit: `feat: serialize cockpit task operations`.

### Task 6: Add idempotent command records

**Files:**
- Modify: `apps/engineering-cockpit/backend/models.py`
- Create: `apps/engineering-cockpit/backend/cockpit/persistence/idempotency.py`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/persistence/test_idempotency.py`
- Add migration for: `CockpitCommandReceipt`

**Interfaces:**

```python
class CommandReceiptStore:
    def begin(*, key: str, task_id: UUID, command: str, request_hash: str) -> BeginResult: ...
    def complete(*, receipt_id: UUID, response_status: int, response_json: dict[str, Any]) -> None: ...
```

- [ ] Test first use, same-body replay, different-body conflict, incomplete receipt recovery, and key expiry policy.
- [ ] Normalize JSON before hashing with deterministic key ordering.
- [ ] Limit keys and stored response bodies to bounded sizes.
- [ ] Commit: `feat: add idempotent cockpit commands`.

### Task 7: Wire lifecycle initialization into FastAPI lifespan

**Files:**
- Modify: `apps/engineering-cockpit/backend/main.py`
- Create: `apps/engineering-cockpit/backend/cockpit/runtime/context.py`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/runtime/test_lifespan.py`

**Interfaces:**

```python
@dataclass
class CockpitRuntimeContext:
    store: CockpitStore
    locks: TaskOperationLocks
    limits: RuntimeLimits
```

- [ ] Build one context during FastAPI lifespan and store it on `app.state.cockpit`.
- [ ] Assert the host single-instance lock from subsystem 01 is held before accepting task commands.
- [ ] On shutdown, mark runtime as draining; do not start new task operations.
- [ ] Test exactly one context is created and closed per application lifespan.
- [ ] Do not initialize live adapters or recovery here yet; later subsystems extend the context.
- [ ] Commit: `feat: initialize cockpit runtime context`.

### Task 8: Complete subsystem verification

- [ ] Run:

```bash
cd apps/engineering-cockpit
uv run alembic upgrade head
uv run pytest backend/tests/cockpit/domain backend/tests/cockpit/persistence backend/tests/cockpit/runtime -q
uv run mypy backend
uv run ruff check backend
```

Expected: one Alembic head and all checks pass.

- [ ] Manually inspect PostgreSQL to confirm event IDs increase and no state transition occurs without a matching event.
- [ ] Update `apps/engineering-cockpit/superpowers/README.md` only if an interface changed; do not alter downstream contracts silently.
- [ ] Commit: `test: verify cockpit task domain`.

## Exit criteria

Subsystem 03 is complete when migrations are reversible, task state can only change through the validated store, committed events are replayable by ID, duplicate/stale commands are rejected deterministically, and concurrent commands cannot produce two owners for one task.
