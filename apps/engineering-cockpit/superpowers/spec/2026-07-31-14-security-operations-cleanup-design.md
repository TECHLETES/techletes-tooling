# 14 — Security, Audit, Quotas, Retention, Cleanup, and Operations Specification

## Purpose

Define the safety boundary for a local application that can run repository-controlled devcontainer builds/hooks, access Docker, mount Codex/GitHub credentials, edit Git worktrees, and control coding agents. This subsystem also defines resource quotas, retained data, guarded cleanup, diagnostics, and how the cockpit runs reliably in WSL.

The cockpit is local-first, but local does not mean low risk. The WSL control plane has developer-level access to source, credentials, Docker, and remote repositories.

## Threat model

Protected assets:

- source code and uncommitted changes;
- Git refs/history and remote branches;
- Codex account state and `CODEX_HOME`;
- GitHub authentication and repository permissions;
- Docker daemon and local containers/volumes;
- issue/PR/model conversation content;
- validation logs/artifacts;
- workstation filesystem outside approved roots.

Relevant threats:

- malicious or compromised repository configuration/Dockerfile/lifecycle hook;
- prompt injection from issue/comment/source content;
- path traversal/symlink escape;
- shell/argument injection;
- unauthorized browser/user action;
- cross-task/container/resource confusion;
- accidental force/cleanup/merge/data loss;
- secret leakage in events/logs/notifications/PR body;
- denial of service through output, processes, containers, disk, or events;
- stale browser command/replay;
- supply-chain drift in Codex/devcontainer/gh/images/dependencies;
- exposing the localhost service on a network interface.

## Trust boundary

A repository must be explicitly marked `trusted` before the cockpit may:

- run its `initializeCommand` on the WSL host;
- build its Dockerfile/features;
- mount writable Codex/GitHub/Git metadata;
- run its lifecycle hooks/scripts;
- start an authenticated agent.

Trust is per canonical repository identity and configuration fingerprint. A changed devcontainer configuration, Dockerfile, Compose file, lifecycle script, or credential mount produces `TRUST_REVIEW_REQUIRED` before the next build/start.

Trust UI shows reviewed file paths/hashes and high-risk features, especially:

- host `initializeCommand`;
- Docker socket mount;
- bind mounts outside repository/cache/credential allowlists;
- privileged containers/capabilities/host network/PID;
- credential mounts;
- external/global mutable volumes;
- remote features/images not digest/version pinned.

Untrusted repositories may be registered for static Git diagnostics but cannot run the devcontainer or authenticated Codex.

## Local network boundary

Operational backend binds to `127.0.0.1` by default. The browser uses same-origin local HTTP.

- CORS allows only configured local origins in development.
- WebSockets validate origin plus authentication.
- Non-loopback binding is refused unless an explicit future remote-access mode supplies TLS, strong auth, and CSRF/origin review; remote mode is not MVP.
- Health endpoints expose no sensitive detail anonymously.
- No public webhook listener is required.

## Authentication and authorization

Preserve the full-stack template's authentication and RBAC.

Permissions:

```text
cockpit:view
cockpit:operate
cockpit:deliver
cockpit:manage
```

- owner with `view`: read own tasks and safe repository metadata;
- owner with `operate`: create/start/message/validate/interrupt/stop own tasks;
- `deliver`: commit/push/PR actions according to repository policy;
- `manage`: repository trust/config, force operations, overrides, cleanup volumes, all-task operations.

Administrative users still need typed confirmations for destructive actions. Authorization is checked server-side on every REST resource and event replay.

## CSRF, origin, and browser security

Follow the inherited auth transport. For cookie-authenticated mutating requests:

- enforce same-site cookie policy and template CSRF strategy;
- validate `Origin`/`Host` for local control endpoints;
- do not expose permissive wildcard CORS with credentials;
- require WebSocket origin and auth;
- use a Content Security Policy compatible with the built frontend;
- prohibit unsafe HTML/eval rendering.

Idempotency/version checks complement but do not replace CSRF/auth.

## External command security

- executable plus argv arrays; no `shell=True`;
- shell scripts only when committed/reviewed and invoked as fixed paths;
- fixed working directory under approved roots;
- environment names allowlisted and values inherited/secret-sourced without persistence;
- output/line/time/process limits;
- process groups for termination;
- no browser/model-controlled host path, executable, Git ref, Docker filter, or environment key without validation;
- all external-tool versions pinned/tested.

## Docker risk

Membership/access to Docker is effectively host-root-equivalent. The operational control plane runs as the normal WSL developer user and talks to Docker Desktop integration; it is not exposed to other users/network.

Target task containers do not receive the Docker socket by default. A repository requesting it is blocked pending explicit trust review and is outside normal development profiles.

The cockpit itself never runs `docker system prune`, broad label/name deletions, or arbitrary Compose project cleanup. It operates only on exact persisted container IDs and exact task/workspace labels.

## Credential handling

Credential sources:

- `CODEX_HOME` mount;
- GitHub CLI config/credential helper;
- Git/SSH/1Password integration;
- package registries and repository env files.

Rules:

- never persist raw tokens, credential files, or complete environment snapshots;
- logs/events redact key-name and value-pattern matches;
- diagnostics expose booleans/provider/login only;
- target task container mounts are listed in trust review;
- PR/notification body excludes local paths/account details;
- source diffs are not silently redacted; secret scanning blocks delivery and requires review/remediation;
- cleanup never deletes host credential directories.

## Prompt and external-content security

Issue bodies, PR comments, CI logs, source files, and model output are untrusted content. They cannot change cockpit execution profile, repository trust, validation commands, delivery permissions, or cleanup behavior.

The task context labels external content and reasserts policy/skills. Only explicit browser/control-plane actions can commit, push, force, create PR, mark ready, clean, merge (not supported), or deploy (not supported).

## Audit model

`CockpitAuditEvent` is append-only and separate from user-facing activity events.

Fields:

- monotonic ID;
- actor user ID or `system`;
- action;
- repository/task/resource IDs;
- expected/current versions and relevant safe SHAs;
- decision/result code;
- safe metadata;
- timestamp and server instance ID.

Audit actions include:

- repository add/trust/config change;
- task create/start/control;
- clarification/approval response;
- validation override;
- commit/push/force/PR/ready/draft;
- recovery acknowledgement/orphan termination;
- rebuild/stop/remove containers/volumes;
- worktree/branch cleanup;
- retention/manual deletion;
- RBAC change.

There is no API to update audit rows. Retention default is longer than ordinary events.

## Resource quotas

Default local limits, configurable downward/upward by a manager:

```text
max active app-server tasks: 4
max concurrent devcontainer starts/builds: 1
max concurrent validations: 2
max active task runtimes: 6
max pending protocol requests per task: 16
max protocol line: 4 MiB
max durable event payload: 256 KiB
max diagnostic log per session: 25 MiB x 3 rotations
max validation artifact per file: 50 MiB
max validation artifacts per batch: 250 MiB
max replay page: 500 events
```

Before creating worktree/container, check configurable minimum free space in WSL filesystem and Docker storage. Quota violation blocks new operations, never kills existing work automatically.

Resource diagnostics show active tasks, containers, approximate worktree/log/artifact sizes, Docker disk usage, queue/semaphore utilization, and retention candidates.

## Retention defaults

Defaults are explicit and configurable:

- audit events: 365 days;
- completed task/domain/delivery metadata: 180 days;
- ordinary activity/conversation events: 30 days after task completion;
- diagnostic stderr/protocol traces: 14 days after session end;
- validation artifacts: 30 days after batch completion;
- unresolved/recovery-required task data: never auto-pruned;
- active task data: never auto-pruned.

A daily retention job runs only under the host single-instance lock. It records counts/bytes and audit results. It does not remove worktrees, containers, branches, commits, or remote resources.

## Guarded cleanup

Cleanup is an explicit multi-stage workflow.

### Assessment

Collect fresh evidence:

- task/turn/request/validation/delivery state;
- owned process/connection and possible orphan;
- Git dirty/unmerged/unpushed/PR state;
- container/network/volume identities and labels;
- worktree path/common-dir registration;
- runtime/artifact/log sizes.

Return blockers and an exact planned action list before any mutation.

### Normal cleanup

1. acquire task lock and cleanup semaphore;
2. interrupt/stop active turn/session cleanly;
3. stop validation/monitoring;
4. verify Git safe-removal assessment;
5. stop exact task containers if policy requests it;
6. remove task worktree with `git worktree remove`;
7. optionally remove exact task containers/networks after verification;
8. preserve mutable volumes by default;
9. retain database/audit/delivery history and mark `CLEANED`.

Branch deletion is a separate explicit action and only allowed when remote/PR/commit reachability is proven.

### Force cleanup

Requires manager permission or policy-authorized owner plus typed confirmation showing:

- exact task/repository/worktree;
- dirty paths/unpushed commits;
- containers/networks/volumes;
- data-loss effects.

Even forced cleanup refuses paths/resources outside configured roots or without exact ownership. Volume deletion is a second separate confirmation. No global prune.

### Idempotency

Cleanup records intent/result per stage. Re-running after crash inspects current reality and continues safely. Missing already-removed exact resources are idempotent success; mismatched resources are recovery blockers.

## Branch deletion

Local branch deletion is separate from worktree cleanup:

- normal `git branch -d` only when Git considers it merged/reachable per policy;
- squash-merged branches may require explicit force deletion after verifying PR merged and tree changes preserved;
- remote branch deletion is another explicit delivery action, not automatic;
- never delete `main`, `staging`, `develop`, `master`, or configured protected branches.

## Operational deployment in WSL

### Development

- inherited devcontainer/Vite/backend workflow;
- backend can run in the cockpit devcontainer for development with explicit host Docker/path mounts;
- external target operations still use real WSL paths and are covered by tests.

### Daily operational use

- backend/control plane runs host-native in WSL as one process/one Uvicorn worker;
- production frontend build is served same-origin by the backend (or an equivalent loopback-only local proxy documented by bootstrap spec);
- PostgreSQL/Redis support services use inherited Compose and bind only to loopback;
- optional WSL systemd user service starts after Docker/support readiness, runs as the user, restarts on failure, and does not run as root;
- host single-instance lock prevents duplicate owner.

Systemd/service environment references an owner-readable env file; secrets are not embedded in unit text. Startup health distinguishes database/Redis/Docker unavailable from app recovery.

## Health and diagnostics

- liveness: backend event loop responds;
- readiness: database, migrations, Redis, host lock, Docker, Git, devcontainer, Codex schema/account/skills, GitHub CLI, and recovery status;
- detailed diagnostics require auth/permission;
- no health endpoint starts/rebuilds/logs in automatically;
- version/config fingerprints and known limitations are visible.

## Supply-chain controls

- pin Codex, Dev Container CLI, GitHub CLI tested ranges;
- pin Python/JS dependencies through uv/Bun locks;
- review Dev Container features/images and prefer immutable versions/digests where practical;
- run dependency vulnerability scan, secret scan, CodeQL/static analysis, lint/type/tests;
- generated Codex schema and OpenAPI client drift checks;
- no automatic dependency upgrade in release path.

## Failure taxonomy

- `REPOSITORY_TRUST_REQUIRED`
- `TRUST_CONFIGURATION_CHANGED`
- `ORIGIN_FORBIDDEN`
- `PERMISSION_DENIED`
- `COMMAND_POLICY_VIOLATION`
- `DOCKER_SOCKET_FORBIDDEN`
- `RESOURCE_QUOTA_EXCEEDED`
- `DISK_SPACE_LOW`
- `RETENTION_JOB_FAILED`
- `CLEANUP_BLOCKED`
- `CLEANUP_IDENTITY_MISMATCH`
- `CLEANUP_FORCE_CONFIRMATION_REQUIRED`
- `CLEANUP_VOLUME_CONFIRMATION_REQUIRED`
- `BRANCH_PROTECTED`
- `BRANCH_DELETE_UNSAFE`
- `OPERATIONAL_DEPENDENCY_UNAVAILABLE`

## Testing strategy

Security:

- RBAC/ownership on every endpoint/event;
- CSRF/origin/CORS/WebSocket-origin;
- path/symlink/ref/argv/environment injection;
- malicious repository `initializeCommand` and trust-fingerprint change;
- Docker socket/privileged/host mount diagnostics;
- secret redaction and secret-scan delivery block;
- XSS/ANSI/external content;
- stale/idempotent/destructive confirmation.

Operations:

- quotas/semaphores/disk thresholds;
- log/artifact/event retention boundaries;
- normal/force cleanup and crash-after-each-stage;
- exact labels/IDs and unrelated resource survival;
- branch deletion/protection/squash merge evidence;
- systemd start/stop/restart, Docker/DB/Redis unavailable, backend crash/recovery;
- same-origin built frontend and loopback binding;
- dependency/schema/client drift CI.

## Acceptance criteria

- Only reviewed trusted repositories can execute host/container code with credentials.
- Every endpoint/event/action is authorized and consequential actions audited.
- External commands, paths, resources, output, and concurrency are bounded.
- Secrets do not appear in stored diagnostics/notifications/PR content.
- Cleanup is previewed, identity-verified, staged, idempotent, and non-destructive by default.
- No code path runs global Docker/Git cleanup, merge, or deployment.
- The one-worker host-native service restarts/reconciles reliably and remains loopback-only.

## Research basis

- [Docker daemon attack surface](https://docs.docker.com/engine/security/)
- [OWASP CSRF prevention](https://owasp.org/www-community/attacks/csrf)
- [OWASP command injection](https://owasp.org/www-community/attacks/Command_Injection)
- [FastAPI security](https://fastapi.tiangolo.com/tutorial/security/)
- [Git safe worktree removal](https://git-scm.com/docs/git-worktree)
- [systemd user services](https://www.freedesktop.org/software/systemd/man/latest/systemd.service.html)
