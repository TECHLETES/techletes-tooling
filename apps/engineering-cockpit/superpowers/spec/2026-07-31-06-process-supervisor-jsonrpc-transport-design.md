# 06 — Owned Process Supervision and App-Server JSON-RPC Transport Specification

## Purpose

Define the low-level runtime that owns one long-lived `devcontainer exec ... codex app-server` process per active task and provides a reliable, bounded, bidirectional protocol connection to higher-level Codex code.

This subsystem deliberately knows nothing about Codex thread semantics. It owns processes, pipes, framing, request correlation, cancellation, diagnostics, and connection failure. Subsystem 07 implements app-server methods and events on top of it.

## Process topology

```text
single FastAPI control-plane process in WSL
  -> ProcessRegistry
      -> task/session generation
          -> child process: devcontainer exec ... codex app-server --listen stdio://
              stdin  <- JSON request/response/notification lines
              stdout -> protocol lines only
              stderr -> diagnostic text only
```

The backend process that creates the child is the sole owner of its stdin/stdout/stderr. RQ workers, browser clients, other Uvicorn workers, and tmux sessions never own or proxy the app-server protocol.

## Owned process contract

An `OwnedProcess` exposes:

- immutable process/session identity;
- PID and process-group metadata for diagnostics;
- async stdin writes;
- separate stdout and stderr readers;
- exit future/status;
- graceful stdin close;
- terminate and kill operations;
- bounded diagnostic log location;
- start/end timestamps;
- a monotonically updated last-I/O timestamp.

The process is started with `asyncio.create_subprocess_exec`, explicit argument arrays, pipes, and a new process group/session. `shell=True` is prohibited.

## Wrapper versus in-container process

The child PID belongs to `devcontainer exec`, not necessarily the inner app-server process. Terminating the wrapper may not prove that the inner process is gone. Therefore:

- protocol interruption is the normal stop path in subsystem 09;
- process termination is a force-stop of the owned wrapper;
- subsystem 10 detects and cleans up possible orphan app-server processes through the known task container;
- a backend restart cannot reattach to the old stdio stream.

The cockpit never claims otherwise.

## Process registry

The in-memory `ProcessRegistry` is keyed by task ID and session generation. Rules:

- at most one active owned app-server process per task;
- registration occurs before pumps begin;
- duplicate registration is rejected;
- exit removes the live owner but keeps durable session metadata;
- shutdown marks the registry draining and rejects new processes;
- registry lookups return handles only within the current backend process generation.

A durable PID is diagnostic, not a recovery handle.

## Output limits and backpressure

Raw child output is untrusted and potentially unbounded.

### stdout

- expected to contain newline-delimited protocol JSON only;
- maximum line size is configurable, default 4 MiB;
- maximum undecoded buffer is bounded;
- a non-JSON/non-protocol line is a connection-fatal protocol violation and is copied to sanitized diagnostics;
- stdout is consumed continuously regardless of browser state.

### stderr

- consumed continuously into a bounded in-memory tail and a rotated local log;
- never parsed as protocol;
- sanitized before UI/database exposure;
- file permissions are user-only;
- default retention/rotation is defined in subsystem 14.

### queues

The protocol reader dispatches to bounded internal queues. Higher-level notification handlers must not await browser delivery inline. If a consumer cannot keep up, the connection fails with an explicit backpressure error rather than consuming unlimited memory.

## JSON-RPC framing

Codex app-server uses newline-delimited JSON messages shaped like JSON-RPC requests, responses, errors, and notifications. Current app-server transport omits the standard `"jsonrpc": "2.0"` member, so the parser must use the generated Codex schema/shape rather than require that field.

Message classification:

- object with `method` and `id`: incoming request;
- object with `method` and no `id`: notification;
- object with `id` and `result`: successful response;
- object with `id` and `error`: error response;
- anything else: protocol violation.

IDs may be numbers or strings. They are normalized to a tagged internal value so `1` and `"1"` remain distinct.

One complete JSON object is written per line. Writes are serialized through an async lock and followed by `drain()`.

## Client request correlation

`JsonRpcConnection.send_request`:

1. allocates a monotonically increasing numeric client ID;
2. inserts a pending future before writing;
3. writes one request line;
4. waits with a method-specific timeout;
5. resolves on matching response/error;
6. removes the pending entry in all exit paths.

Responses may arrive out of order. Unknown, duplicate, or already-completed response IDs are protocol errors recorded with evidence.

No request is retried automatically after an ambiguous write or disconnect. Higher-level methods decide whether an operation is safely repeatable.

## Incoming server requests

For a server-to-client request, the transport:

1. validates ID uniqueness among unresolved incoming requests;
2. publishes a typed callback with method, ID, and raw typed params;
3. keeps the request pending until higher-level code responds;
4. permits exactly one `send_result` or `send_error` call;
5. fails unresolved requests when the connection closes.

Subsystem 09 persists the request before exposing it to the browser. The transport itself does not write database rows.

## Notifications

Notifications are dispatched to a registered handler without response. Ordering is preserved as read from stdout. The handler returns quickly after placing the normalized work on an internal queue.

Unknown notifications are retained as versioned diagnostic events but do not necessarily terminate the connection. Unknown requests are rejected with a method-not-found error only when the current generated protocol allows that behavior; otherwise the adapter marks incompatibility.

## Connection lifecycle

States:

```text
CREATED
STARTING
OPEN
CLOSING
CLOSED
FAILED
```

Open requires the process to be running and all pumps installed. Connection close:

- prevents new requests;
- fails all pending client futures;
- marks incoming requests undeliverable;
- closes stdin;
- waits a bounded grace period;
- records process exit or leaves force-stop to the caller;
- invokes one close callback.

Close is idempotent.

## Timeouts and liveness

Timeout classes are separate:

- process start timeout;
- protocol initialization timeout;
- ordinary request timeout;
- stdin drain timeout;
- graceful close timeout;
- force-kill timeout.

Silence during model work is not automatically treated as a hang. The registry exposes last protocol activity and process state; the UI may show “no recent events.” A user or recovery policy decides whether to interrupt. Only an explicit protocol/request timeout fails an operation automatically.

## Logging and redaction

Persist/log:

- task/session IDs;
- method names;
- request IDs;
- message byte counts;
- timing and exit status;
- safe error codes;
- bounded sanitized stderr.

Do not persist/log:

- environment values;
- full prompts or model content in infrastructure logs;
- authentication material;
- raw tool output without the event-specific sanitization policy;
- arbitrary full JSON protocol dumps by default.

A developer-only protocol trace can be enabled per task, with a warning and short retention, but still passes through redaction.

## Error taxonomy

- `PROCESS_SPAWN_FAILED`
- `PROCESS_DUPLICATE_OWNER`
- `PROCESS_OUTPUT_LIMIT`
- `PROCESS_STDIN_CLOSED`
- `PROCESS_EXITED`
- `PROCESS_TERMINATE_TIMEOUT`
- `JSONRPC_INVALID_JSON`
- `JSONRPC_INVALID_MESSAGE`
- `JSONRPC_LINE_TOO_LARGE`
- `JSONRPC_UNKNOWN_RESPONSE_ID`
- `JSONRPC_DUPLICATE_RESPONSE`
- `JSONRPC_DUPLICATE_INCOMING_REQUEST`
- `JSONRPC_REQUEST_TIMEOUT`
- `JSONRPC_CONNECTION_CLOSED`
- `JSONRPC_BACKPRESSURE`

## Security

- strict argv arrays;
- minimal environment allowlist merged with required inherited environment;
- working directory fixed to the registered worktree;
- logs stored under a cockpit-controlled directory, not the target repository;
- restrictive log permissions;
- no terminal escape rendering;
- message size and pending-request limits;
- process group signals target only the owned wrapper group.

## Testing strategy

Deterministic child programs exercise:

- stdin echo and bidirectional messages;
- fragmented writes and multiple lines in one OS read;
- out-of-order responses;
- numeric and string IDs;
- notifications and incoming requests;
- duplicate/unknown IDs;
- malformed JSON and oversize lines;
- stderr flood and rotation boundary;
- child exit before/after response;
- request timeout;
- cancellation during write/wait;
- process termination and forced kill;
- consumer backpressure;
- registry duplicate ownership and draining shutdown.

The fake app-server in subsystem 07 uses this transport rather than bypassing it.

## Acceptance criteria

- One backend process owns one process/connection per active task.
- stdin/stdout/stderr remain separate and continuously drained.
- JSON messages are framed and correlated without requiring the omitted `jsonrpc` field.
- Out-of-order responses and server requests work.
- Memory and log growth are bounded.
- Connection loss deterministically fails pending work.
- Browser disconnection has no effect on process ownership.
- Backend restart is explicitly non-reattachable and leaves evidence for recovery.

## Research basis

- [Python asyncio subprocesses](https://docs.python.org/3/library/asyncio-subprocess.html)
- [JSON-RPC 2.0](https://www.jsonrpc.org/specification)
- [OpenAI Codex app-server protocol](https://github.com/openai/codex/blob/main/codex-rs/app-server/README.md)
- [Uvicorn process management](https://www.uvicorn.org/deployment/)
