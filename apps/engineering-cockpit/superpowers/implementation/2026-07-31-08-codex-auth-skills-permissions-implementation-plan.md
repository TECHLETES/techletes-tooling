# 08 — Codex Authentication, `CODEX_HOME`, Techletes Skills, Instructions, and Permissions Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `techletes-superpowers:subagent-driven-development` or `techletes-superpowers:executing-plans`. Subsystems 02, 05, and 07 are prerequisites.

**Goal:** Make authenticated app-server startup reproducible in trusted task devcontainers, verify Techletes skill availability, build deterministic task context, and apply version-tested execution profiles.

**Architecture:** Reuse the template's host-mounted `CODEX_HOME`, validate it inside each target container, serialize global home mutations, configure extra skill roots on every app-server generation, and map product permission profiles to the pinned app-server schema.

**Tech stack:** Codex app-server account/skills methods from the pinned schema, Dev Container CLI adapter, Pydantic settings, SQLModel metadata, Pytest, real concurrent acceptance script.

## Global constraints

- Never infer or copy credential filenames.
- Never log account tokens, config contents, or raw authentication responses.
- Do not start authenticated tasks for untrusted repositories.
- Skill root paths are container-visible paths, not assumed sibling WSL paths.
- Delivery credentials/actions remain outside the Codex turn.
- A profile can only reduce, never exceed, global/repository policy.

---

### Task 1: Add Codex-home and trust configuration models

**Files:**
- Create: `apps/engineering-cockpit/backend/cockpit/codex/home.py`
- Modify: `apps/engineering-cockpit/backend/cockpit/repositories/configuration.py`
- Modify: `apps/engineering-cockpit/backend/core/config.py`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/codex/test_home_config.py`

**Interfaces:**

```python
class CodexHomeStrategy(str, Enum):
    SHARED_HOST_HOME = "shared_host_home"

class RepositoryTrust(str, Enum):
    TRUSTED = "trusted"
    UNTRUSTED = "untrusted"

@dataclass(frozen=True)
class CodexHomeConfig:
    strategy: CodexHomeStrategy
    container_path: PurePosixPath
    repository_trust: RepositoryTrust
```

- [ ] Extend strict `.techletes/cockpit.yaml` parsing with trust, Codex-home, skill-root, required-skill, and execution-profile settings.
- [ ] Resolve `${CODEX_HOME}` only inside the target container after a readiness command returns its value.
- [ ] Reject relative paths, NUL/control characters, symlink escape, and untrusted repository use.
- [ ] Do not accept a user-supplied credential file path.
- [ ] Test template defaults and a non-`vscode` remote user.
- [ ] Commit: `feat: configure codex home and repository trust`.

### Task 2: Implement target-container home diagnostics

**Files:**
- Create: `apps/engineering-cockpit/backend/cockpit/codex/home_diagnostics.py`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/codex/test_home_diagnostics.py`

**Interfaces:**

```python
@dataclass(frozen=True)
class CodexHomeDiagnostics:
    path: str
    path_hash: str
    exists: bool
    readable: bool
    writable: bool
    owner_uid: int | None
    remote_uid: int
    trusted: bool
```

- [ ] Execute a fixed Python or POSIX diagnostic command through `DevcontainerExecLauncher`; do not interpolate the path into a shell string.
- [ ] Verify environment, real path, stat ownership/mode, read/write behavior, and containment under the remote user's intended home.
- [ ] Hash the public path value before database persistence if global policy hides local usernames.
- [ ] Test missing variable, nonexistent directory, read-only path, wrong owner but writable group, symlink, and root remote user.
- [ ] Add active repository diagnostic output with no directory listing/content.
- [ ] Commit: `feat: diagnose target codex home`.

### Task 3: Add the global Codex-home mutation lock

**Files:**
- Create: `apps/engineering-cockpit/backend/cockpit/codex/home_lock.py`
- Modify: `apps/engineering-cockpit/backend/cockpit/runtime/context.py`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/codex/test_home_lock.py`

**Interfaces:**

```python
class CodexHomeMutationLock:
    @asynccontextmanager
    async def hold(self, operation: str) -> AsyncIterator[None]: ...
```

- [ ] Serialize administrative account/config/skill-install operations globally.
- [ ] Do not acquire this lock for normal thread/turn operations.
- [ ] Track current operation/start time for diagnostics but never arguments/secrets.
- [ ] Test cancellation, timeout, nested use rejection, and concurrent readers continuing during a mutation only when explicitly safe.
- [ ] Commit: `feat: serialize codex home mutations`.

### Task 4: Implement account-read diagnostics

**Files:**
- Create: `apps/engineering-cockpit/backend/cockpit/codex/account.py`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/codex/test_account.py`

**Interfaces:**

```python
@dataclass(frozen=True)
class CodexAccountStatus:
    authenticated: bool
    provider: str | None
    account_type: str | None
    login_required: bool

class CodexAccountService:
    async def read(self, adapter: CodexAppServerAdapter) -> CodexAccountStatus: ...
```

- [ ] Derive account-read method/result from the pinned generated schema.
- [ ] Whitelist public fields explicitly; discard all unrecognized fields.
- [ ] Test authenticated, unauthenticated, login pending, method unsupported, schema violation, and server error.
- [ ] Map unauthenticated to `CODEX_AUTH_REQUIRED` with a safe remediation command.
- [ ] Do not implement task-triggered login/logout.
- [ ] Commit: `feat: verify codex account status`.

### Task 5: Resolve and configure skill roots

**Files:**
- Create: `apps/engineering-cockpit/backend/cockpit/codex/skills.py`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/codex/test_skills.py`

**Interfaces:**

```python
@dataclass(frozen=True)
class ResolvedSkill:
    name: str
    source_path_hash: str
    description: str | None
    metadata_hash: str

class CodexSkillService:
    async def configure_and_list(
        self,
        adapter: CodexAppServerAdapter,
        roots: Sequence[PurePosixPath],
        required_names: Sequence[str],
    ) -> tuple[ResolvedSkill, ...]: ...
```

- [ ] Derive exact extra-root and skill-list methods from the pinned schema.
- [ ] Set extra roots after every app-server initialization; do not assume persistence.
- [ ] Validate roots inside the container before calling app-server.
- [ ] Normalize names so `techletes-superpowers:using-superpowers` cannot be confused with another plugin's `using-superpowers`.
- [ ] Test present, missing, duplicate/shadowed, unreadable, invalid metadata, restart/reapply, and unsupported methods.
- [ ] Persist a manifest fingerprint and resolved required skill identities, not full skill contents.
- [ ] Commit: `feat: configure techletes codex skills`.

### Task 6: Add an administrative skill-sync command

**Files:**
- Create: `apps/engineering-cockpit/scripts/sync-techletes-codex-skills.sh`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/codex/test_skill_sync_script.py`
- Modify: `apps/engineering-cockpit/README.md`

- [ ] Inspect the actual Techletes plugin installation convention before writing the command; use its supported installer/link process rather than inventing a directory layout.
- [ ] Run under the global home mutation lock when invoked through the API/CLI.
- [ ] Copy/link only from a verified `TECHLETES/techletes-tooling` checkout/ref and record source commit.
- [ ] Make the operation atomic: stage to a temporary directory, validate `skills/list` in a disposable app-server, then swap.
- [ ] Never print file contents or credentials.
- [ ] Test missing source, dirty source policy, invalid skill, atomic rollback, and successful manifest update.
- [ ] Commit: `build: synchronize techletes codex skills`.

### Task 7: Implement deterministic task-context assembly

**Files:**
- Create: `apps/engineering-cockpit/backend/cockpit/codex/context.py`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/codex/test_context.py`

**Interfaces:**

```python
@dataclass(frozen=True)
class TaskContext:
    input_items: tuple[CodexInputItem, ...]
    fingerprint: str
    source_references: tuple[str, ...]
    byte_size: int

class TaskContextBuilder:
    def build(... ) -> TaskContext: ...
```

- [ ] Compose user/issue text, task metadata, exact child spec/plan paths, required skill names, and delivery boundary in a fixed order.
- [ ] Refer to repository `AGENTS.md`; do not paste it by default.
- [ ] Prefer a schema-supported skill input/capability-root item; use a text instruction fallback only when compatibility manifest says so.
- [ ] Normalize line endings/JSON and calculate a deterministic hash.
- [ ] Enforce item and total byte limits; return `CODEX_INSTRUCTION_CONTEXT_TOO_LARGE` with per-source sizes.
- [ ] Test manual task, issue task, preset, Unicode, repeated build determinism, missing plan path, and attempted hidden prompt injection in repository metadata.
- [ ] Commit: `feat: assemble codex task context`.

### Task 8: Define product permission profiles

**Files:**
- Create: `apps/engineering-cockpit/backend/cockpit/codex/permissions.py`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/codex/test_permissions.py`

**Interfaces:**

```python
class ExecutionProfileName(str, Enum):
    ANALYSIS = "analysis"
    DEVELOPMENT = "development"
    DEPENDENCY_UPDATE = "dependency_update"
    DIAGNOSTIC_REPAIR = "diagnostic_repair"

@dataclass(frozen=True)
class ResolvedExecutionProfile:
    name: ExecutionProfileName
    sandbox_params: dict[str, object]
    approval_policy_params: dict[str, object]
    network_policy: str
    fingerprint: str
```

- [ ] Build mappings from the pinned generated schema, not remembered field names.
- [ ] Define global maximum profile and repository allowed profiles.
- [ ] Reject escalation and `danger-full-access`/unrestricted host access.
- [ ] Keep push/PR/merge/deploy absent from all profiles.
- [ ] Test each profile's exact serialized thread/turn params, unsupported network expression, profile escalation, and schema drift.
- [ ] Commit: `feat: define codex execution profiles`.

### Task 9: Verify approval emission for each profile

**Files:**
- Create: `apps/engineering-cockpit/backend/tests/cockpit/codex/test_profile_approval_protocol.py`
- Create: `apps/engineering-cockpit/backend/tests/manual/codex_profile_matrix.md`

- [ ] Extend the fake app-server to assert expected approval-policy params and emit representative command/file-change requests.
- [ ] For the pinned real Codex version, run disposable tasks that attempt:
  - read-only inspection;
  - workspace file edit;
  - command outside ordinary safe set;
  - network/package access where applicable;
  - write outside workspace (must fail/block).
- [ ] Record whether the corresponding approval request appears and whether rejection is honored.
- [ ] Mark a profile unsupported if the required request stalls or bypasses policy; do not weaken it automatically.
- [ ] Commit: `test: verify codex permission profiles`.

### Task 10: Integrate auth, skills, context, and profile into session startup

**Files:**
- Modify: `apps/engineering-cockpit/backend/cockpit/codex/service.py`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/codex/test_session_policy.py`

- [ ] After initialize, verify home/account, set/list skills, resolve execution profile, and build task context before `thread/start`/`turn/start`.
- [ ] Persist home strategy hash, account status, skill manifest, context fingerprint, and profile fingerprint.
- [ ] Fail before implementation work if any required check fails.
- [ ] Ensure restart reapplies skill roots and revalidates account/profile compatibility before thread resume.
- [ ] Test trusted success, untrusted repository, auth missing, skill missing, profile unsupported, and context too large.
- [ ] Commit: `feat: apply codex session policy`.

### Task 11: Run shared-home concurrency acceptance

**Files:**
- Create: `apps/engineering-cockpit/scripts/check-codex-home-concurrency.sh`
- Create: `apps/engineering-cockpit/backend/tests/manual/codex_home_concurrency.md`

- [ ] Start two disposable template-derived task devcontainers sharing the configured host Codex home.
- [ ] Initialize two app-server processes concurrently.
- [ ] Start distinct threads, run harmless turns, close both, start fresh processes, and resume both threads.
- [ ] Confirm no config/session corruption, cross-thread event leakage, or authentication loss.
- [ ] Concurrently attempt an administrative mutation and prove the cockpit lock serializes it.
- [ ] Record pinned versions, home strategy, outcomes, and any file-lock diagnostics without recording file contents.
- [ ] Treat failure as a release blocker; do not add secret-copy fallback.
- [ ] Commit: `test: verify shared codex home concurrency`.

### Task 12: Complete subsystem verification

```bash
cd apps/engineering-cockpit
uv run pytest backend/tests/cockpit/codex/test_home_config.py backend/tests/cockpit/codex/test_home_diagnostics.py backend/tests/cockpit/codex/test_home_lock.py backend/tests/cockpit/codex/test_account.py backend/tests/cockpit/codex/test_skills.py backend/tests/cockpit/codex/test_context.py backend/tests/cockpit/codex/test_permissions.py backend/tests/cockpit/codex/test_session_policy.py -q
uv run mypy backend/cockpit/codex
uv run ruff check backend/cockpit/codex
```

- [ ] Attach the two manual acceptance records to the internal release evidence.
- [ ] Commit: `test: verify codex auth skills and permissions`.

## Exit criteria

Subsystem 08 is complete when trusted target containers can use the shared authenticated Codex home concurrently, required Techletes skills are reconfigured and verified after every app-server start, task context references exact plans deterministically, and every allowed execution profile is schema-valid, non-escalating, and proven to surface or deny the expected operations.
