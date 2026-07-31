# 06 — Owned Process Supervision and App-Server JSON-RPC Transport Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `techletes-superpowers:subagent-driven-development` or `techletes-superpowers:executing-plans`. Subsystems 01, 03, and 05 are prerequisites.

**Goal:** Add the one-owner subprocess runtime and newline-delimited JSON-RPC transport required to communicate with app-server without TTY scraping.

**Architecture:** The WSL FastAPI process owns every `devcontainer exec` child, pumps stdout/stderr continuously, serializes stdin writes, correlates JSON request IDs, and exposes typed close/error behavior. Higher-level Codex semantics are deferred to subsystem 07.

**Tech stack:** Python 3.12 asyncio, standard library subprocess/JSON/logging, template settings and redaction utilities, Pytest.

## Global constraints

- No `shell=True`.
- No PTY for app-server.
- stdout is protocol-only; stderr is diagnostic-only.
- Bound every line, queue, pending request set, and log file.
- Do not block protocol reading on database writes, browser clients, or slow consumers.
- A PID is not a reattachable session after backend restart.

---

### Task 1: Define process and connection error types

**Files:**
- Create: `apps/engineering-cockpit/backend/cockpit/runtime/errors.py`
- Create: `apps/engineering-cockpit/backend/cockpit/protocol/errors.py`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/runtime/test_errors.py`

**Interfaces:**

```python
class CockpitProcessError(RuntimeError):
    code: str

class JsonRpcError(RuntimeError):
    code: str

@dataclass(frozen=True)
class SafeFailure:
    code: str
    summary: str
    diagnostic_log_id: str | None
```

- [ ] Implement every machine code from the specification as a typed exception subclass or stable code.
- [ ] Test that `str(error)` is sanitized and detailed binary/process evidence is not exposed accidentally.
- [ ] Commit: `feat: define runtime protocol errors`.

### Task 2: Implement rotated, permission-safe diagnostic logs

**Files:**
- Create: `apps/engineering-cockpit/backend/cockpit/runtime/diagnostic_logs.py`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/runtime/test_diagnostic_logs.py`

**Interfaces:**

```python
class DiagnosticLogWriter:
    async def write_stderr(self, chunk: bytes) -> None: ...
    def tail(self, max_bytes: int) -> str: ...
    def close(self) -> None: ...
```

- [ ] Store logs under `${XDG_STATE_HOME:-~/.local/state}/techletes-cockpit/tasks/<task-id>/<session-generation>/`.
- [ ] Create directories/files with user-only permissions.
- [ ] Implement size-based rotation and a bounded in-memory tail.
- [ ] Run every exposed tail through the shared redactor.
- [ ] Test rotation, binary bytes, invalid UTF-8, permissions, and concurrent writes.
- [ ] Commit: `feat: add bounded task diagnostics`.

### Task 3: Implement `OwnedProcess`

**Files:**
- Create: `apps/engineering-cockpit/backend/cockpit/runtime/process.py`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/runtime/test_process.py`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/fakes/child_process.py`

**Interfaces:**

```python
@dataclass(frozen=True)
class OwnedProcessIdentity:
    task_id: UUID
    agent_session_id: UUID
    generation: int

class OwnedProcess:
    @classmethod
    async def spawn(... ) -> "OwnedProcess": ...
    async def write(self, payload: bytes) -> None: ...
    async def close_stdin(self) -> None: ...
    async def wait(self) -> int: ...
    async def terminate(self, grace_seconds: float) -> int: ...
    async def kill(self, timeout_seconds: float) -> int: ...
```

- [ ] Write tests for successful spawn, missing executable, stdin echo, stdout/stderr separation, child exit, cancellation, terminate, ignored terminate then kill, and process-group cleanup.
- [ ] Use `asyncio.create_subprocess_exec(..., stdin=PIPE, stdout=PIPE, stderr=PIPE, start_new_session=True)`.
- [ ] Serialize writes through an async lock and bound payload size.
- [ ] Pump stderr immediately into `DiagnosticLogWriter`.
- [ ] Expose stdout only to the protocol layer; no second consumer may read it.
- [ ] Commit: `feat: own long-running child processes`.

### Task 4: Implement the in-memory process registry

**Files:**
- Create: `apps/engineering-cockpit/backend/cockpit/runtime/process_registry.py`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/runtime/test_process_registry.py`

**Interfaces:**

```python
class ProcessRegistry:
    async def register(self, identity: OwnedProcessIdentity, process: OwnedProcess) -> None: ...
    async def get_for_task(self, task_id: UUID) -> OwnedProcess | None: ...
    async def unregister(self, identity: OwnedProcessIdentity) -> None: ...
    async def drain(self) -> None: ...
```

- [ ] Test duplicate task ownership, generation replacement after old exit, unregister race, draining shutdown, and concurrent different tasks.
- [ ] Attach one exit watcher per registered process and remove only the matching generation.
- [ ] Never reconstruct a live handle from stored PID metadata.
- [ ] Add registry counts to diagnostics.
- [ ] Commit: `feat: register owned task processes`.

### Task 5: Define JSON-RPC message and ID types

**Files:**
- Create: `apps/engineering-cockpit/backend/cockpit/protocol/models.py`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/protocol/test_models.py`

**Interfaces:**

```python
@dataclass(frozen=True)
class JsonRpcId:
    kind: Literal["integer", "string"]
    value: int | str

@dataclass(frozen=True)
class IncomingRequest: ...
@dataclass(frozen=True)
class Notification: ...
@dataclass(frozen=True)
class SuccessResponse: ...
@dataclass(frozen=True)
class ErrorResponse: ...

def classify_message(value: object) -> JsonRpcMessage: ...
```

- [ ] Test request, notification, success, error, numeric/string IDs, `null`, arrays, duplicate keys, missing fields, and omitted `jsonrpc` member.
- [ ] Keep `1` and `"1"` distinct.
- [ ] Enforce object payloads and bounded method/ID sizes.
- [ ] Commit: `feat: model app-server json-rpc messages`.

### Task 6: Implement newline framing and output limits

**Files:**
- Create: `apps/engineering-cockpit/backend/cockpit/protocol/framing.py`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/protocol/test_framing.py`

**Interfaces:**

```python
class JsonLineReader:
    async def read_message(self) -> JsonRpcMessage: ...

async def encode_line(message: Mapping[str, object], *, max_bytes: int) -> bytes: ...
```

- [ ] Test fragmented line, multiple lines in one chunk, CRLF, final EOF without newline, blank line, invalid JSON, 4 MiB boundary, and oversized line.
- [ ] Configure `StreamReader` limits or use bounded `readuntil` logic so memory cannot grow before the newline.
- [ ] Reject non-JSON stdout as `JSONRPC_INVALID_JSON` and preserve a redacted tail in diagnostics.
- [ ] Encode compact UTF-8 JSON plus exactly one newline.
- [ ] Commit: `feat: frame app-server json lines`.

### Task 7: Implement request correlation and serialized writes

**Files:**
- Create: `apps/engineering-cockpit/backend/cockpit/protocol/connection.py`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/protocol/test_connection_requests.py`

**Interfaces:**

```python
class JsonRpcConnection:
    async def start(self) -> None: ...
    async def send_request(self, method: str, params: object, timeout: float) -> object: ...
    async def send_notification(self, method: str, params: object | None = None) -> None: ...
    async def respond_result(self, request_id: JsonRpcId, result: object) -> None: ...
    async def respond_error(self, request_id: JsonRpcId, code: int, message: str) -> None: ...
    async def close(self) -> None: ...
```

- [ ] Use a monotonically increasing integer for client request IDs.
- [ ] Insert pending futures before writing; remove them in `finally`.
- [ ] Test out-of-order responses, error responses, timeout, cancellation, unknown response ID, duplicate response, write failure, and connection closure with pending requests.
- [ ] Serialize all writes through one lock and await `drain()` with timeout.
- [ ] Do not retry ambiguous writes automatically.
- [ ] Commit: `feat: correlate app-server requests`.

### Task 8: Dispatch notifications and incoming server requests

**Files:**
- Modify: `apps/engineering-cockpit/backend/cockpit/protocol/connection.py`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/protocol/test_connection_incoming.py`

**Interfaces:**

```python
IncomingRequestHandler = Callable[[IncomingRequest], Awaitable[None]]
NotificationHandler = Callable[[Notification], Awaitable[None]]
```

- [ ] Route incoming requests by exact typed ID and reject duplicates.
- [ ] Permit exactly one response for each incoming request.
- [ ] Dispatch notifications in read order into a bounded internal queue.
- [ ] Ensure a slow handler triggers explicit backpressure behavior instead of blocking the stdout pump indefinitely.
- [ ] Test unknown notification, unknown request, handler exception, duplicate incoming ID, close with unresolved request, and full queue.
- [ ] Commit: `feat: dispatch app-server incoming messages`.

### Task 9: Add connection states and close semantics

**Files:**
- Modify: `apps/engineering-cockpit/backend/cockpit/protocol/connection.py`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/protocol/test_connection_lifecycle.py`

- [ ] Implement `CREATED`, `STARTING`, `OPEN`, `CLOSING`, `CLOSED`, and `FAILED` states.
- [ ] Make `start` and `close` idempotent only where safe; duplicate `start` after open is a typed error.
- [ ] On EOF/process exit, fail pending client futures and unresolved incoming requests.
- [ ] Invoke one close callback carrying exit code and safe failure.
- [ ] Close stdin, await bounded grace, and leave process force-kill to the caller.
- [ ] Test every race: close during write, child exits during request, two close calls, handler closes connection, and cancellation.
- [ ] Commit: `feat: manage app-server connection lifecycle`.

### Task 10: Connect devcontainer launch to process ownership

**Files:**
- Create: `apps/engineering-cockpit/backend/cockpit/runtime/app_server_process.py`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/runtime/test_app_server_process.py`

**Interfaces:**

```python
class AppServerProcessFactory:
    async def start(
        self,
        *,
        task: CockpitTaskSnapshot,
        workspace: CockpitWorkspaceSnapshot,
        agent_session_id: UUID,
        generation: int,
    ) -> tuple[OwnedProcess, JsonRpcConnection]: ...
```

- [ ] Launch through `DevcontainerExecLauncher` with:

```text
codex app-server --listen stdio://
```

- [ ] Pass only approved environment overrides; rely on the target devcontainer for normal environment and `CODEX_HOME`.
- [ ] Register the process before opening the connection.
- [ ] If connection startup fails, unregister and terminate the owned wrapper.
- [ ] Test duplicate owner, stopped container, process exits immediately, and successful open with fake app-server.
- [ ] Commit: `feat: launch owned app-server connections`.

### Task 11: Integrate with FastAPI lifespan shutdown

**Files:**
- Modify: `apps/engineering-cockpit/backend/cockpit/runtime/context.py`
- Modify: `apps/engineering-cockpit/backend/main.py`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/runtime/test_process_shutdown.py`

- [ ] Add `ProcessRegistry` and process factory to the runtime context.
- [ ] On shutdown, mark draining, reject new sessions, and request higher-level interruption when available.
- [ ] Until subsystem 09 exists, close stdin and terminate wrappers after a bounded grace period.
- [ ] Persist session exit metadata through short store calls.
- [ ] Test application shutdown with zero, one, and several running fake processes.
- [ ] Commit: `feat: drain cockpit child processes`.

### Task 12: Complete subsystem verification

```bash
cd apps/engineering-cockpit
uv run pytest backend/tests/cockpit/runtime backend/tests/cockpit/protocol -q
uv run mypy backend/cockpit/runtime backend/cockpit/protocol
uv run ruff check backend/cockpit/runtime backend/cockpit/protocol
```

- [ ] Run a manual process test inside a disposable target devcontainer and verify stdout protocol and stderr diagnostics remain separate.
- [ ] Verify browser disconnection has no code path to close the process.
- [ ] Commit: `test: verify app-server process transport`.

## Exit criteria

Subsystem 06 is complete when one backend owner can launch, communicate with, and deterministically close a piped app-server process; JSON messages are bounded and correctly correlated; stderr/log growth is bounded; and every loss of connection fails pending work without pretending it can be reattached.
