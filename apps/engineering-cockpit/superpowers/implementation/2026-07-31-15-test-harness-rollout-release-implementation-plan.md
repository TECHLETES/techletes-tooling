# 15 — Deterministic Test Harness, Acceptance Matrix, Rollout, and Release Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `techletes-superpowers:subagent-driven-development` or `techletes-superpowers:executing-plans`. This is the final integration subsystem and depends on stable contracts from subsystems 01–14.

**Goal:** Build one deterministic external-tool scenario harness, complete the cross-subsystem integration/chaos/E2E matrix, prove the real local workflow, and package staged rollout, release evidence, backup, and rollback.

**Architecture:** External fakes remain real child executables/adapters driven by strict versioned scenarios. Backend integration uses real PostgreSQL/Redis. Playwright drives the full application. Authenticated real acceptance runs locally against a disposable template-derived GitHub repository.

**Tech stack:** Pytest, Hypothesis where useful for parser/path properties, Playwright, Vitest, PostgreSQL, Redis, fake external processes, GitHub Actions, shell scripts with strict mode, Markdown/JSON release evidence.

## Global constraints

- CI never receives real OpenAI/GitHub/developer credentials.
- Fakes fail on unexpected argv/message and cannot execute arbitrary scenario code.
- Every mutation is tested around intent/action/inspection/result boundaries.
- Real acceptance uses disposable non-production resources.
- Release gates cannot be waived by a frontend-only feature flag.
- Rollback preserves worktrees, containers, commits, branches, and volumes unless separately cleaned later.

---

### Task 1: Define the unified scenario schema

**Files:**
- Create: `apps/engineering-cockpit/backend/tests/cockpit/fakes/scenario_models.py`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/fakes/scenario_loader.py`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/fakes/scenario.schema.json`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/fakes/test_scenario_loader.py`

**Interfaces:**

```python
class Scenario(BaseModel):
    version: Literal[1]
    name: str
    variables: dict[str, ScenarioVariable]
    initial: InitialExternalState
    steps: tuple[ScenarioStep, ...]
    faults: tuple[FaultRule, ...]
    assertions: tuple[ScenarioAssertion, ...]

class ScenarioRuntime:
    def next_invocation(self, invocation: ToolInvocation) -> ToolResult: ...
    def journal(self) -> tuple[InvocationRecord, ...]: ...
```

- [ ] Use strict Pydantic models with unknown fields forbidden.
- [ ] Support only declared literal/path/UUID/SHA/test-token variables; no arbitrary expression or environment substitution.
- [ ] Model ordered steps plus explicit concurrency groups.
- [ ] Model deterministic result, delay, timeout, malformed output, process exit, connection close, duplicate, and ambiguous-success faults.
- [ ] Redact declared secret test tokens from validation failures/journal display.
- [ ] Validate fixture file references remain under the scenario root.
- [ ] Test invalid version, missing variable, traversal, unexpected field, concurrency-group mismatch, unknown fault, and secret redaction.
- [ ] Commit: `test: define cockpit external scenario format`.

### Task 2: Add the append-only invocation journal and assertion engine

**Files:**
- Create: `apps/engineering-cockpit/backend/tests/cockpit/fakes/journal.py`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/fakes/assertions.py`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/fakes/test_journal_assertions.py`

**Interfaces:**

```python
@dataclass(frozen=True)
class InvocationRecord:
    sequence: int
    tool: str
    argv: tuple[str, ...]
    cwd: str | None
    env_names: tuple[str, ...]
    stdin_hashes: tuple[str, ...]
    result_code: str
    started_at: datetime
    completed_at: datetime

class ScenarioAssertions:
    def verify(self, scenario: Scenario, journal: Sequence[InvocationRecord]) -> None: ...
```

- [ ] Never record environment values or raw secret-bearing stdin.
- [ ] Support exact count/order/concurrency, must-not-call, expected task/worktree/container/thread/turn/SHA IDs, and unrelated-resource-survival assertions.
- [ ] Produce concise deterministic diff when actual invocation does not match scenario.
- [ ] Test concurrent ordering, duplicate calls, forbidden merge/deploy command, and ambiguous-result journal.
- [ ] Commit: `test: record fake tool invocation evidence`.

### Task 3: Migrate all external fakes to the unified harness

**Files:**
- Modify: fake Git/devcontainer/Docker/app-server/GitHub/editor helpers created by subsystems 04–13
- Create: `apps/engineering-cockpit/backend/tests/cockpit/fakes/runner.py`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/fakes/test_all_fakes.py`

- [ ] Provide one scenario endpoint/state directory shared by child processes without unsafe global mutable state.
- [ ] Make fake `devcontainer`, `docker`, `codex app-server`, `gh`, editor command, and any fake Git wrapper consume exact scenario steps and append journal records.
- [ ] Keep real temporary Git repositories for Git behavior tests; use a fake wrapper only for process-level failures that real Git cannot reliably induce.
- [ ] App-server remains a real stdin/stdout child and validates generated schema.
- [ ] Fakes exit non-zero on unexpected commands/messages or incomplete scenario at test end.
- [ ] Test two fake processes consuming declared concurrency steps safely.
- [ ] Commit: `test: unify cockpit external tool fakes`.

### Task 4: Add test failpoint infrastructure

**Files:**
- Create: `apps/engineering-cockpit/backend/cockpit/testing/failpoints.py`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/testing/test_failpoints.py`
- Modify: orchestration services to accept an injected `FailpointController` at defined boundaries

**Interfaces:**

```python
class FailpointName(str, Enum):
    BEFORE_INTENT = "before_intent"
    AFTER_INTENT = "after_intent"
    DURING_EXTERNAL_ACTION = "during_external_action"
    AFTER_EXTERNAL_ACTION = "after_external_action"
    AFTER_INSPECTION = "after_inspection"
    AFTER_RESULT_PERSIST = "after_result_persist"
    AFTER_EVENT_PUBLISH = "after_event_publish"

class FailpointController(Protocol):
    async def hit(self, operation: str, point: FailpointName) -> None: ...
```

- [ ] Production implementation is a no-op and cannot be configured through public settings/API.
- [ ] Test implementation can raise, cancel, delay, or hard-exit the test subprocess at exact named points.
- [ ] Add points to worktree, devcontainer, app-server session, request response, validation, commit, push, PR, recovery, and cleanup operations.
- [ ] Test no failpoint changes behavior when disabled and hard-exit leaves durable evidence expected by recovery.
- [ ] Commit: `test: inject orchestration failure boundaries`.

### Task 5: Create reusable PostgreSQL/Redis integration environment

**Files:**
- Create: `apps/engineering-cockpit/backend/tests/integration/conftest.py`
- Create: `apps/engineering-cockpit/backend/tests/integration/support_services.py`
- Create: `apps/engineering-cockpit/backend/tests/integration/test_support_services.py`

- [ ] Reuse the inherited Compose support services or create isolated per-test database/schema and Redis namespace.
- [ ] Apply Alembic migrations from zero for a session and verify one head.
- [ ] Reset database/Redis deterministically between tests without using SQLite.
- [ ] Run FastAPI lifespan with host lock and test paths redirected to disposable roots.
- [ ] Expose helpers for authenticated users/RBAC, event WebSocket, scenario runtime, and backend restart.
- [ ] Test service unavailable, migration failure, reset leakage, parallel test worker policy, and cleanup.
- [ ] Default integration suite to serial if shared process/port resources cannot be isolated safely.
- [ ] Commit: `test: add real cockpit integration services`.

### Task 6: Implement golden backend scenario A — one manual task

**Files:**
- Create: `apps/engineering-cockpit/backend/tests/integration/scenarios/golden_manual_task.yaml`
- Create: `apps/engineering-cockpit/backend/tests/integration/test_golden_manual_task.py`

- [ ] Drive repository register/trust, task create/start, worktree, devcontainer, initialize/thread/turn, file-change events, clarification, answer, completion, validation, review, exact commit, and graceful stop through public services/API.
- [ ] Assert every durable task state/event/request/validation/commit identity and invocation journal entry.
- [ ] Assert browser absence has no bearing on process lifecycle.
- [ ] Assert no push/PR/merge/deploy command.
- [ ] Commit: `test: cover manual task golden path`.

### Task 7: Implement golden backend scenario B — two concurrent tasks

**Files:**
- Create: `apps/engineering-cockpit/backend/tests/integration/scenarios/golden_concurrent_tasks.yaml`
- Create: `apps/engineering-cockpit/backend/tests/integration/test_golden_concurrent_tasks.py`

- [ ] Start two tasks in one repository concurrently.
- [ ] Assert distinct branch, worktree, container, mutable volumes, process/session/thread/turn IDs and event/request ownership.
- [ ] Edit non-overlapping then overlapping paths and verify overlap levels/base warning.
- [ ] Complete/commit one task while second continues.
- [ ] Attempt cross-task response/process/cleanup IDs and assert authorization/identity rejection.
- [ ] Assert global start semaphore and per-task locks permit only intended concurrency.
- [ ] Commit: `test: cover concurrent task isolation`.

### Task 8: Implement golden backend scenario C — GitHub delivery

**Files:**
- Create: `apps/engineering-cockpit/backend/tests/integration/scenarios/golden_github_delivery.yaml`
- Create: `apps/engineering-cockpit/backend/tests/integration/test_golden_github_delivery.py`

- [ ] Preview/snapshot issue, create task, validate/commit, push, create draft PR, monitor pending/failure/success checks and review changes.
- [ ] Fetch bounded failure context and add it only through explicit follow-up.
- [ ] Assert expected local/remote/head SHAs and idempotent ambiguous PR creation handling.
- [ ] Assert no merge/auto-merge/deploy command in invocation journal.
- [ ] Commit: `test: cover github delivery golden path`.

### Task 9: Implement golden backend scenario D — browser reconnect and backend recovery

**Files:**
- Create: `apps/engineering-cockpit/backend/tests/integration/scenarios/golden_recovery.yaml`
- Create: `apps/engineering-cockpit/backend/tests/integration/test_golden_recovery.py`

- [ ] Disconnect/reconnect event client while process continues and verify exact cursor replay.
- [ ] Hard-stop backend after intent/action boundaries while fake app-server remains tagged.
- [ ] Start a new backend instance, terminate exact orphan, ordinary-up container without rebuild, initialize/resume/read thread, and reconcile terminal-history case.
- [ ] Run a second scenario with no terminal evidence and require `RECOVERY_REQUIRED`/lost-turn acknowledgement.
- [ ] Include unresolved approval and Redis unavailable/replay cases.
- [ ] Assert no prompt/approval automatic replay.
- [ ] Commit: `test: cover cockpit recovery golden path`.

### Task 10: Implement golden backend scenario E — guarded cleanup

**Files:**
- Create: `apps/engineering-cockpit/backend/tests/integration/scenarios/golden_cleanup.yaml`
- Create: `apps/engineering-cockpit/backend/tests/integration/test_golden_cleanup.py`

- [ ] Create task-owned and unrelated worktree/container/network/volume/branch resources.
- [ ] Assess cleanup, stop task/runtime, remove worktree and exact runtime, preserve volume/history by default.
- [ ] Separately confirm branch and volume deletion in disposable scenario.
- [ ] Crash after every cleanup stage and continue idempotently.
- [ ] Assert unrelated resources and credentials survive.
- [ ] Commit: `test: cover guarded cleanup golden path`.

### Task 11: Generate the full contract/scenario matrix

**Files:**
- Create: `apps/engineering-cockpit/backend/tests/matrix/cases.py`
- Create: `apps/engineering-cockpit/backend/tests/matrix/test_matrix.py`
- Create: `apps/engineering-cockpit/backend/tests/matrix/README.md`

- [ ] Encode every scenario dimension listed in the specification with stable case IDs and owner subsystem.
- [ ] Parameterize parsers/adapters/services where runtime remains reasonable; mark real/manual-only cases explicitly.
- [ ] Fail a meta-test when a required matrix case lacks an automated or manual evidence implementation.
- [ ] Produce a JSON automated summary by case ID, duration, result, and diagnostic reference.
- [ ] Split CI shards by subsystem/cost without changing semantics.
- [ ] Commit: `test: enforce cockpit acceptance matrix`.

### Task 12: Add recovery and cleanup crash matrices

**Files:**
- Create: `apps/engineering-cockpit/backend/tests/chaos/test_operation_failpoints.py`
- Create: `apps/engineering-cockpit/backend/tests/chaos/test_recovery_failpoints.py`
- Create: `apps/engineering-cockpit/backend/tests/chaos/test_cleanup_failpoints.py`

- [ ] Parameterize every mutating operation across all failpoint boundaries.
- [ ] After failure/hard exit, restart application and assert exact plan/outcome/idempotency.
- [ ] Assert no duplicate thread/turn/request/event/PR/commit, no broad resource deletion, and no inferred success.
- [ ] Include event publication failure after committed result.
- [ ] Keep chaos tests serial and bound total runtime.
- [ ] Commit: `test: exercise cockpit operation crash boundaries`.

### Task 13: Build frontend E2E scenario bridge

**Files:**
- Create: `apps/engineering-cockpit/frontend/e2e/helpers/scenario.ts`
- Create: `apps/engineering-cockpit/backend/api/routes/testing_scenarios.py` under test-only application assembly
- Create: `apps/engineering-cockpit/backend/tests/cockpit/testing/test_scenario_route_absent.py`

- [ ] Expose scenario selection/fault advancement only in the dedicated test app build/dependency override.
- [ ] Assert the production FastAPI app has no testing route and no failpoint activation endpoint.
- [ ] Playwright helper starts/resets a strict scenario and can inspect sanitized journal/assertion results.
- [ ] Do not let browser submit arbitrary fake responses/commands outside scenario schema.
- [ ] Commit: `test: connect playwright to fake tool scenarios`.

### Task 14: Complete full-browser golden paths

**Files:**
- Consolidate/extend: subsystem 13 Playwright specs
- Create: `apps/engineering-cockpit/frontend/e2e/cockpit-golden-paths.spec.ts`
- Create: `apps/engineering-cockpit/frontend/e2e/cockpit-recovery-chaos.spec.ts`

- [ ] Cover golden paths A–E through UI/REST/WebSocket, including two concurrent tasks, request resolution, reconnect, recovery, validation/review/commit, GitHub delivery, and cleanup.
- [ ] Assert generated client/service calls include exact versions/IDs/hashes/idempotency.
- [ ] Run desktop and narrow viewport plus keyboard/axe critical flow.
- [ ] On failure, attach screenshots/traces and sanitized scenario journal.
- [ ] Assert no terminal is required and no merge/deploy control exists.
- [ ] Commit: `test: verify cockpit golden paths in browser`.

### Task 15: Add compatibility matrix and update workflow

**Files:**
- Create: `apps/engineering-cockpit/compatibility.json`
- Create: `apps/engineering-cockpit/docs/updating-toolchain.md`
- Create: `apps/engineering-cockpit/scripts/check-compatibility.sh`
- Create: `apps/engineering-cockpit/backend/tests/release/test_compatibility.py`

- [ ] Record exact/min/max versions and generated hashes from all subsystem manifests.
- [ ] Validate installed tools and lockfile/runtime versions in CI and active diagnostics.
- [ ] Document the required update branch, schema/client generation, affected contract/real acceptance, security review, and rollback.
- [ ] Block unknown app-server and unreviewed major boundary versions.
- [ ] Test malformed/missing/stale compatibility record and generated hash mismatch.
- [ ] Commit: `build: define cockpit compatibility matrix`.

### Task 16: Add backend rollout gates and feature policy

**Files:**
- Create: `apps/engineering-cockpit/backend/cockpit/release/features.py`
- Modify: `apps/engineering-cockpit/backend/core/config.py`
- Create: `apps/engineering-cockpit/backend/tests/release/test_features.py`

**Interfaces:**

```python
class RolloutStage(str, Enum):
    PROTOCOL_SPIKE = "protocol_spike"
    READ_ONLY_ANALYSIS = "read_only_analysis"
    LOCAL_DEVELOPMENT = "local_development"
    DRAFT_PR_DELIVERY = "draft_pr_delivery"
    TEAM_INTERNAL = "team_internal"

class FeaturePolicy:
    def allowed_actions(self, stage: RolloutStage, repository_policy: ...) -> set[str]: ...
```

- [ ] Encode stages/capabilities exactly from the spec.
- [ ] Enforce in backend routes/services; frontend receives allowed actions only.
- [ ] Repository/global policy can reduce stage capabilities but not exceed configured stage.
- [ ] Force/volume/remote-branch operations remain separately permissioned even at final stage.
- [ ] Test every stage/action and attempted frontend/direct-API bypass.
- [ ] Commit: `feat: gate cockpit rollout capabilities`.

### Task 17: Create operator, onboarding, troubleshooting, and architecture documentation

**Files:**
- Create: `apps/engineering-cockpit/docs/architecture.md`
- Create: `apps/engineering-cockpit/docs/install-wsl.md`
- Create: `apps/engineering-cockpit/docs/operator-guide.md`
- Create: `apps/engineering-cockpit/docs/repository-onboarding.md`
- Create: `apps/engineering-cockpit/docs/troubleshooting.md`
- Create: `apps/engineering-cockpit/docs/security.md`
- Modify: `apps/engineering-cockpit/README.md`

- [ ] Architecture links all 15 child specs/plans and identifies authoritative contracts.
- [ ] Install guide starts from current full-stack template, WSL paths, Docker Desktop integration, support services, tool versions, Codex/GitHub auth, skills, service install.
- [ ] Operator guide covers states, controls, diagnostics, trust, recovery, retention, quotas, audit, cleanup.
- [ ] Repository onboarding covers config, branch/base, devcontainer common-dir mount compatibility, Compose isolation, validation profiles, trust review.
- [ ] Troubleshooting covers app-server schema/auth/approval, Git worktree mount, container conflict, reconnect/recovery, validation/hooks/signing, GitHub/rate limits, systemd.
- [ ] Security doc restates threat model/residual risks without credentials.
- [ ] Test links/commands and keep docs synchronized through a docs-link check.
- [ ] Commit: `docs: add cockpit operating documentation`.

### Task 18: Add backup and rollback tooling

**Files:**
- Create: `apps/engineering-cockpit/scripts/backup-local.sh`
- Create: `apps/engineering-cockpit/scripts/restore-local.sh`
- Create: `apps/engineering-cockpit/docs/backup-rollback.md`
- Create: `apps/engineering-cockpit/backend/tests/release/test_backup_scripts.py`

- [ ] Backup stops/drains service, records app/migration/compatibility/runtime inventory, and creates PostgreSQL backup with user-only permissions.
- [ ] It never archives credential homes, target source contents, or Docker volumes by default.
- [ ] Restore requires explicit destination/confirmation and refuses while an owner instance is running.
- [ ] Rollback guide distinguishes Alembic downgrade from database restore and mandates read-only reconciliation before mutations.
- [ ] Test against disposable database, paths with spaces, partial backup, checksum failure, wrong app/migration version, and successful restore.
- [ ] Commit: `ops: add cockpit backup and rollback`.

### Task 19: Generate release evidence and checklist

**Files:**
- Create: `apps/engineering-cockpit/release/checklist.md`
- Create: `apps/engineering-cockpit/scripts/build-release-evidence.py`
- Create: `apps/engineering-cockpit/backend/tests/release/test_release_evidence.py`

- [ ] Collect compatibility record, automated matrix summary, migration report, security checks, known limitations template, rollback-test result, and checksums.
- [ ] Reject raw logs, prompts, diffs, tokens, credentials, and machine-specific local paths through a release-evidence validator/redactor.
- [ ] Checklist contains every release gate from the spec with evidence link/owner/date/result.
- [ ] Require a second Techletes reviewer for threat model/residual risk and an operator sign-off for manual acceptance.
- [ ] Commit: `build: generate cockpit release evidence`.

### Task 20: Add real local acceptance scripts and record template

**Files:**
- Create: `apps/engineering-cockpit/scripts/run-real-acceptance.sh`
- Create: `apps/engineering-cockpit/release/manual-acceptance-template.md`
- Create: `apps/engineering-cockpit/docs/real-acceptance.md`

- [ ] Script validates loopback/service/tool/auth/skills/disposable repository preconditions and prints each manual/partially automated step without outputting secrets.
- [ ] Run two real tasks and collect sanitized IDs/version/hash evidence; do not collect task content/source diff.
- [ ] Include browser reconnect, backend restart, request resolution, validation/commit, draft PR, overlap, cleanup, unrelated-resource survival.
- [ ] Require explicit confirmation before disposable force-with-lease, remote branch deletion, or volume deletion.
- [ ] Fail if repository is production/client/tooling main branch or contains non-test data according to configuration.
- [ ] Commit: `test: script cockpit real acceptance`.

### Task 21: Harden CI workflow and artifact handling

**Files:**
- Modify/create: `.github/workflows/engineering-cockpit-ci.yml`
- Modify/create: `.github/workflows/engineering-cockpit-e2e.yml`
- Modify/create: `.github/workflows/engineering-cockpit-release-evidence.yml`

- [ ] Use path filters for cockpit plus relevant tooling/template contracts.
- [ ] Pin action SHAs/versions and set least permissions.
- [ ] Cache only package/build dependencies, not credentials or mutable test state.
- [ ] Run unit/contract/integration/security/chaos/frontend/E2E in appropriate jobs and serialize shared-resource suites.
- [ ] Upload sanitized test summary, Playwright traces/screenshots, scenario journals, and release evidence with bounded retention.
- [ ] Do not expose secrets to fork/untrusted PR execution and do not run real authenticated acceptance in CI.
- [ ] Add concurrency cancellation for superseded branch CI without cancelling release evidence unexpectedly.
- [ ] Commit: `ci: verify cockpit integration and release gates`.

### Task 22: Execute staged rollout rehearsal

**Files:**
- Create: `apps/engineering-cockpit/release/rollout-rehearsal.md`

- [ ] Start at Stage 0 and prove disabled endpoints/actions return policy errors.
- [ ] Promote sequentially through Stages 1–3 against disposable/internal repositories only after each gate.
- [ ] At every stage, test downgrade to previous stage while preserving tasks/worktrees and blocking newly disabled actions.
- [ ] Rehearse service upgrade, backup, migration, rollback, and read-only reconciliation.
- [ ] Document observed timings/resource use/known limitations and final Stage 4 approval decision.
- [ ] Commit: `test: rehearse cockpit rollout and rollback`.

### Task 23: Complete full release verification

Run the repository's complete preflight plus:

```bash
cd apps/engineering-cockpit
bash scripts/check-compatibility.sh
bash scripts/security-preflight.sh
uv run pytest backend/tests/cockpit backend/tests/integration backend/tests/chaos backend/tests/security backend/tests/release backend/tests/matrix -q
cd frontend
bun run generate-client
bun run typecheck
bun run lint
bun run test:unit
bun run test:e2e
```

- [ ] Run real local acceptance and fill a copy of the manual acceptance template.
- [ ] Generate release evidence and verify its secret/path validator passes.
- [ ] Complete the release checklist with second-developer security review and operator sign-off.
- [ ] Confirm no merge, auto-merge, deployment, broad Docker prune, `rm -rf` worktree cleanup, `--no-verify`, plain `--force`, or TUI scraping path exists.
- [ ] Commit: `test: complete engineering cockpit release verification`.

## Exit criteria

Subsystem 15 is complete when all external boundaries are driven by strict reusable scenarios, every mutation/recovery boundary has fault-injection coverage, golden paths pass through backend and browser, the real two-task/GitHub acceptance is recorded, feature rollout gates are enforced server-side, and backup/rollback/release evidence have been rehearsed and approved.
