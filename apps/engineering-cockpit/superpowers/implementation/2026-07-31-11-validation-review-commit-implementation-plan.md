# 11 — Validation, Quality Gates, Change Review, and Explicit Commit Preparation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `techletes-superpowers:subagent-driven-development` or `techletes-superpowers:executing-plans`. Subsystems 03–10 are prerequisites. Before implementation, amend subsystem 05 with the Git-common-directory mount requirement from this spec.

**Goal:** Execute reviewed repository validation profiles in the task devcontainer, expose a safe/fresh Git review, and create a verified local commit only after explicit confirmation.

**Architecture:** Parse strict validation config, run bounded trusted processes through the devcontainer adapter, tie every result to Git/config fingerprints, expose changed-file/diff APIs, stage exact selected paths, and commit inside the devcontainer with hooks/signing intact.

**Tech stack:** SQLModel models, subsystem 04 Git adapter, subsystem 05 devcontainer exec, subsystem 06 process supervision, FastAPI, inherited generated client, Pytest.

## Global constraints

- No active turn or pending request during validation/commit.
- Commands come only from committed reviewed config.
- No implicit shell, `git add .`, `--no-verify`, signing disablement, or secret environment logging.
- Review/validation freshness is checked immediately before commit.
- Git common directory must be mounted and verified inside the container.

---

### Task 1: Amend devcontainer runtime for linked-worktree Git metadata

**Files:**
- Modify: `apps/engineering-cockpit/backend/cockpit/devcontainers/adapter.py`
- Modify: `apps/engineering-cockpit/backend/cockpit/devcontainers/models.py`
- Modify: `apps/engineering-cockpit/backend/tests/cockpit/devcontainers/test_adapter_up.py`
- Modify: `apps/engineering-cockpit/backend/tests/manual/devcontainer_two_worktrees.md`

**Interfaces:**

```python
@dataclass(frozen=True)
class GitMetadataMount:
    source: Path
    target: PurePosixPath

async def build_git_common_dir_mount(
    *,
    repository: CockpitRepositorySnapshot,
    worktree: GitWorktreeEntry,
    cli_version: DevcontainerCliVersion,
) -> GitMetadataMount: ...
```

- [ ] Confirm the pinned Dev Container CLI's supported additional-mount option from `devcontainer up --help` and lock it into the compatibility test.
- [ ] Resolve the canonical Git common directory through subsystem 04 and mount it at the exact absolute path referenced by the worktree's `.git` file.
- [ ] Reject source/target mismatch, non-directory common dir, untrusted repository, symlink escape, and unsupported CLI version.
- [ ] Pass the mount on both initial and ordinary `up`; persist its source/target hash, not user-sensitive path if policy hides it.
- [ ] After readiness, run `git rev-parse --git-common-dir` and NUL-safe status inside the container and require success.
- [ ] Extend the real two-worktree smoke test to run Git in both containers.
- [ ] Commit: `feat: mount worktree git metadata in devcontainers`.

### Task 2: Define strict validation configuration

**Files:**
- Create: `apps/engineering-cockpit/backend/cockpit/validation/configuration.py`
- Modify: `apps/engineering-cockpit/backend/cockpit/repositories/configuration.py`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/validation/test_configuration.py`

**Interfaces:**

```python
class ValidationStepConfig(BaseModel):
    id: str
    display_name: str
    argv: tuple[str, ...] | None
    script: PurePosixPath | None
    cwd: PurePosixPath
    required: bool
    mutates_workspace: bool
    timeout_seconds: int
    retries: int
    env_allowlist: tuple[str, ...]
    artifacts: tuple[PurePosixPath, ...]

class ValidationProfileConfig(BaseModel):
    steps: tuple[ValidationStepConfig, ...]
```

- [ ] Require exactly one of `argv` or repository script.
- [ ] Reject empty executable, absolute/traversing cwd/artifacts, browser variables, unbounded timeout/retries, duplicate step IDs, and shell strings unless an explicit trusted shell-step schema is implemented.
- [ ] Snapshot/hash the resolved profile.
- [ ] Add onboarding-generated defaults by inspecting actual current template scripts; do not hardcode commands that do not exist.
- [ ] Test template quick/full/delivery profiles and invalid configurations.
- [ ] Commit: `feat: configure cockpit validation profiles`.

### Task 3: Add validation persistence models

**Files:**
- Modify: `apps/engineering-cockpit/backend/models.py`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/validation/test_models.py`
- Add migration if fields are not already present.

**Models:**

```text
CockpitValidationBatch
CockpitValidationRun
CockpitValidationArtifact
```

- [ ] Store profile/config hashes, start/end head/status hashes, aggregate result, step order, attempt, exit/cancel/timeout, sanitized tails, diagnostic log ID, changed paths, and artifact metadata.
- [ ] Add indexes for task/latest batch and task/head/profile lookup.
- [ ] Public schemas expose safe result data and freshness.
- [ ] Test relationships, defaults, constraints, and migration upgrade/downgrade.
- [ ] Commit: `feat: persist cockpit validation results`.

### Task 4: Implement validation command resolution

**Files:**
- Create: `apps/engineering-cockpit/backend/cockpit/validation/commands.py`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/validation/test_commands.py`

**Interfaces:**

```python
@dataclass(frozen=True)
class ResolvedValidationCommand:
    step_id: str
    argv: tuple[str, ...]
    remote_cwd: PurePosixPath
    env_names: tuple[str, ...]
    timeout_seconds: int
```

- [ ] Map relative cwd/script to the verified remote workspace and enforce containment.
- [ ] Resolve env **names** from inherited container environment without storing their values.
- [ ] For reviewed script steps, execute the script path as argv; do not splice its content into a shell.
- [ ] Test missing executable/script, non-executable script, path traversal, environment name rejection, and spaces.
- [ ] Commit: `feat: resolve trusted validation commands`.

### Task 5: Implement validation execution and cancellation

**Files:**
- Create: `apps/engineering-cockpit/backend/cockpit/validation/service.py`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/validation/test_service.py`

**Interfaces:**

```python
class ValidationService:
    async def run(
        self,
        *,
        task_id: UUID,
        profile_name: str,
        expected_task_version: int,
    ) -> CockpitValidationBatchPublic: ...
    async def cancel(self, *, task_id: UUID, batch_id: UUID) -> None: ...
```

- [ ] Acquire task lock and validation semaphore; verify no active turn/request and healthy runtime.
- [ ] Capture initial head/status hash, persist batch and `VALIDATING` transition.
- [ ] Execute sequentially through `DevcontainerExecLauncher`, persist each attempt/result, and stream bounded events.
- [ ] Stop on required failure; optional steps may continue according to config.
- [ ] Implement manual cancellation with graceful/force process stop and refresh Git status.
- [ ] Return task to `READY_FOR_REVIEW` with latest validation status field/event.
- [ ] Test success, required/optional failure, timeout, retry, cancellation, backend connection loss, and step log bounds.
- [ ] Commit: `feat: run task validation profiles`.

### Task 6: Detect workspace mutation and staleness

**Files:**
- Create: `apps/engineering-cockpit/backend/cockpit/validation/freshness.py`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/validation/test_freshness.py`

**Interfaces:**

```python
@dataclass(frozen=True)
class ValidationFreshness:
    current: bool
    reasons: tuple[str, ...]

async def assess_validation_freshness(... ) -> ValidationFreshness: ...
```

- [ ] Capture status before/after every step.
- [ ] Fail an unmarked mutating step as `VALIDATION_UNEXPECTED_MUTATION` while preserving files.
- [ ] For marked mutation, persist changed paths and require a later configured non-mutating check when policy says so.
- [ ] Mark batch stale after head/status/profile-config change.
- [ ] Test external edit during run, expected formatter change, commit after run, config change, and same-content timestamp-only change.
- [ ] Commit: `feat: track validation mutation and freshness`.

### Task 7: Collect bounded artifacts

**Files:**
- Create: `apps/engineering-cockpit/backend/cockpit/validation/artifacts.py`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/validation/test_artifacts.py`

- [ ] Resolve configured artifacts under worktree, reject symlinks/escapes, and record path/type/size/hash.
- [ ] Enforce per-file/total size limits; store large artifacts on local disk with retention ID rather than database bytes.
- [ ] Support known XML/JSON metadata summaries only after safe parsing; do not render arbitrary HTML reports directly.
- [ ] Test missing optional/required artifact, oversized, symlink, binary, malformed XML/JSON, and cleanup retention.
- [ ] Commit: `feat: collect validation artifacts safely`.

### Task 8: Build change review service and endpoints

**Files:**
- Create: `apps/engineering-cockpit/backend/cockpit/review/service.py`
- Create: `apps/engineering-cockpit/backend/api/routes/cockpit_review.py`
- Modify: `apps/engineering-cockpit/backend/api/main.py`
- Create: `apps/engineering-cockpit/backend/tests/api/routes/test_cockpit_review.py`

**Endpoints:**

```text
GET /api/v1/cockpit/tasks/{id}/changes
GET /api/v1/cockpit/tasks/{id}/changes/{path}
```

- [ ] Return status, head/base/merge-base, stats, path markers, review snapshot hash, and latest validation freshness.
- [ ] Validate requested file path against the effective changed set.
- [ ] Bound unified diff; return binary/oversized marker and a controlled download/reference path where allowed.
- [ ] Escape content at serialization/render layer; do not interpret ANSI/HTML.
- [ ] Detect secret patterns and emit warnings/blockers without rewriting the source diff.
- [ ] Test traversal, unauthorized task, stale snapshot, binary, rename/delete, conflict, generated file, and sensitive pattern.
- [ ] Commit: `feat: expose safe cockpit change review`.

### Task 9: Implement commit-message validation and proposal storage

**Files:**
- Create: `apps/engineering-cockpit/backend/cockpit/review/commit_message.py`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/review/test_commit_message.py`

**Interfaces:**

```python
@dataclass(frozen=True)
class CommitMessagePolicy: ...

def validate_commit_message(message: str, policy: CommitMessagePolicy) -> str: ...
```

- [ ] Validate subject/body length, control characters, blank subject, configured conventional format, and explicit issue-closing keyword policy.
- [ ] Store agent proposal separately from user-approved final message.
- [ ] Test Unicode, multiline, malicious terminal escapes, auto-close keywords, and whitespace normalization.
- [ ] Commit: `feat: validate cockpit commit messages`.

### Task 10: Implement exact staging and local commit

**Files:**
- Create: `apps/engineering-cockpit/backend/cockpit/review/commit_service.py`
- Create: `apps/engineering-cockpit/backend/api/routes/cockpit_commit.py`
- Modify: `apps/engineering-cockpit/backend/api/main.py`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/review/test_commit_service.py`
- Create: `apps/engineering-cockpit/backend/tests/api/routes/test_cockpit_commit.py`

**Endpoint:**

```text
POST /api/v1/cockpit/tasks/{id}/commit
```

Request includes expected task version, expected review snapshot hash, exact selected paths, final message, and optional authorized validation override.

- [ ] Require owner/permission, no active operation/request, task branch/head match, no conflicts, and current validation/override.
- [ ] Validate selected paths exactly against current status; preserve NUL-safe internal representation.
- [ ] Run `git add -- <paths...>` and `git commit -m <message>` through trusted devcontainer exec at verified remote workspace.
- [ ] Do not use shell, `git add .`, `--no-verify`, or signing overrides.
- [ ] Capture hook/signing stderr safely and leave staged state intact on failure.
- [ ] Verify new commit parent/head and committed paths, persist commit metadata/event, refresh status, and mark validation freshness appropriately.
- [ ] Test stale review, subset/all, conflict, hook failure, signing failure, head race, no changes, two-tab idempotency, and success.
- [ ] Commit: `feat: create explicit cockpit commits`.

### Task 11: Add validation/review/commit UI client contract readiness

**Files:**
- Regenerate: `apps/engineering-cockpit/frontend/src/client/`
- Create: `apps/engineering-cockpit/frontend/src/services/CockpitValidationService.ts`
- Create: `apps/engineering-cockpit/frontend/src/services/CockpitReviewService.ts`
- Create: `apps/engineering-cockpit/frontend/src/services/CockpitCommitService.ts`
- Create: corresponding service tests if the template supports them.

- [ ] Regenerate OpenAPI client after backend routes.
- [ ] Wrap generated client in the service layer; do not call it directly from components.
- [ ] Preserve binary/oversized/sensitive warning types.
- [ ] No full UI yet; subsystem 13 consumes these services.
- [ ] Run typecheck and commit: `feat: add validation review service clients`.

### Task 12: Run real template validation/commit acceptance

**Files:**
- Create: `apps/engineering-cockpit/backend/tests/manual/validation_commit.md`

- [ ] In a disposable template-derived worktree/devcontainer, make a harmless backend and frontend change.
- [ ] Run quick/full/delivery profiles.
- [ ] Confirm Git works inside the linked-worktree container through common-dir mount.
- [ ] Trigger a hook failure and verify no bypass.
- [ ] Commit selected paths successfully and verify head/parent/status.
- [ ] Record signing behavior for the developer's WSL/devcontainer configuration; if headless signing fails, document the supported remediation rather than disabling it.
- [ ] Commit: `test: verify validation review and commit flow`.

### Task 13: Complete subsystem verification

```bash
cd apps/engineering-cockpit
uv run pytest backend/tests/cockpit/validation backend/tests/cockpit/review backend/tests/api/routes/test_cockpit_review.py backend/tests/api/routes/test_cockpit_commit.py -q
uv run mypy backend/cockpit/validation backend/cockpit/review
uv run ruff check backend/cockpit/validation backend/cockpit/review
cd frontend && bun run generate-client && bun run typecheck
```

- [ ] Commit: `test: verify cockpit quality gates`.

## Exit criteria

Subsystem 11 is complete when validation is command-allowlisted and tied to exact Git/config state, review paths/diffs are safe and fresh, linked-worktree Git works inside the devcontainer, and the user can create a hook-respecting verified local commit from exact selected changes without any automatic push.
