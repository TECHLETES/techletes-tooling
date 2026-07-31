# 10 — Durable Events, WebSocket Replay, Browser Reconnect, and Backend Recovery Specification

## Purpose

Define how task activity remains observable across browser disconnects and how the control plane recovers conservatively after its own restart. The central rule is:

> PostgreSQL stores durable orchestration events; Redis wakes live subscribers; the browser is never the process owner.

A browser may disappear at any time without affecting work. A backend restart is different: it loses all in-memory process handles and stdio connections, so the cockpit must reconcile rather than pretend to reattach.

## Event source of truth

`CockpitEvent` from subsystem 03 is the durable source. Every event is committed before live publication and has a globally monotonic integer ID.

Redis pub/sub transports only a small wake-up envelope:

```json
{
  "eventId": 12345,
  "taskId": "...",
  "ownerId": "..."
}
```

A WebSocket handler receiving the envelope fetches the committed event from PostgreSQL and applies authorization. Losing a Redis message does not lose the event; reconnect replay fills the gap.

## Event schema

Every public event contains:

- global event ID;
- event schema version;
- task ID;
- optional repository/session/thread/turn/item/protocol-request IDs;
- stable event type;
- sanitized payload;
- created timestamp.

Raw protocol JSON, environment values, credential paths, and unlimited output are excluded. Event payload migrations are versioned; the frontend supports the current version and a bounded previous-version window during rolling local upgrades.

## Publishing pipeline

```text
domain operation
  -> database transaction writes state/domain row + CockpitEvent
  -> commit
  -> publish event ID to Redis user/task channel
  -> active WebSocket connections fetch/send event
```

If Redis publication fails, record a metric/log warning; do not roll back committed domain state. A later reconnect replays it.

## WebSocket endpoint

```text
WS /api/v1/cockpit/events/ws?after_event_id=<integer>
```

Authentication follows the inherited template cookie/JWT pattern. Query-token compatibility may remain for existing clients, but the browser uses the secure session cookie where supported.

After acceptance, server sends:

```json
{
  "type": "hello",
  "serverInstanceId": "uuid",
  "currentEventId": 12345,
  "retentionFloorEventId": 1000,
  "heartbeatSeconds": 20
}
```

Then it:

1. validates `after_event_id`;
2. replays authorized events in ascending pages;
3. subscribes to the authenticated user's Redis event channel;
4. sends live events in ID order;
5. accepts client `ping`, subscription/filter, and optional acknowledgement frames;
6. closes cleanly on auth expiry, shutdown, or slow consumer.

Authorization is rechecked when loading each event/task, not trusted from the Redis envelope.

## Subscription model

Default subscription is all tasks the user can view. An optional client message narrows to a set of task IDs. Administrative users may subscribe to all tasks when `cockpit:manage` allows it.

The server must not leak existence or event counts for unauthorized task IDs. Invalid requested IDs are ignored or rejected generically.

## Replay and snapshots

Replay pages are bounded. The client persists the highest fully applied event ID in browser storage and includes it on reconnect.

If `after_event_id` is below the retention floor, the server sends `replay_reset_required` with the current retention floor. The client then:

1. reloads task/repository snapshots through REST;
2. sets its cursor to the snapshot's `currentEventId`;
3. resumes live streaming.

The event stream is not the only way to reconstruct state; REST task detail remains authoritative current state.

## Ordering and duplicates

PostgreSQL event ID defines order. WebSocket sends strictly ascending IDs per connection. The client deduplicates IDs because replay and a concurrent Redis notification can overlap.

A gap detected by the client triggers a paginated REST/WS replay request, not speculative rendering.

High-frequency delta events are coalesced in subsystem 07 before insertion. The event broker may batch sends but cannot reorder terminal events before their preceding deltas.

## Backpressure

Each WebSocket has a bounded queue. When full:

- stop accepting more live envelope work for that connection;
- close with code 1013 (`try again later`) and a safe reason;
- the client reconnects using its last applied event ID.

Do not drop arbitrary events and keep the connection open. Browser/network slowness must never block the app-server stdout reader.

## Heartbeats and presence

The server sends heartbeat frames or expects ping/pong on a configured interval. Presence is UI metadata only. A missing browser heartbeat never stops, interrupts, or pauses a task.

## Backend instance identity

Each backend process generation has a UUID and start timestamp. It is included in WebSocket hello and diagnostics. The host single-instance lock prevents two active owners.

On graceful shutdown, send `server_draining`, stop accepting new mutating commands, and close WebSockets after a bounded period. Live app-server sessions are stopped according to subsystem 09, but a sudden crash is handled by reconciliation.

## Recovery principle

After a backend restart, old Python process handles and stdio pipes are gone. Even if the target app-server process continues inside a container, it is not controllable. Recovery must terminate a positively identified orphan, open a fresh connection, and reconcile the persisted thread.

MVP does not promise transparent continuation of an in-flight model turn across backend process death.

## Orphan identification

Every app-server launch includes a non-secret environment marker:

```text
COCKPIT_AGENT_SESSION_ID=<agent-session-uuid>
COCKPIT_TASK_ID=<task-uuid>
```

The command is launched as an argv array using `env`, not shell interpolation. During recovery the cockpit inspects **only the exact persisted task container** and finds processes whose environment and command line match both IDs and `codex app-server`.

A positively identified orphan is terminated with a bounded TERM/KILL sequence and audited before a replacement process starts. No host-wide `pkill codex` or name-only container scan is permitted.

If process identity cannot be proven, mark `RECOVERY_REQUIRED` and require an operator diagnostic action.

## Startup reconciliation order

After database migrations and single-instance lock:

1. create new server instance ID;
2. load tasks in non-terminal states;
3. group by repository/task and process with bounded concurrency;
4. verify canonical repository and worktree registration;
5. inspect persisted task container ID/labels/mount;
6. mark previous agent session generation disconnected;
7. identify and terminate a proven orphan app-server;
8. start/reuse the devcontainer without rebuild if required;
9. start a fresh app-server process generation;
10. initialize authentication, skills, and permission policy;
11. resume the persisted thread;
12. read thread history and compare exact known turn/item IDs;
13. inspect Git status/head;
14. choose a deterministic recovery outcome;
15. publish recovery events.

No missing worktree is recreated automatically. No container is rebuilt automatically. No new model turn is started automatically.

## Recovery outcome matrix

### Worktree missing or Git identity mismatch

`RECOVERY_REQUIRED`. Do not create a replacement path.

### Container missing/stopped, worktree intact

Run ordinary `devcontainer up` without rebuild, then continue.

### Thread missing/unreadable

`RECOVERY_REQUIRED`; preserve worktree/container for manual analysis.

### Previously active turn now has terminal history

Reconcile missing terminal/items/events idempotently, clear active turn, and transition to the corresponding ready/stopped/failed state.

### Previously active turn has no terminal history

`RECOVERY_REQUIRED` with reason `LOST_IN_FLIGHT_TURN`. The user may review diff and start a follow-up after acknowledgement; the cockpit does not replay the previous prompt automatically.

### No active turn, thread resumes cleanly

Transition to `STOPPED`/ready-for-follow-up with current diff/status.

### Unresolved protocol request from lost connection

Mark `DELIVERY_FAILED`; do not resend its response on the new connection. Recovery required if the turn remains ambiguous.

## Reconciliation idempotency

Each recovery run has an ID. Domain updates use exact external IDs and unique constraints. Re-running after another crash must not duplicate events, turns, or requests. Recovery intent/result events distinguish steps already completed.

## Browser behavior during backend restart

The client:

- shows connection-lost state without marking tasks stopped;
- retries with exponential backoff and jitter;
- compares `serverInstanceId` on hello;
- reloads snapshots when instance changes;
- replays after its last applied event ID;
- displays `RECOVERY_REQUIRED` tasks prominently.

No optimistic mutating command is assumed successful after a network error; idempotency keys allow safe retry.

## Failure taxonomy

- `EVENT_PUBLISH_FAILED`
- `EVENT_REPLAY_CURSOR_INVALID`
- `EVENT_REPLAY_BELOW_RETENTION`
- `EVENT_CONSUMER_TOO_SLOW`
- `RECOVERY_WORKTREE_MISSING`
- `RECOVERY_GIT_IDENTITY_MISMATCH`
- `RECOVERY_CONTAINER_IDENTITY_MISMATCH`
- `RECOVERY_ORPHAN_UNCONFIRMED`
- `RECOVERY_ORPHAN_TERMINATE_FAILED`
- `RECOVERY_THREAD_MISSING`
- `RECOVERY_HISTORY_MISMATCH`
- `RECOVERY_LOST_IN_FLIGHT_TURN`
- `RECOVERY_PROTOCOL_REQUEST_UNDELIVERED`

## Testing strategy

Event tests:

- database-first commit then Redis publication;
- Redis outage with successful replay;
- ordering, duplicate envelope, replay/live overlap, cursor gaps;
- unauthorized event/subscription;
- slow consumer close/reconnect;
- retention-floor reset and snapshot;
- heartbeat and auth expiry.

Recovery tests:

- browser reconnect while backend remains alive;
- backend graceful restart and hard process death;
- running/stopped/missing/mismatched container;
- missing/moved worktree;
- proven orphan terminate and unprovable orphan;
- thread resume/read success/failure;
- terminal history discovered after crash;
- lost in-flight turn;
- unresolved approval;
- crash during recovery and idempotent second reconciliation;
- two tasks recovered concurrently without violating global limits.

## Acceptance criteria

- Browser closure or slowness never blocks or stops a task.
- Every committed event can be replayed by cursor until retention pruning.
- Live Redis loss cannot lose durable state.
- Backend instance changes are visible and trigger snapshot/replay.
- A restart never claims to own an old stdio connection.
- Proven orphan app-server processes are stopped narrowly and audited.
- Thread history and Git state are reconciled by exact identity.
- Ambiguous in-flight work becomes `RECOVERY_REQUIRED`, not silently re-run.

## Research basis

- [FastAPI WebSockets](https://fastapi.tiangolo.com/advanced/websockets/)
- [Redis pub/sub](https://redis.io/docs/latest/develop/interact/pubsub/)
- [PostgreSQL transactions](https://www.postgresql.org/docs/current/tutorial-transactions.html)
- [OpenAI app-server thread resume/read](https://github.com/openai/codex/blob/main/codex-rs/app-server/README.md)
