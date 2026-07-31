# 09 — Clarification, Approvals, Follow-Up, Steering, Interruption, and Force-Stop Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `techletes-superpowers:subagent-driven-development` or `techletes-superpowers:executing-plans`. Subsystems 03, 07, and 08 are prerequisites.

**Goal:** Persist and resolve app-server questions/approvals safely, then expose race-safe follow-up, steering, interruption, stop/resume, and force-stop commands.

**Architecture:** Decode version-specific incoming requests in the Codex adapter, normalize/persist them before fan-out, resolve them through exact external request IDs, and serialize every turn control with task version, session generation, and turn ID checks.

**Tech stack:** FastAPI routes, SQLModel/PostgreSQL, subsystem 06 transport, subsystem 07 adapter, inherited RBAC and audit conventions, Pytest.

## Global constraints

- Never auto-approve, auto-reject, or guess an answer.
- Persist request and task attention before browser notification.
- Deliver each external request response at most once.
- Do not equate interrupt response with terminal turn completion.
- Force-stop is explicit, audited, and followed by recovery assessment.
- Free text and command details are sanitized according to data-retention policy.

---

### Task 1: Add public protocol-request schemas and enum completeness

**Files:**
- Modify: `apps/engineering-cockpit/backend/models.py`
- Modify: `apps/engineering-cockpit/backend/cockpit/domain/enums.py`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/interactions/test_models.py`
- Add migration if subsystem 03 did not include every final field/index.

**Interfaces:**

```python
class ProtocolRequestKind(str, Enum):
    USER_INPUT = "user_input"
    COMMAND_APPROVAL = "command_approval"
    FILE_CHANGE_APPROVAL = "file_change_approval"

class ProtocolRequestStatus(str, Enum): ...
class CockpitProtocolRequestPublic(SQLModel): ...
class CockpitProtocolRequestResolve(SQLModel): ...
```

- [ ] Model one or more question IDs, options, free-text rules, safe command/file summary, request version, and response status.
- [ ] Public output omits raw params and protocol-only secret fields.
- [ ] Add uniqueness on `(agent_session_id, external_request_id_kind, external_request_id_value)`.
- [ ] Test JSON round trips, status values, option IDs, and invalid mixed approval/input bodies.
- [ ] Commit: `feat: model cockpit protocol requests`.

### Task 2: Normalize incoming app-server requests

**Files:**
- Create: `apps/engineering-cockpit/backend/cockpit/codex/server_requests.py`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/codex/test_server_requests.py`

**Interfaces:**

```python
@dataclass(frozen=True)
class NormalizedServerRequest:
    external_id: JsonRpcId
    kind: ProtocolRequestKind
    thread_id: str
    turn_id: str
    title: str
    prompt: str
    questions: tuple[NormalizedQuestion, ...]
    command_summary: SafeCommandSummary | None
    file_change_summary: SafeFileChangeSummary | None
    payload_hash: str
```

- [ ] Derive exact request methods/params from generated schema and compatibility manifest.
- [ ] Test grouped questions, options, free text, command approval, file-change approval, unknown request, malformed payload, oversized prompt, ANSI, and secret-looking values.
- [ ] Preserve exact question/option IDs while sanitizing display text.
- [ ] Unknown request returns `APP_SERVER_UNKNOWN_REQUEST` and blocks the session.
- [ ] Commit: `feat: normalize codex server requests`.

### Task 3: Persist incoming requests atomically

**Files:**
- Create: `apps/engineering-cockpit/backend/cockpit/interactions/store.py`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/interactions/test_store.py`

**Interfaces:**

```python
class InteractionStore:
    def create_pending(
        self,
        *,
        task_id: UUID,
        session_id: UUID,
        request: NormalizedServerRequest,
    ) -> tuple[CockpitProtocolRequest, CockpitEvent, CockpitTask]: ...
    def begin_answer(... ) -> tuple[CockpitProtocolRequest, CockpitEvent]: ...
    def finish_answer(... ) -> tuple[CockpitProtocolRequest, CockpitEvent, CockpitTask]: ...
```

- [ ] Test request insert + waiting transition + event are atomic.
- [ ] Test duplicate identical payload returns existing record; duplicate ID with different hash fails.
- [ ] Support several pending requests and only return task to `RUNNING` after the last blocking request is delivered.
- [ ] Test turn-terminal cancellation of all pending requests.
- [ ] Keep sessions short and no await inside transaction.
- [ ] Commit: `feat: persist app-server interactions`.

### Task 4: Connect incoming-request callbacks to persistence

**Files:**
- Modify: `apps/engineering-cockpit/backend/cockpit/codex/service.py`
- Create: `apps/engineering-cockpit/backend/cockpit/interactions/service.py`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/interactions/test_incoming_service.py`

- [ ] Register one incoming-request callback when the JSON-RPC connection opens.
- [ ] Normalize then persist before any event broker call.
- [ ] Keep the transport request unresolved until browser resolution.
- [ ] On persistence failure, send a safe protocol error if possible and fail the task/session.
- [ ] On connection close, mark unresolved requests `DELIVERY_FAILED` or `CANCELLED_BY_TURN_END` based on known terminal evidence.
- [ ] Test persist-before-broadcast ordering with a spy broker.
- [ ] Commit: `feat: receive durable codex requests`.

### Task 5: Implement answer validation and wire response encoding

**Files:**
- Create: `apps/engineering-cockpit/backend/cockpit/interactions/responses.py`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/interactions/test_responses.py`

**Interfaces:**

```python
class ProtocolResponseEncoder:
    def validate_public_response(
        self,
        request: CockpitProtocolRequestSnapshot,
        response: CockpitProtocolRequestResolve,
    ) -> NormalizedProtocolResponse: ...
    def encode_wire_result(
        self,
        request: CockpitProtocolRequestSnapshot,
        response: NormalizedProtocolResponse,
    ) -> object: ...
```

- [ ] Validate exact question/option IDs, required free text, rejection support, and no extra answers.
- [ ] Derive wire result shape from generated schema.
- [ ] Test every request kind and invalid combination.
- [ ] Bound free-text length and normalize line endings without changing semantic content.
- [ ] Commit: `feat: encode codex interaction responses`.

### Task 6: Add the resolution API

**Files:**
- Create: `apps/engineering-cockpit/backend/api/routes/cockpit_interactions.py`
- Modify: `apps/engineering-cockpit/backend/api/main.py`
- Create: `apps/engineering-cockpit/backend/tests/api/routes/test_cockpit_interactions.py`

**Endpoint:**

```text
POST /api/v1/cockpit/protocol-requests/{request_id}/resolve
```

- [ ] Require authenticated task owner with `cockpit:operate`, or `cockpit:manage` for administrative action.
- [ ] Require expected request version and support idempotency key.
- [ ] Acquire task lock, validate active session generation/turn, mark `ANSWERING`, commit intent, send exact JSON-RPC response, then mark final status.
- [ ] Return HTTP 409 for stale/duplicate/wrong generation/ended turn; 422 for invalid answer; 403 for unauthorized.
- [ ] On ambiguous write/connection loss, mark `DELIVERY_FAILED` and task `RECOVERY_REQUIRED`.
- [ ] Add API tests for two-tab race and idempotent replay.
- [ ] Regenerate frontend client after all subsystem routes are final.
- [ ] Commit: `feat: resolve codex questions and approvals`.

### Task 7: Add follow-up command

**Files:**
- Create: `apps/engineering-cockpit/backend/cockpit/interactions/turn_control.py`
- Modify: `apps/engineering-cockpit/backend/api/routes/cockpit_tasks.py`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/interactions/test_follow_up.py`

**Interfaces:**

```python
async def follow_up(
    *,
    task_id: UUID,
    expected_task_version: int,
    text: str,
    idempotency_key: str | None,
) -> CockpitTaskPublic: ...
```

- [ ] Require live initialized connection, thread, no active turn, no pending request, and allowed task state.
- [ ] Build bounded context through subsystem 08 and start a new turn on the same thread.
- [ ] Persist turn ID and transitions before returning.
- [ ] Test ready/stopped success, active-turn conflict, pending-request conflict, stale version, connection lost, and idempotent repeat.
- [ ] Commit: `feat: add codex follow-up turns`.

### Task 8: Add steering command

**Files:**
- Modify: `apps/engineering-cockpit/backend/cockpit/interactions/turn_control.py`
- Modify: `apps/engineering-cockpit/backend/api/routes/cockpit_tasks.py`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/interactions/test_steer.py`

- [ ] Require exact expected thread/turn IDs and `RUNNING` state.
- [ ] Block while waiting for input/approval or interrupting.
- [ ] Persist intent before `turn/steer`, result afterward.
- [ ] Test success, unsupported capability, completion-wins race, stale turn, oversized input, and connection loss.
- [ ] A completion-wins race returns 409 and never starts a new turn automatically.
- [ ] Commit: `feat: steer active codex turns`.

### Task 9: Add protocol interruption

**Files:**
- Modify: `apps/engineering-cockpit/backend/cockpit/interactions/turn_control.py`
- Modify: `apps/engineering-cockpit/backend/api/routes/cockpit_tasks.py`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/interactions/test_interrupt.py`

- [ ] Transition to `INTERRUPTING`, call `turn/interrupt`, and wait on a future completed only by a schema-defined terminal event.
- [ ] Add configurable timeout; timeout leaves force-stop available and records `INTERRUPT_TIMEOUT`.
- [ ] On terminal event, cancel pending requests and transition `STOPPED` or reported terminal state.
- [ ] Test completion before request, completion after request, timeout, wrong turn, connection close, and request arriving during interruption.
- [ ] Commit: `feat: interrupt active codex turns`.

### Task 10: Add graceful stop and resume commands

**Files:**
- Create: `apps/engineering-cockpit/backend/cockpit/interactions/task_control.py`
- Modify: `apps/engineering-cockpit/backend/api/routes/cockpit_tasks.py`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/interactions/test_stop_resume.py`

- [ ] Stop: interrupt active turn, close app-server connection, retain worktree/container/thread, transition `STOPPED`.
- [ ] Resume: start a new process generation, reinitialize policy/skills, resume/read thread, then remain stopped-ready or start an explicitly supplied follow-up.
- [ ] Test no-active-turn stop, active-turn stop, repeated stop, resume from wrong state, thread missing, and policy drift.
- [ ] Do not promise continuation of an in-flight turn lost before terminal evidence.
- [ ] Commit: `feat: stop and resume cockpit tasks`.

### Task 11: Add force-stop and orphan assessment

**Files:**
- Modify: `apps/engineering-cockpit/backend/cockpit/interactions/task_control.py`
- Create: `apps/engineering-cockpit/backend/cockpit/interactions/orphan.py`
- Modify: `apps/engineering-cockpit/backend/api/routes/cockpit_tasks.py`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/interactions/test_force_stop.py`

- [ ] Require typed confirmation containing repository and task slug/ID.
- [ ] Close connection and terminate/kill only the owned wrapper process group.
- [ ] Inspect the exact task container for a possible remaining app-server using version-tested process matching plus task session metadata; never kill arbitrary `codex` processes globally.
- [ ] Mark `RECOVERY_REQUIRED` unless a terminal event already exists.
- [ ] Test confirmation mismatch, terminate success, kill fallback, orphan found/not found, process generation race, and simultaneous answer delivery.
- [ ] Commit: `feat: force-stop unrecoverable codex sessions`.

### Task 12: Add interaction audit events and attention timers

**Files:**
- Create: `apps/engineering-cockpit/backend/cockpit/interactions/audit.py`
- Create: `apps/engineering-cockpit/backend/cockpit/interactions/attention.py`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/interactions/test_audit_attention.py`

- [ ] Record actor, action, task/session/turn/request IDs, decision, timestamp, and safe summary.
- [ ] Add bounded reminder events for long-pending requests without changing status.
- [ ] Add stale-activity diagnostics for a silent running turn; do not classify it as hung automatically.
- [ ] Test reminder deduplication, no auto resolution, and sensitive free text absent from infrastructure logs.
- [ ] Commit: `feat: audit and surface pending interactions`.

### Task 13: Complete subsystem verification

```bash
cd apps/engineering-cockpit
uv run pytest backend/tests/cockpit/interactions backend/tests/api/routes/test_cockpit_interactions.py -q
uv run mypy backend/cockpit/interactions backend/api/routes/cockpit_interactions.py
uv run ruff check backend/cockpit/interactions backend/api/routes/cockpit_interactions.py
cd frontend && bun run generate-client && bun run typecheck
```

- [ ] Run a real harmless Codex task that asks a clarification, emits an approval, accepts/rejects from the API, receives a follow-up, is steered, interrupted, stopped, and resumed.
- [ ] Record all race/timeout outcomes.
- [ ] Commit: `test: verify interactive codex controls`.

## Exit criteria

Subsystem 09 is complete when every app-server request is durable and resolvable exactly once, follow-up/steer/interrupt/stop/resume have distinct enforced semantics, force-stop is explicit and recovery-safe, and all user decisions are authorized and audited without hidden auto-approval.
