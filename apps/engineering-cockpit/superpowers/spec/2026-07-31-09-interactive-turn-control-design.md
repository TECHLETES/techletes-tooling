# 09 — Clarification, Approvals, Follow-Up, Steering, Interruption, and Force-Stop Specification

## Purpose

Define every human-in-the-loop interaction between a browser user and an active Codex app-server task. This subsystem converts version-specific server requests and turn controls into durable, authorized, race-safe cockpit commands.

No response is inferred from browser presence, timeout, or model text. Clarifications and approvals remain pending until an authorized user resolves them or the owning app-server connection is lost.

## Interaction categories

### Server-to-client request

App-server sends a JSON-RPC request that requires exactly one response. Supported semantic kinds:

- user clarification / request for additional information;
- command execution approval;
- file-change or patch approval;
- any future required request explicitly listed in the pinned compatibility manifest.

Subsystem 07 validates and decodes the wire message. This subsystem persists, presents, authorizes, and responds.

### Follow-up turn

The user sends additional instructions after the previous turn reached a terminal state. A new turn starts on the same thread.

### Steering

The user adds or changes context while a compatible turn is active. The exact persisted active turn ID is required.

### Interruption

The user requests protocol-level cancellation of the active turn. The cockpit waits for the terminal app-server event.

### Force-stop

The user explicitly terminates the owned `devcontainer exec` wrapper after interruption failed or the connection is unusable. Force-stop is not interruption and cannot promise that the in-container process is gone.

## Durable request lifecycle

`CockpitProtocolRequest` states:

```text
PENDING
ANSWERING
ANSWERED
REJECTED
EXPIRED
DELIVERY_FAILED
CANCELLED_BY_TURN_END
```

Creation sequence:

1. app-server adapter receives and schema-validates the incoming request;
2. normalize safe prompt/options and exact typed external request ID;
3. in one PostgreSQL transaction:
   - insert the request if `(session, external_request_id)` is new;
   - transition task to `WAITING_FOR_INPUT` or `WAITING_FOR_APPROVAL` when appropriate;
   - insert the durable event;
4. commit;
5. publish the event to browser subscribers.

If the same external request is observed twice, the second observation must match the stored method/payload hash. A mismatch is a protocol failure.

## Multiple pending requests

The model does not assume only one request can exist. A task may have several pending requests, although the pinned app-server acceptance suite records observed behavior.

Task attention remains waiting until all blocking requests for the active turn are resolved or cancelled. The task returns to `RUNNING` only when:

- delivery of the selected response succeeded for the last blocking request;
- the app-server connection remains open;
- the turn is still active.

## Public request representation

The browser receives a normalized model containing:

- cockpit request UUID and version;
- task/session/turn IDs;
- semantic kind;
- title/prompt/description;
- one or more question IDs when the protocol groups questions;
- protocol-provided options with labels/descriptions;
- whether free text is allowed/required;
- whether rejection is allowed;
- safe command/file-change summary when applicable;
- creation time and current status.

It never receives raw unredacted command environment, credential material, or arbitrary protocol JSON.

## Resolution API

```text
POST /api/v1/cockpit/protocol-requests/{id}/resolve
```

Request includes:

- expected request version;
- selected option IDs and/or free-text answers keyed by exact question ID;
- approve/reject decision when applicable;
- optional user note stored in audit history, not sent unless schema requires it.

Authorization requires task ownership plus `cockpit:operate`, or `cockpit:manage` for administrative intervention.

Resolution flow:

1. acquire task operation lock;
2. load request and active session/turn;
3. verify status `PENDING`, expected version, user authorization, and exact owning connection generation;
4. validate answer shape/options against the persisted normalized request;
5. transition request to `ANSWERING` and commit an intent event;
6. send the exact schema-valid JSON-RPC result/error against the exact external request ID;
7. on successful write, mark `ANSWERED`/`REJECTED` and commit result event;
8. recalculate task waiting/running state.

If the connection closes or write result is ambiguous after step 5, mark `DELIVERY_FAILED` and task `RECOVERY_REQUIRED`. Never retry an approval automatically on a new connection.

## Stale and duplicate responses

Return HTTP 409 when:

- request is already resolved;
- expected version is stale;
- active session generation changed;
- active turn ended;
- browser sends an option/question not in the persisted request;
- another browser tab is already answering.

The original resolution result is returned for an idempotent repeat with the same idempotency key/body.

## Request expiry and turn completion

No clarification or approval is auto-approved or auto-rejected on timeout.

If the owning turn reaches terminal state while requests remain pending, mark them `CANCELLED_BY_TURN_END` and emit an audit event. If app-server explicitly cancels/resolves a server request, reflect that exact protocol event.

A configurable attention timer may notify the user repeatedly at bounded intervals; it does not change the request state.

## Follow-up turns

Endpoint:

```text
POST /api/v1/cockpit/tasks/{task_id}/follow-up
```

Preconditions:

- initialized live app-server connection;
- persisted thread ID;
- no active turn;
- task in a resumable/ready/stopped state allowed by the state map;
- no unresolved protocol request;
- expected task version matches.

Build context through subsystem 08, call `turn/start`, persist the returned turn ID, transition to `RUNNING`, and emit events. A follow-up is not implemented as a new thread unless the user explicitly creates a new task.

## Steering

Endpoint:

```text
POST /api/v1/cockpit/tasks/{task_id}/steer
```

Preconditions:

- pinned version advertises supported steering;
- exact active thread and turn IDs match request;
- task is `RUNNING`, not waiting for a server request or interrupting;
- input passes context/size validation.

Call the schema-defined `turn/steer`. Persist an intent event before the request and result event afterward. If completion wins the race, return HTTP 409 with the terminal state; do not create a surprise follow-up.

## Interruption

Endpoint:

```text
POST /api/v1/cockpit/tasks/{task_id}/interrupt
```

Flow:

1. verify exact active turn;
2. transition to `INTERRUPTING` and persist intent;
3. call `turn/interrupt`;
4. wait for the schema-defined terminal event up to configured timeout;
5. clear active turn, cancel remaining requests, and transition to `STOPPED` or the reported terminal state.

A successful interrupt request response alone is not terminal proof.

## Force-stop

Endpoint:

```text
POST /api/v1/cockpit/tasks/{task_id}/force-stop
```

Requires:

- explicit UI confirmation containing repository/task identity;
- `cockpit:manage` or owner plus configured permission;
- active connection/process evidence;
- no simultaneous cleanup/rebuild.

Flow:

1. record force-stop intent;
2. close the connection and terminate/kill the owned wrapper through subsystem 06;
3. inspect the task container for possible orphan app-server processes;
4. transition to `RECOVERY_REQUIRED` unless the turn had already produced a terminal event;
5. provide an explicit orphan-cleanup/recovery action.

Force-stop never directly deletes the worktree or container.

## Stop/resume terminology

- **Interrupt:** stop current turn through protocol.
- **Stop task:** interrupt current turn if any, close app-server connection cleanly, retain worktree/container/thread, transition `STOPPED`.
- **Resume task:** start a fresh app-server generation, resume thread, then wait for user follow-up or start a requested turn.
- **Force-stop:** kill owned process after confirmation; recovery required.
- **Cleanup:** subsystem 14 removes runtime/worktree after safety checks.

The UI must use these terms consistently.

## Races

Every operation uses task lock, expected task version, expected session generation, and expected turn ID.

Required race outcomes:

- completion before steer: steer 409, no follow-up;
- completion while interrupting: accept terminal event and finish cleanly;
- two tabs resolve one request: one success, one idempotent replay or 409;
- app-server disconnect during answer: `DELIVERY_FAILED` + recovery;
- request arrives during interrupt: persist then cancel when terminal event arrives;
- force-stop while answer delivery is active: serialized by task lock.

## Audit and security

Persist actor user ID, action, task/session/turn/request IDs, decision, timestamp, and safe summary. Do not store sensitive free text in infrastructure logs; task conversation/event storage follows retention policy.

Command approval UI must clearly show:

- executable/argv summary;
- working directory;
- sandbox reason/risk supplied by protocol;
- whether network/escalation is requested;
- approve/reject effect.

File-change approval must show affected paths and change summary/diff reference. Never render raw ANSI/HTML.

## Failure taxonomy

- `PROTOCOL_REQUEST_DUPLICATE`
- `PROTOCOL_REQUEST_PAYLOAD_MISMATCH`
- `PROTOCOL_REQUEST_STALE`
- `PROTOCOL_REQUEST_INVALID_RESPONSE`
- `PROTOCOL_REQUEST_UNAUTHORIZED`
- `PROTOCOL_REQUEST_DELIVERY_FAILED`
- `FOLLOW_UP_ACTIVE_TURN`
- `STEER_UNSUPPORTED`
- `STEER_TURN_MISMATCH`
- `INTERRUPT_TURN_MISMATCH`
- `INTERRUPT_TIMEOUT`
- `FORCE_STOP_CONFIRMATION_REQUIRED`
- `APPROVAL_PROTOCOL_STALLED`

## Testing strategy

- all request kinds, multiple questions/options/free text;
- persist-before-broadcast ordering;
- approve, reject, invalid option, stale version, duplicate tab, idempotent retry;
- multiple pending requests and state recalculation;
- turn completes with pending request;
- connection closes before/during/after answer write;
- follow-up on same thread;
- follow-up blocked by active turn/request;
- steer success and completion race;
- interrupt success, timeout, completion race, and request arrival;
- force-stop wrapper plus orphan diagnostic;
- auth/RBAC checks;
- no secret/ANSI/HTML leakage.

## Acceptance criteria

- Every server request is durable before notification.
- Browser answers map to the exact protocol request and are delivered at most once.
- No request is auto-approved.
- Follow-up, steering, interruption, stop, resume, and force-stop have distinct semantics and UI controls.
- All races result in deterministic state or `RECOVERY_REQUIRED`, never silent continuation.
- Audit history identifies who made every consequential decision.

## Research basis

- [OpenAI Codex app-server README](https://github.com/openai/codex/blob/main/codex-rs/app-server/README.md)
- [OpenAI app-server test client](https://github.com/openai/codex/blob/main/codex-rs/app-server-test-client/README.md)
- [FastAPI status and dependency patterns](https://fastapi.tiangolo.com/)
