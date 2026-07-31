# 07 — Codex App-Server Schema Compatibility, Threads, Turns, and Events Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `techletes-superpowers:subagent-driven-development` or `techletes-superpowers:executing-plans`. Subsystems 05 and 06 must be complete.

**Goal:** Integrate the pinned Codex app-server protocol with generated schema validation, initialization/capability checks, durable thread/turn identity, and stable normalized cockpit events.

**Architecture:** Generate and commit the official JSON schemas from the exact supported Codex binary. Validate wire messages at the boundary, isolate version-specific decoding in `backend/cockpit/codex/`, and expose stable internal operations/events to the task runner.

**Tech stack:** Pinned `@openai/codex`, app-server schema generator, Python `jsonschema`, Pydantic/dataclasses, subsystem 06 transport, Pytest fake process.

## Global constraints

- Generated protocol files are never hand-edited.
- An unrecognized Codex version cannot start a real task.
- Persist exact thread/turn/item/request IDs before dependent operations.
- Do not infer turn completion from text or silence.
- Unknown incoming requests are compatibility failures.
- Raw protocol messages never become frontend contracts.

---

### Task 1: Pin Codex and record the compatibility floor

**Files:**
- Modify: `apps/engineering-cockpit/.devcontainer/Dockerfile`
- Modify: `apps/engineering-cockpit/pyproject.toml`
- Create: `apps/engineering-cockpit/backend/cockpit/codex/version.py`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/codex/test_version.py`

**Interfaces:**

```python
@dataclass(frozen=True)
class CodexVersion:
    raw: str
    semantic: Version
    manifest_key: str | None
    supported: bool
```

- [ ] Inspect the current template-installed `codex --version` and select an exact pinned version for the first compatibility manifest.
- [ ] Replace unbounded global Codex installation with the exact version in the cockpit-derived environment while leaving target repositories free to declare an explicitly supported compatible version.
- [ ] Add `jsonschema` using `uv add` and regenerate `uv.lock`.
- [ ] Test exact supported, unsupported older, unsupported newer, malformed, and missing binary output.
- [ ] Commit: `build: pin codex app-server protocol version`.

### Task 2: Add reproducible schema generation

**Files:**
- Create: `apps/engineering-cockpit/scripts/update-codex-app-server-schema.sh`
- Create: `apps/engineering-cockpit/backend/cockpit/codex/generated/<version>/manifest.json`
- Generate: `apps/engineering-cockpit/backend/cockpit/codex/generated/<version>/**/*.json`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/codex/test_generated_schema.py`

- [ ] Write the script with `set -euo pipefail`, verify the installed version equals the requested version, generate into a temporary directory, calculate deterministic SHA-256 hashes, and atomically replace the target directory.
- [ ] Run and record the exact command accepted by the pinned binary:

```bash
codex app-server generate-json-schema --out <temporary-directory>
```

- [ ] Store required/optional methods, known limitations, Dev Container CLI range, and schema hash in `manifest.json`.
- [ ] Add a test that regenerates into a temporary directory and compares all committed files byte-for-byte after normalizing only generator timestamps declared in the manifest.
- [ ] Add generated JSON to normal source control; do not add it to formatter rewrites.
- [ ] Commit: `build: generate pinned app-server schema`.

### Task 3: Implement the schema registry and validator

**Files:**
- Create: `apps/engineering-cockpit/backend/cockpit/codex/schema_registry.py`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/codex/test_schema_registry.py`

**Interfaces:**

```python
class CodexSchemaRegistry:
    @classmethod
    def load(cls, version: CodexVersion) -> "CodexSchemaRegistry": ...
    def validate_request(self, method: str, params: object) -> None: ...
    def validate_result(self, method: str, result: object) -> None: ...
    def validate_notification(self, method: str, params: object) -> None: ...
    def validate_server_request(self, method: str, params: object) -> None: ...
```

- [ ] Discover schema entry points from generated files/manifest, not hardcoded filesystem glob order.
- [ ] Resolve `$ref` safely within the generated directory only.
- [ ] Convert schema failures to `APP_SERVER_SCHEMA_VIOLATION` with method and JSON pointer, never full secret-bearing payload.
- [ ] Test valid fixtures, wrong field type, missing required field, extra field policy, malicious external `$ref`, and unsupported method.
- [ ] Commit: `feat: validate app-server wire schemas`.

### Task 4: Build a process-level fake app-server

**Files:**
- Create: `apps/engineering-cockpit/backend/tests/cockpit/fakes/fake_app_server.py`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/fakes/scenarios/app_server/*.json`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/codex/test_fake_app_server.py`

**Scenario contract:**

```json
{
  "steps": [
    {"expectRequest": "initialize", "respond": {}},
    {"expectRequest": "thread/start", "respond": {}},
    {"expectRequest": "turn/start", "respond": {}},
    {"notify": "turn/started", "params": {}},
    {"notify": "turn/completed", "params": {}}
  ]
}
```

- [ ] Validate every scripted request/result/notification against the committed generated schemas.
- [ ] Support success, deltas, command/file changes, diff, warning, terminal error, unknown notification, unknown request, schema violation, crash, resume, user input, approvals, steering, and interruption.
- [ ] Run as a real stdin/stdout child through subsystem 06.
- [ ] Make scenario mismatches exit non-zero with deterministic stderr.
- [ ] Commit: `test: add schema-valid fake app-server`.

### Task 5: Define stable normalized Codex domain types

**Files:**
- Create: `apps/engineering-cockpit/backend/cockpit/codex/models.py`
- Create: `apps/engineering-cockpit/backend/cockpit/codex/events.py`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/codex/test_events.py`

**Interfaces:**

```python
@dataclass(frozen=True)
class CapabilitySnapshot: ...
@dataclass(frozen=True)
class CodexThreadInfo: ...
@dataclass(frozen=True)
class CodexTurnInfo: ...
@dataclass(frozen=True)
class CodexItemInfo: ...
@dataclass(frozen=True)
class NormalizedCodexEvent: ...
```

- [ ] Define the stable event enum exactly as in the spec.
- [ ] Require task/session/thread/turn/item IDs when semantically available.
- [ ] Include source method, source hash, schema version, and observed timestamp.
- [ ] Keep command output/message content in bounded fields or chunk references.
- [ ] Test JSON serialization and public redaction.
- [ ] Commit: `feat: define normalized codex events`.

### Task 6: Implement initialization and capability evaluation

**Files:**
- Create: `apps/engineering-cockpit/backend/cockpit/codex/compatibility.py`
- Create: `apps/engineering-cockpit/backend/cockpit/codex/adapter.py`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/codex/test_initialize.py`

**Interfaces:**

```python
class CodexAppServerAdapter:
    async def initialize(self) -> CapabilitySnapshot: ...
```

- [ ] Derive the exact `initialize` params and any required `initialized` notification from the generated schema and official test client for the pinned version.
- [ ] Send stable `clientInfo` name/version and only capabilities the cockpit actually implements.
- [ ] Validate response and evaluate hard/optional capability manifest.
- [ ] Persist server/Codex version, schema hash, and capability snapshot through the store.
- [ ] Test missing hard capability, unknown optional capability, initialize timeout, error response, duplicate initialize, and enterprise/client-info rejection.
- [ ] Commit: `feat: initialize codex app-server safely`.

### Task 7: Implement thread start, resume, and read

**Files:**
- Modify: `apps/engineering-cockpit/backend/cockpit/codex/adapter.py`
- Create: `apps/engineering-cockpit/backend/cockpit/codex/thread_decoder.py`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/codex/test_threads.py`

**Interfaces:**

```python
async def start_thread(config: ThreadStartConfig) -> CodexThreadInfo: ...
async def resume_thread(thread_id: str) -> CodexThreadInfo: ...
async def read_thread(thread_id: str) -> CodexThreadSnapshot: ...
```

- [ ] Build outbound params from generated schema; set the verified remote workspace folder as `cwd`/equivalent.
- [ ] Persist returned thread ID before any turn starts.
- [ ] Test start, resume, read, unknown thread, thread/workspace mismatch, schema error, and connection loss after result write.
- [ ] During resume, compare returned identity/config fingerprint and flag unexpected mismatch rather than overwriting local state.
- [ ] Commit: `feat: manage persistent codex threads`.

### Task 8: Implement turn start, steer, and interrupt protocol methods

**Files:**
- Modify: `apps/engineering-cockpit/backend/cockpit/codex/adapter.py`
- Create: `apps/engineering-cockpit/backend/cockpit/codex/turn_decoder.py`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/codex/test_turn_methods.py`

**Interfaces:**

```python
async def start_turn(thread_id: str, input_items: Sequence[CodexInputItem], config: TurnConfig) -> CodexTurnInfo: ...
async def steer_turn(thread_id: str, turn_id: str, input_items: Sequence[CodexInputItem]) -> None: ...
async def interrupt_turn(thread_id: str, turn_id: str) -> None: ...
```

- [ ] Derive exact methods/params from the pinned generated schema.
- [ ] Validate one active-turn invariant before requests.
- [ ] Persist returned turn ID before enabling controls.
- [ ] Test wrong thread/turn, unsupported steer capability, interrupt after completion, timeout, and error response.
- [ ] Do not implement browser/business rules yet.
- [ ] Commit: `feat: call codex turn operations`.

### Task 9: Normalize app-server notifications

**Files:**
- Create: `apps/engineering-cockpit/backend/cockpit/codex/normalizer.py`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/codex/test_normalizer.py`

- [ ] Add one decoder per required semantic category, using generated-schema validation first.
- [ ] Test thread/turn status, item start/complete, message delta/final, command start/output/final, file-change start/delta/final, diff, usage, warning, error, and completion.
- [ ] Hash source params after deterministic JSON encoding.
- [ ] Map unknown notification to `UNKNOWN_APP_SERVER_NOTIFICATION` with method and hash only.
- [ ] Treat schema-invalid known notification as connection-fatal.
- [ ] Never include environment values or unbounded command output in normalized event payloads.
- [ ] Commit: `feat: normalize codex app-server events`.

### Task 10: Add delta coalescing

**Files:**
- Create: `apps/engineering-cockpit/backend/cockpit/codex/coalescing.py`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/codex/test_coalescing.py`

**Interfaces:**

```python
class DeltaCoalescer:
    async def accept(self, event: NormalizedCodexEvent) -> list[NormalizedCodexEvent]: ...
    async def flush(self, *, item_id: str | None = None) -> list[NormalizedCodexEvent]: ...
```

- [ ] Coalesce adjacent deltas for the same item/channel within a short bounded interval and byte limit.
- [ ] Flush before item completion, turn completion, errors, connection close, and timeout.
- [ ] Test interleaved items, UTF-8 boundaries, maximum chunk, crash flush, and final reconstructed equality.
- [ ] Keep terminal events immediate.
- [ ] Commit: `feat: coalesce codex output deltas`.

### Task 11: Integrate app-server session lifecycle with task state

**Files:**
- Create: `apps/engineering-cockpit/backend/cockpit/codex/service.py`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/codex/test_service.py`

**Flow:**

```text
CONTAINER_READY
-> STARTING_APP_SERVER
-> INITIALIZING_APP_SERVER
-> STARTING_THREAD or RESUMING_THREAD
-> STARTING_TURN
-> RUNNING
-> terminal turn event
```

- [ ] Create a new `CockpitAgentSession` generation before process launch.
- [ ] Initialize, start/resume thread, and start turn while holding only task-operation coordination—not a database transaction.
- [ ] Persist thread/turn IDs and normalized events before fan-out.
- [ ] On terminal completion, clear active turn and transition according to completion status; do not automatically validate yet.
- [ ] On compatibility/protocol loss, persist safe failure and choose `FAILED` or `RECOVERY_REQUIRED` based on ambiguity.
- [ ] Test the complete fake success/error/crash flow.
- [ ] Commit: `feat: run codex app-server task sessions`.

### Task 12: Add compatibility diagnostics and CI drift check

**Files:**
- Modify: `apps/engineering-cockpit/backend/cockpit/repositories/diagnostics.py`
- Create: `apps/engineering-cockpit/.github/workflows/codex-schema-check.yml` or adapt root monorepo workflow
- Create: `apps/engineering-cockpit/backend/tests/cockpit/codex/test_compatibility_diagnostics.py`

- [ ] Report installed version, supported manifest, schema hash, hard/optional capability status, and known limitations.
- [ ] Add CI that installs the exact pinned Codex version, regenerates schemas, and fails on diff.
- [ ] Do not require OpenAI login for schema generation if the command does not; document any observed requirement.
- [ ] Test unsupported version blocks active diagnostics/task start.
- [ ] Commit: `ci: verify codex app-server schema compatibility`.

### Task 13: Complete subsystem verification

```bash
cd apps/engineering-cockpit
uv run pytest backend/tests/cockpit/codex backend/tests/cockpit/protocol backend/tests/cockpit/runtime -q
uv run mypy backend/cockpit/codex
uv run ruff check backend/cockpit/codex
bash scripts/update-codex-app-server-schema.sh --check
```

- [ ] Run a real app-server smoke test inside a disposable template devcontainer: initialize, start thread, start a harmless analysis turn, receive terminal completion, and stop.
- [ ] Record exact Codex version/schema hash in the compatibility manifest.
- [ ] Commit: `test: verify codex app-server core adapter`.

## Exit criteria

Subsystem 07 is complete when the exact pinned binary's generated schema is committed and reproducible, initialization/capabilities are enforced, one persistent thread per task can start/resume/read, turns can start/steer/interrupt at protocol level, all required events normalize safely, and unsupported protocol drift blocks execution instead of being guessed around.
