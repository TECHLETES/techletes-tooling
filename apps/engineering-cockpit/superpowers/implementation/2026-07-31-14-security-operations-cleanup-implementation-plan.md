# 14 — Security, Audit, Quotas, Retention, Cleanup, and Operations Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `techletes-superpowers:subagent-driven-development` or `techletes-superpowers:executing-plans`. Use `techletes-superpowers:codeql-analysis-remediation` and the repository's dependency/security skills during the final security tasks. Subsystems 01–13 must expose stable operations first.

**Goal:** Harden the cockpit's high-privilege local control plane, enforce trust/RBAC/origin/resource limits, add append-only audit and retention, implement identity-safe cleanup, and package a reliable loopback-only WSL service.

**Architecture:** Extend inherited auth/RBAC and settings, centralize security policy in backend services, audit every consequential action, apply quotas before external work, run cleanup as an idempotent staged state machine, and serve the built frontend from the one-worker WSL backend.

**Tech stack:** FastAPI/SQLModel/PostgreSQL, Redis, Docker/Git/devcontainer/Codex/GitHub adapters, systemd user service, detect-secrets/CodeQL/dependency scanners, Pytest/Playwright.

## Global constraints

- Do not weaken inherited authentication to simplify a local MVP.
- No wildcard credentialed CORS or non-loopback bind.
- No global Docker/Git prune or arbitrary recursive deletion.
- Trust/config changes and destructive operations are explicit and audited.
- Active/recovery-required data is never auto-pruned.
- One backend process and one Uvicorn worker own all live sessions.

---

### Task 1: Add cockpit permissions and ownership policy

**Files:**
- Modify: `apps/engineering-cockpit/backend/models.py`
- Modify: inherited RBAC seed/permission modules and initial-data setup
- Create: `apps/engineering-cockpit/backend/cockpit/security/authorization.py`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/security/test_authorization.py`
- Add migration/seed update as required.

**Permissions:**

```text
cockpit:view
cockpit:operate
cockpit:deliver
cockpit:manage
```

- [ ] Add permissions through the template's current RBAC model/seed convention, not a parallel authorization table.
- [ ] Define reusable dependencies/functions for owner-or-permission checks on repository/task/request/delivery/recovery/cleanup resources.
- [ ] Ensure list/replay queries filter unauthorized rows at query time.
- [ ] Test owner/non-owner/admin, disabled user, deleted/restricted owner, and every permission boundary.
- [ ] Update all cockpit routes to use the shared policy.
- [ ] Commit: `feat: enforce cockpit authorization`.

### Task 2: Add repository trust records and fingerprint review

**Files:**
- Modify: `apps/engineering-cockpit/backend/models.py`
- Create: `apps/engineering-cockpit/backend/cockpit/security/trust.py`
- Create: `apps/engineering-cockpit/backend/api/routes/cockpit_trust.py`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/security/test_trust.py`
- Add migration for trust fields/history.

**Interfaces:**

```python
@dataclass(frozen=True)
class TrustAssessment:
    trusted: bool
    reviewed_fingerprint: str | None
    current_fingerprint: str
    high_risk_findings: tuple[RuntimeDiagnostic, ...]
    review_required: bool
```

- [ ] Fingerprint devcontainer JSON, Dockerfiles, Compose files, lifecycle scripts, features/images/mounts, and credential/Docker-socket requests.
- [ ] Block active diagnostics/start when untrusted or fingerprint changed.
- [ ] Add manager-only trust/revoke endpoint requiring exact repository/fingerprint confirmation.
- [ ] Audit actor, old/new fingerprint, and high-risk findings.
- [ ] Test initialize-command change, benign source-only change, symlinked config, Docker socket, privileged/host network/capability, external volume, and credential mount.
- [ ] Commit: `feat: require repository execution trust`.

### Task 3: Harden host/origin/CORS/WebSocket boundary

**Files:**
- Modify: `apps/engineering-cockpit/backend/core/config.py`
- Modify: `apps/engineering-cockpit/backend/main.py`
- Create: `apps/engineering-cockpit/backend/cockpit/security/origin.py`
- Modify: WebSocket auth helper from subsystem 10
- Create: `apps/engineering-cockpit/backend/tests/cockpit/security/test_origin.py`

- [ ] Default bind host to `127.0.0.1`; reject `0.0.0.0`, IPv6-any, or non-loopback config unless an unsupported explicit remote mode is enabled (which still fails MVP startup with actionable message).
- [ ] Restrict allowed origins/hosts to configured same-origin local frontend in production and Vite origins in development.
- [ ] Reuse template CSRF strategy for cookie-mutating requests; add Origin/Host validation where missing.
- [ ] Validate WebSocket Origin and auth before accept.
- [ ] Add CSP and security headers compatible with the built frontend; no unsafe-eval/HTML requirement.
- [ ] Test cross-origin REST/WS, wildcard CORS rejection, forged Host, missing/expired auth, and development origin allowlist.
- [ ] Commit: `security: harden cockpit local web boundary`.

### Task 4: Centralize command/environment/path policy

**Files:**
- Create: `apps/engineering-cockpit/backend/cockpit/security/commands.py`
- Create: `apps/engineering-cockpit/backend/cockpit/security/paths.py`
- Create: `apps/engineering-cockpit/backend/cockpit/security/environment.py`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/security/test_commands_paths_env.py`

**Interfaces:**

```python
class CommandPolicy:
    def validate_argv(self, operation: str, argv: Sequence[str]) -> tuple[str, ...]: ...

class PathPolicy:
    def require_under(self, path: Path, roots: Sequence[Path], *, allow_missing_leaf: bool) -> Path: ...

class EnvironmentPolicy:
    def build(self, operation: str, inherited: Mapping[str, str], requested_names: Sequence[str]) -> Mapping[str, str]: ...
```

- [ ] Route all external adapters through these helpers where applicable.
- [ ] Reject shell metacharacter concern through structural argv, invalid refs, control/NUL chars, symlink escape, missing-parent race, unknown env names, and secret logging.
- [ ] Add property/fuzz tests for paths/refs/argv/filenames.
- [ ] Test TOCTOU-sensitive operations re-resolve immediately before mutation.
- [ ] Commit: `security: centralize cockpit execution policy`.

### Task 5: Implement layered redaction and secret-detection policy

**Files:**
- Create: `apps/engineering-cockpit/backend/cockpit/security/redaction.py`
- Create: `apps/engineering-cockpit/backend/cockpit/security/secret_scan.py`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/security/test_redaction_secret_scan.py`

**Interfaces:**

```python
class Redactor:
    def redact_text(self, value: str) -> str: ...
    def redact_mapping(self, value: Mapping[str, object]) -> dict[str, object]: ...

class SecretScanService:
    async def scan_task_changes(self, task_id: UUID) -> SecretScanResult: ...
```

- [ ] Redact key-name patterns (`token`, `secret`, `password`, `authorization`, private-key fields) and known value patterns while limiting false disclosure.
- [ ] Apply to logs/events/diagnostics/GitHub detail attachments/notifications, not by silently modifying source diffs.
- [ ] Integrate the repository's detect-secrets/pre-commit configuration for changed-file delivery scan.
- [ ] Block commit/push/PR readiness on confirmed/potential secret finding until remediation or manager override with audit.
- [ ] Test common tokens, PEM/private keys, URLs, false positives, split-across-chunks, binary files, and proof secrets never appear in logs/database/public API snapshots.
- [ ] Commit: `security: redact outputs and scan task changes`.

### Task 6: Add append-only audit storage and API

**Files:**
- Modify: `apps/engineering-cockpit/backend/models.py`
- Create: `apps/engineering-cockpit/backend/cockpit/audit/service.py`
- Create: `apps/engineering-cockpit/backend/api/routes/cockpit_audit.py`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/audit/test_audit.py`
- Add migration for `CockpitAuditEvent`.

**Interfaces:**

```python
class AuditService:
    def record(
        self,
        *,
        actor_id: UUID | None,
        action: str,
        resource: AuditResource,
        result_code: str,
        safe_metadata: Mapping[str, object],
    ) -> CockpitAuditEvent: ...
```

- [ ] Add monotonic ID, server instance ID, actor/system, resource IDs, expected/current versions/SHAs, result, safe metadata, timestamp.
- [ ] No update/delete route or store method.
- [ ] Wire every consequential operation listed in the spec; test representative action coverage with a registry/checklist.
- [ ] Add manager-only paginated/filterable read API with export size limit.
- [ ] Test unauthorized, redaction, ordering, system actor, failed action, and retention boundary.
- [ ] Commit: `feat: add cockpit security audit trail`.

### Task 7: Implement quotas and resource diagnostics

**Files:**
- Modify: `apps/engineering-cockpit/backend/core/config.py`
- Create: `apps/engineering-cockpit/backend/cockpit/operations/quotas.py`
- Create: `apps/engineering-cockpit/backend/cockpit/operations/resources.py`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/operations/test_quotas_resources.py`

**Interfaces:**

```python
@dataclass(frozen=True)
class QuotaSnapshot: ...

class QuotaService:
    async def require_capacity(self, operation: QuotaOperation, user_id: UUID) -> QuotaSnapshot: ...
```

- [ ] Add exact defaults from the spec with bounded configuration validators.
- [ ] Enforce before worktree/container/app-server/validation/artifact/event/log operations.
- [ ] Calculate free WSL filesystem space, Docker disk usage, task/worktree/log/artifact estimates, active semaphores/queues.
- [ ] Never kill active work automatically on quota/disk pressure; block new operation and notify manager.
- [ ] Test each limit, concurrent reservation race, release after failure, low disk, Docker unavailable, and manager config change.
- [ ] Commit: `feat: enforce cockpit resource quotas`.

### Task 8: Add retention policy and scheduled pruning

**Files:**
- Create: `apps/engineering-cockpit/backend/cockpit/operations/retention.py`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/operations/test_retention.py`
- Modify: `apps/engineering-cockpit/backend/cockpit/runtime/context.py`

**Interfaces:**

```python
class RetentionService:
    async def run_once(self, *, now: datetime) -> RetentionReport: ...
```

- [ ] Implement exact default periods and setting validators.
- [ ] Prune only eligible database events/log files/artifacts in bounded batches under host instance lock.
- [ ] Never prune active, pending-request, or recovery-required task data.
- [ ] Update event retention floor transactionally and coordinate with WebSocket reset behavior.
- [ ] Record report counts/bytes/failures in audit; one failed file does not corrupt database retention state.
- [ ] Schedule daily with jitter in the single backend process; allow manager-triggered dry run/run.
- [ ] Test time boundaries, active exemption, audit 365 days, event 30 days, log 14, artifact 30, crash/restart idempotency, and WebSocket cursor below floor.
- [ ] Commit: `feat: retain cockpit data safely`.

### Task 9: Model cleanup assessment and staged plan

**Files:**
- Create: `apps/engineering-cockpit/backend/cockpit/cleanup/models.py`
- Create: `apps/engineering-cockpit/backend/cockpit/cleanup/planner.py`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/cleanup/test_planner.py`

**Interfaces:**

```python
@dataclass(frozen=True)
class CleanupObservation: ...
@dataclass(frozen=True)
class CleanupBlocker: ...
@dataclass(frozen=True)
class CleanupPlan:
    stages: tuple[CleanupStage, ...]
    blockers: tuple[CleanupBlocker, ...]
    destructive_effects: tuple[str, ...]
    confirmation_token: str
```

- [ ] Incorporate task/process/request/validation/delivery, Git cleanup assessment, exact containers/networks/volumes, path ownership, and sizes.
- [ ] Generate a short-lived signed/hashed confirmation token tied to observation fingerprints; stale evidence invalidates it.
- [ ] Test clean/dirty/unpushed/open PR/active turn/validation/orphan/mismatched container/primary worktree/external volume/protected branch.
- [ ] Volume deletion and branch deletion are separate optional stages.
- [ ] Commit: `feat: plan guarded cockpit cleanup`.

### Task 10: Implement idempotent cleanup state machine

**Files:**
- Create: `apps/engineering-cockpit/backend/cockpit/cleanup/service.py`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/cleanup/test_service.py`

**Interfaces:**

```python
class CleanupService:
    async def assess(self, task_id: UUID) -> CleanupPlan: ...
    async def execute(
        self,
        *,
        task_id: UUID,
        expected_task_version: int,
        confirmation_token: str,
        force: bool,
        remove_runtime: bool,
        remove_volumes: bool,
    ) -> CleanupResult: ...
```

- [ ] Persist cleanup intent/stage results and transition to `CLEANUP_PENDING`.
- [ ] Stop app-server/validation/monitoring through their normal services; handle force only when confirmed.
- [ ] Re-run Git/runtime identity immediately before mutation.
- [ ] Remove worktree only through `git worktree remove`; stop/remove exact task containers/networks; preserve volumes by default.
- [ ] Volume deletion requires second explicit confirmation listing exact volume names/labels/data effect.
- [ ] Retain domain/audit history and transition `CLEANED`.
- [ ] Test crash after each stage and idempotent continuation; unrelated resources must survive.
- [ ] Commit: `feat: execute safe cockpit cleanup`.

### Task 11: Add branch deletion service

**Files:**
- Create: `apps/engineering-cockpit/backend/cockpit/cleanup/branches.py`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/cleanup/test_branches.py`

- [ ] Reject protected bare/configured branches.
- [ ] Normal local delete uses `git branch -d`; force local delete requires merged PR/tree-preservation evidence and typed confirmation.
- [ ] Remote branch deletion is separate, explicit, and uses exact expected remote SHA where supported.
- [ ] Test merge commit, squash merge, unmerged/unpushed, remote changed, protected branch, worktree still attached, and repeated deletion.
- [ ] Audit every deletion/result.
- [ ] Commit: `feat: guard cockpit branch deletion`.

### Task 12: Add cleanup/retention/quota APIs and UI service contracts

**Files:**
- Create: `apps/engineering-cockpit/backend/api/routes/cockpit_operations.py`
- Modify: `apps/engineering-cockpit/backend/api/main.py`
- Create: `apps/engineering-cockpit/backend/tests/api/routes/test_cockpit_operations.py`
- Regenerate frontend client
- Create: `apps/engineering-cockpit/frontend/src/services/CockpitOperationsService.ts`

**Endpoints:**

```text
GET  /api/v1/cockpit/operations/resources
POST /api/v1/cockpit/operations/retention/dry-run
POST /api/v1/cockpit/operations/retention/run
GET  /api/v1/cockpit/tasks/{id}/cleanup
POST /api/v1/cockpit/tasks/{id}/cleanup
POST /api/v1/cockpit/tasks/{id}/branch/delete-local
POST /api/v1/cockpit/tasks/{id}/branch/delete-remote
```

- [ ] Enforce owner/manager distinctions, expected versions, confirmation tokens, idempotency, and audit.
- [ ] Public cleanup assessment includes exact safe blockers/effects but hides unauthorized paths/resources.
- [ ] No generic Docker/Git command endpoint.
- [ ] Test all auth/stale/confirmation/error cases.
- [ ] Commit: `feat: expose cockpit operations controls`.

### Task 13: Serve built frontend same-origin

**Files:**
- Modify: `apps/engineering-cockpit/frontend/vite.config.ts`
- Modify: `apps/engineering-cockpit/backend/main.py`
- Create: `apps/engineering-cockpit/backend/cockpit/web/static.py`
- Modify: `apps/engineering-cockpit/scripts/dev.sh`
- Create: `apps/engineering-cockpit/scripts/build-local.sh`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/web/test_static.py`

- [ ] Build frontend into a deterministic directory under the application distribution.
- [ ] Serve hashed assets and SPA fallback from FastAPI only for non-API routes; API/WebSocket routes take precedence.
- [ ] Add cache headers: immutable hashed assets, no-cache index.
- [ ] Add CSP/security headers and loopback-only configuration.
- [ ] Development still uses Vite with explicit local CORS origins.
- [ ] Test asset, SPA route, API 404 separation, CSP, cache headers, and missing build diagnostics.
- [ ] Commit: `build: serve cockpit frontend locally`.

### Task 14: Add WSL host service packaging

**Files:**
- Create: `apps/engineering-cockpit/deploy/systemd/techletes-engineering-cockpit.service`
- Create: `apps/engineering-cockpit/scripts/install-wsl-service.sh`
- Create: `apps/engineering-cockpit/scripts/start-local-support.sh`
- Create: `apps/engineering-cockpit/docs/operations.md`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/operations/test_service_files.py`

- [ ] User service runs host-native app as WSL user, one Uvicorn worker, loopback host/port, explicit working directory, restart policy, no root.
- [ ] Environment file is owner-readable and referenced, not embedded.
- [ ] Startup helper checks Docker Desktop integration and starts/waits for PostgreSQL/Redis support services.
- [ ] Service starts backend; backend recovery handles tasks. Do not start duplicate through tmux.
- [ ] Install script validates systemd availability in WSL, writes only user unit, reloads/enables after confirmation.
- [ ] Test unit syntax, no secrets/root/non-loopback/multi-worker, and document uninstall/recovery/log commands.
- [ ] Commit: `ops: package cockpit wsl service`.

### Task 15: Add readiness/diagnostics endpoints

**Files:**
- Create: `apps/engineering-cockpit/backend/cockpit/operations/health.py`
- Modify: inherited health/diagnostics routes
- Create: `apps/engineering-cockpit/backend/tests/cockpit/operations/test_health.py`

- [ ] Liveness checks only event loop/process.
- [ ] Readiness checks DB/migrations, Redis, host lock, recovery status, Docker, Git, devcontainer, Codex schema/account/skills, GitHub CLI, disk/quota.
- [ ] Anonymous health returns aggregate status only; detailed diagnostics require permission.
- [ ] No check mutates/login/rebuilds.
- [ ] Test each dependency down/degraded/recovering and secret/path redaction.
- [ ] Commit: `feat: report cockpit operational readiness`.

### Task 16: Add security and supply-chain CI gates

**Files:**
- Modify/create root monorepo workflows under `.github/workflows/` using path filters for `apps/engineering-cockpit/**`
- Create: `apps/engineering-cockpit/scripts/security-preflight.sh`
- Modify: `apps/engineering-cockpit/scripts/preflight.sh`

- [ ] Run uv/Bun lock checks, Ruff/mypy/tests, frontend lint/type/unit/E2E, detect-secrets, dependency vulnerability checks, CodeQL/static analysis, generated Codex schema diff, OpenAPI client/route tree/i18n checks, and Docker/devcontainer config lint.
- [ ] Pin action versions and use least GitHub Actions permissions.
- [ ] No real Codex/GitHub credentials in CI; use fake external tools.
- [ ] Fail on unsupported dependency/CLI/schema drift.
- [ ] Commit: `ci: enforce cockpit security gates`.

### Task 17: Run adversarial and cleanup chaos tests

**Files:**
- Create: `apps/engineering-cockpit/backend/tests/security/test_cockpit_adversarial.py`
- Create: `apps/engineering-cockpit/backend/tests/integration/test_cleanup_crash_matrix.py`
- Create: `apps/engineering-cockpit/frontend/e2e/cockpit-security.spec.ts`

- [ ] Cover malicious paths/symlinks/refs/argv/env, untrusted initialize hook, Docker socket/privileged mount, XSS/ANSI/prompt injection, secret output, cross-origin REST/WS, RBAC data isolation, stale confirmation/idempotency.
- [ ] Crash cleanup after each stage and prove only exact task resources are affected.
- [ ] Create unrelated container/volume/worktree/branch and assert survival.
- [ ] Run force cleanup and volume deletion only in fake/disposable resources.
- [ ] Commit: `test: harden cockpit security and cleanup`.

### Task 18: Complete subsystem verification

```bash
cd apps/engineering-cockpit
bash scripts/security-preflight.sh
uv run pytest backend/tests/cockpit/security backend/tests/cockpit/audit backend/tests/cockpit/operations backend/tests/cockpit/cleanup backend/tests/security backend/tests/integration/test_cleanup_crash_matrix.py -q
cd frontend && bun run test:e2e -- cockpit-security.spec.ts
```

- [ ] Install/start/stop/restart the WSL user service and verify loopback binding, one worker, dependency/recovery behavior, logs, and uninstall.
- [ ] Review the threat model and residual risks with another Techletes developer before release.
- [ ] Commit: `test: verify cockpit security and operations`.

## Exit criteria

Subsystem 14 is complete when only reviewed trusted repositories execute; all resources/actions are authorized, bounded, and audited; secrets and external content cannot escape policy; retention is predictable; cleanup cannot affect unproven resources; and the one-worker loopback-only WSL service survives restarts with conservative task recovery.
