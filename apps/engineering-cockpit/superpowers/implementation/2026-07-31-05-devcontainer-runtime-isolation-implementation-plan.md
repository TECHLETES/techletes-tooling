# 05 — Devcontainer Lifecycle, Docker Isolation, Caching, Paths, and Ports Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `techletes-superpowers:subagent-driven-development` or `techletes-superpowers:executing-plans`. Subsystems 01–04 are prerequisites.

**Goal:** Implement a version-tested Dev Container adapter that starts or reuses the task worktree environment, verifies runtime identity, executes commands with pipes, detects unsafe resource sharing, and exposes precise cleanup metadata.

**Architecture:** Use the official `devcontainer` CLI for configuration, startup, and execution. Use a narrow Docker inspection adapter for persisted container identity and operations the CLI does not expose. Keep configuration resolution and runtime ownership separate.

**Tech stack:** Pinned `@devcontainers/cli`, Docker CLI/Engine, Python asyncio, Pydantic/SQLModel, PyYAML for static Compose diagnostics, Pytest.

## Global constraints

- Do not reimplement Dev Container configuration resolution.
- Do not rebuild on normal resume.
- Do not use broad Docker filters or global prune operations.
- Store only sanitized configuration metadata and fingerprints.
- Treat mutable volumes and published ports as task-isolation concerns.
- Real target commands always execute inside the task devcontainer.

---

### Task 1: Pin and diagnose the Dev Container CLI

**Files:**
- Modify: `apps/engineering-cockpit/pyproject.toml` only if Python dependencies are needed
- Modify: `apps/engineering-cockpit/.devcontainer/Dockerfile`
- Create: `apps/engineering-cockpit/backend/cockpit/devcontainers/version.py`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/devcontainers/test_version.py`

**Interfaces:**

```python
@dataclass(frozen=True)
class DevcontainerCliVersion:
    raw: str
    semantic: Version
    supported: bool

async def read_devcontainer_version(runner: CommandRunner) -> DevcontainerCliVersion: ...
```

- [ ] Select and document the exact tested CLI version range after running `devcontainer --version` in WSL and the inherited devcontainer.
- [ ] Pin installation in the template-derived setup rather than using unbounded `latest` for CI.
- [ ] Write tests for supported, below-floor, above-tested-major, malformed, and missing executable cases.
- [ ] Expose the result through repository diagnostics.
- [ ] Commit: `build: pin devcontainer cli compatibility`.

### Task 2: Add resolved configuration models and sanitization

**Files:**
- Create: `apps/engineering-cockpit/backend/cockpit/devcontainers/models.py`
- Create: `apps/engineering-cockpit/backend/cockpit/devcontainers/configuration.py`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/devcontainers/test_configuration.py`

**Interfaces:**

```python
@dataclass(frozen=True)
class ResolvedDevcontainerConfiguration:
    config_path: Path
    workspace_folder: Path
    remote_workspace_folder: str
    remote_user: str | None
    service: str | None
    compose_files: tuple[Path, ...]
    dockerfile: Path | None
    lifecycle_commands: Mapping[str, object]
    sanitized_fingerprint: str
```

- [ ] Build a fake CLI response fixture from the pinned `read-configuration` output.
- [ ] Invoke `devcontainer read-configuration --workspace-folder <path>` and parse only the structured result.
- [ ] Normalize referenced paths relative to the config file and enforce repository containment.
- [ ] Redact environment values, credential mount sources, and unrelated host paths before persistence.
- [ ] Hash relevant file content and normalized paths deterministically.
- [ ] Test missing references, symlink escape, paths with spaces, and malformed JSON.
- [ ] Commit: `feat: resolve target devcontainer configuration`.

### Task 3: Implement static Compose/resource diagnostics

**Files:**
- Modify: `apps/engineering-cockpit/pyproject.toml` to add the selected YAML parser
- Create: `apps/engineering-cockpit/backend/cockpit/devcontainers/compose_diagnostics.py`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/devcontainers/test_compose_diagnostics.py`

**Interfaces:**

```python
class RuntimeDiagnosticSeverity(str, Enum): ...

@dataclass(frozen=True)
class RuntimeDiagnostic:
    code: str
    severity: RuntimeDiagnosticSeverity
    file: Path | None
    service: str | None
    message: str
    evidence: dict[str, object]
```

- [ ] Test fixed `container_name`, top-level `name`, external/global mutable volume, fixed host port, dynamic host port, Docker socket mount, approved cache volume, bind escape, and environment interpolation.
- [ ] Parse Compose YAML as a best-effort static check; never claim it is the fully resolved Compose model.
- [ ] Classify the template's uv/pre-commit volumes as allowed shared caches and PostgreSQL data as task-specific.
- [ ] Mark a fixed published port as a blocker only when concurrent runtime is requested and no task override exists.
- [ ] Commit: `feat: diagnose devcontainer resource conflicts`.

### Task 4: Build fake Dev Container and Docker adapters

**Files:**
- Create: `apps/engineering-cockpit/backend/tests/cockpit/fakes/fake_devcontainer.py`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/fakes/fake_docker.py`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/fakes/scenarios/devcontainer/*.json`

**Capabilities:**

- `read-configuration` success/failure;
- `up` first-create/reuse/recreate/malformed result/lifecycle failure/timeout;
- `exec` with stdin/stdout/stderr and exit status;
- Docker inspect for running/stopped/missing/mismatched containers;
- Compose labels, task labels, mounts, ports, and volumes.

- [ ] Make the fake executable use newline-delimited scenario commands and deterministic IDs.
- [ ] Ensure tests require no Docker daemon.
- [ ] Include a scenario where stdout contains logs before the final structured result so parsing is version-contract tested.
- [ ] Commit: `test: add fake devcontainer runtime`.

### Task 5: Implement Docker inspection without broad ownership

**Files:**
- Create: `apps/engineering-cockpit/backend/cockpit/devcontainers/docker_adapter.py`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/devcontainers/test_docker_adapter.py`

**Interfaces:**

```python
@dataclass(frozen=True)
class DockerContainerInfo:
    container_id: str
    running: bool
    labels: Mapping[str, str]
    mounts: tuple[DockerMount, ...]
    ports: tuple[PublishedPort, ...]
    compose_project: str | None

class DockerAdapter:
    async def inspect_container(self, container_id: str) -> DockerContainerInfo | None: ...
    async def stop_container(self, container_id: str, timeout: int) -> None: ...
    async def list_containers_by_exact_labels(self, labels: Mapping[str, str]) -> list[DockerContainerInfo]: ...
```

- [ ] Parse `docker inspect` JSON, not table output.
- [ ] Test missing container, exact label matching, task-label mismatch, compose labels, workspace mount, dynamic ports, and stop failure.
- [ ] Require full container IDs in stored state; accept short IDs only in display models.
- [ ] Do not implement volume deletion in this subsystem.
- [ ] Commit: `feat: inspect task devcontainer resources`.

### Task 6: Implement `up` and identity verification

**Files:**
- Create: `apps/engineering-cockpit/backend/cockpit/devcontainers/adapter.py`
- Create: `apps/engineering-cockpit/backend/cockpit/devcontainers/errors.py`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/devcontainers/test_adapter_up.py`

**Interfaces:**

```python
@dataclass(frozen=True)
class DevcontainerRuntimeInfo:
    container_id: str
    remote_workspace_folder: str
    remote_user: str | None
    runtime_kind: str
    compose_project: str | None
    created_or_recreated: bool
    fingerprint: str

class DevcontainerAdapter:
    async def up(
        self,
        *,
        task_id: UUID,
        workspace_id: UUID,
        worktree_path: Path,
        rebuild: bool = False,
    ) -> DevcontainerRuntimeInfo: ...
```

- [ ] Test first create, reuse, stopped container, missing container, explicit rebuild, identity mismatch, initialize failure, lifecycle failure, timeout, and malformed terminal result.
- [ ] Pass stable `--id-label` values only after the version capability test proves support.
- [ ] Parse the pinned CLI's final structured result and inspect the returned container.
- [ ] Verify exact task/workspace labels, running state, and workspace mount source.
- [ ] Run a readiness command such as `pwd` and `id -un` through `exec`; require the expected remote workspace/user.
- [ ] Persist intent/result through the task store outside the adapter.
- [ ] Assert the ordinary resume call path never sets `rebuild=True`.
- [ ] Commit: `feat: start and verify task devcontainers`.

### Task 7: Implement bidirectional `exec` process launch

**Files:**
- Create: `apps/engineering-cockpit/backend/cockpit/devcontainers/exec.py`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/devcontainers/test_exec.py`

**Interfaces:**

```python
class DevcontainerExecLauncher:
    async def spawn(
        self,
        *,
        worktree_path: Path,
        argv: Sequence[str],
        env: Mapping[str, str] | None = None,
    ) -> OwnedProcess: ...
```

- [ ] Initially define `OwnedProcess` as a Protocol compatible with subsystem 06; use a test double until subsystem 06 lands.
- [ ] Test stdin forwarding, stdout/stderr separation, non-zero exit, missing executable, stopped container, cancellation, and paths with spaces.
- [ ] Build an argument vector; do not wrap the target command in `bash -lc` unless a repository validation command explicitly requires a shell through subsystem 11's allowlisted command model.
- [ ] Confirm no TTY is requested for app-server stdio.
- [ ] Commit: `feat: execute piped commands in devcontainers`.

### Task 8: Add runtime service and state integration

**Files:**
- Create: `apps/engineering-cockpit/backend/cockpit/devcontainers/service.py`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/devcontainers/test_service.py`

- [ ] Acquire the task lock and container-start semaphore.
- [ ] Transition `WORKTREE_READY -> STARTING_CONTAINER -> CONTAINER_READY` only after readiness verification.
- [ ] Save container ID, remote workspace, remote user, runtime kind, compose project, fingerprint, and inspection time in `CockpitWorkspace`.
- [ ] Make repeated start idempotent when persisted and inspected identity agree.
- [ ] On drift, persist `DEVCONTAINER_DRIFT_DETECTED`; do not rebuild automatically.
- [ ] Emit sanitized diagnostics and timings.
- [ ] Commit: `feat: integrate devcontainer task lifecycle`.

### Task 9: Add explicit runtime stop/rebuild operations

**Files:**
- Create: `apps/engineering-cockpit/backend/cockpit/devcontainers/operations.py`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/devcontainers/test_operations.py`

- [ ] Implement stop of the verified primary container and exact task-labeled Compose containers, preserving volumes.
- [ ] Refuse stop while an owned app-server/process is active unless subsystem 09 has interrupted or force-stopped it.
- [ ] Implement explicit rebuild as a separate operation that records the old/new container IDs and requires no active app-server.
- [ ] Test label mismatch, partial Compose stop, already stopped, rebuild failure, and no-rebuild resume.
- [ ] Leave container/network/volume deletion to subsystem 14.
- [ ] Commit: `feat: control task devcontainer runtime`.

### Task 10: Run a real two-worktree smoke test

**Files:**
- Create: `apps/engineering-cockpit/backend/tests/manual/devcontainer_two_worktrees.md`
- Create: `apps/engineering-cockpit/scripts/check-devcontainer-concurrency.sh`

- [ ] Clone or use a disposable copy of `TECHLETES/full-stack-template` in WSL.
- [ ] Create two worktrees and run the adapter against both.
- [ ] Verify distinct primary container IDs, Compose projects, PostgreSQL volumes, and worktree mounts.
- [ ] Verify shared uv/pre-commit caches are the only intentionally shared named volumes.
- [ ] Run inside each:

```bash
pwd
id -un
codex --version
uv sync --locked
```

- [ ] Stop one runtime and prove the other remains healthy.
- [ ] Record the tested Docker, Dev Container CLI, and Codex versions.
- [ ] Commit: `test: verify concurrent devcontainer isolation`.

### Task 11: Complete subsystem verification

```bash
cd apps/engineering-cockpit
uv run pytest backend/tests/cockpit/devcontainers -q
uv run mypy backend/cockpit/devcontainers
uv run ruff check backend/cockpit/devcontainers
```

Expected: all fake/contract tests pass and the manual two-worktree checklist has recorded evidence.

## Exit criteria

Subsystem 05 is complete when the cockpit can start or reuse a real task devcontainer without rebuilding, verify exact runtime identity, execute a bidirectional non-TTY process inside it, detect common Compose isolation failures, and stop only proven task resources while preserving mutable data.
