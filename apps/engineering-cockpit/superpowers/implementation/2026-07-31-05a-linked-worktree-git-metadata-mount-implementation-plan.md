# 05a — Linked-Worktree Git Metadata Mount Compatibility Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `techletes-superpowers:subagent-driven-development` or `techletes-superpowers:executing-plans`. Complete subsystem 04 first. Execute before subsystem 05 is considered complete and before subsystem 11 validation/commit work.

**Goal:** Make host-created linked worktrees fully Git-capable inside their task devcontainers by mounting and verifying the canonical shared Git metadata safely.

**Architecture:** Discover the linked worktree's exact `gitdir` and canonical common directory on the WSL host, pass one version-tested additional bind mount to `devcontainer up`, inspect it through Docker, verify Git inside the container, and coordinate shared metadata mutations per repository.

**Tech stack:** Git, pinned Dev Container CLI, Docker inspection adapter, asyncio locks, Pytest temporary repositories, real full-stack-template smoke test.

## Global constraints

- Never copy, rewrite, or fabricate Git metadata.
- Never accept mount source/target from browser, task prompt, or issue text.
- Mount only the verified Git common directory, not the primary source checkout.
- Source and target are exact absolute paths and the mount is read-write.
- Untrusted repositories cannot receive this mount.
- Do not run as root or recursively chown the host repository as a workaround.

---

### Task 1: Pin the supported Dev Container CLI mount mechanism

**Files:**
- Create: `apps/engineering-cockpit/backend/cockpit/devcontainers/mount_capabilities.py`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/devcontainers/test_mount_capabilities.py`
- Modify: `apps/engineering-cockpit/compatibility.json` when subsystem 15 creates it

**Interfaces:**

```python
@dataclass(frozen=True)
class AdditionalMountCapability:
    supported: bool
    argv_builder_name: str
    tested_cli_version: str
    evidence_hash: str

async def inspect_additional_mount_capability(
    runner: CommandRunner,
    version: DevcontainerCliVersion,
) -> AdditionalMountCapability: ...
```

- [ ] Run and capture sanitized `devcontainer up --help` for the pinned CLI.
- [ ] Inspect the corresponding official CLI source/release documentation and identify the exact supported additional-mount option and format.
- [ ] Add a contract test that invokes the pinned CLI/fake with a disposable bind mount and verifies it appears in Docker inspection.
- [ ] If the pinned version cannot add a runtime mount without changing repository files, mark it unsupported and stop; do not invent a hidden flag or silently modify target repositories.
- [ ] Record the option, tested version, and evidence hash in compatibility metadata.
- [ ] Commit: `build: verify devcontainer additional mounts`.

### Task 2: Discover and validate linked-worktree Git metadata

**Files:**
- Create: `apps/engineering-cockpit/backend/cockpit/git/metadata.py`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/git/test_metadata.py`

**Interfaces:**

```python
@dataclass(frozen=True)
class LinkedWorktreeGitMetadata:
    worktree_path: Path
    dot_git_file: Path
    gitdir_target: Path
    git_common_dir: Path
    git_common_dir_relative_to_repository: str
    fingerprint: str

async def inspect_linked_worktree_metadata(
    git: GitAdapter,
    repository: CockpitRepositorySnapshot,
    worktree: GitWorktreeEntry,
) -> LinkedWorktreeGitMetadata: ...
```

- [ ] Require `.git` to be a regular file for the linked-worktree path and parse only one valid `gitdir:` record.
- [ ] Resolve relative entries against the `.git` file parent and compare with `git rev-parse --git-common-dir`/`--git-path HEAD`.
- [ ] Require the common directory to equal the canonical registered repository common directory.
- [ ] Reject symlink escape, another repository, missing path, multiple records, NUL/control characters, and unexpected primary-worktree `.git` directory.
- [ ] Hash normalized identity fields for later drift detection.
- [ ] Test absolute/relative gitdir, spaces/Unicode, malicious external target, stale worktree registration, and tampering.
- [ ] Commit: `feat: inspect linked worktree git metadata`.

### Task 3: Add per-repository Git metadata mutation locking

**Files:**
- Create: `apps/engineering-cockpit/backend/cockpit/git/repository_locks.py`
- Modify: `apps/engineering-cockpit/backend/cockpit/runtime/context.py`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/git/test_repository_locks.py`

**Interfaces:**

```python
class RepositoryGitLocks:
    @asynccontextmanager
    async def read(self, repository_id: UUID) -> AsyncIterator[None]: ...

    @asynccontextmanager
    async def mutate(self, repository_id: UUID, operation: str) -> AsyncIterator[None]: ...
```

- [ ] Implement a fair reader/writer or conservative mutex policy that prevents shared ref/config/worktree-administration races.
- [ ] Route worktree add/remove/repair, fetch/push, commit, branch delete, and shared config/hook mutations through `mutate`.
- [ ] Status/diff may use `read`; define whether distinct-branch commits serialize until the real concurrency test proves parallel safety.
- [ ] Expose current operation/wait counts in diagnostics without paths/content.
- [ ] Test two repositories concurrently, same-repository mutations serialized, readers, cancellation, starvation avoidance, and cleanup.
- [ ] Commit: `feat: coordinate shared git metadata mutations`.

### Task 4: Build the verified additional mount

**Files:**
- Create: `apps/engineering-cockpit/backend/cockpit/devcontainers/git_metadata_mount.py`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/devcontainers/test_git_metadata_mount.py`

**Interfaces:**

```python
@dataclass(frozen=True)
class GitMetadataMount:
    source: Path
    target: PurePosixPath
    read_only: Literal[False]
    identity_fingerprint: str

class GitMetadataMountBuilder:
    def build(
        self,
        *,
        repository: CockpitRepositorySnapshot,
        metadata: LinkedWorktreeGitMetadata,
        trust: TrustAssessment,
        capability: AdditionalMountCapability,
    ) -> GitMetadataMount: ...
```

- [ ] Require trusted repository and current trust fingerprint.
- [ ] Set source to verified canonical common dir and target to the exact absolute `gitdir`/common-dir path required inside the container.
- [ ] Reject target collision evidence, path outside supported WSL namespace, root/system paths, source/target mismatch, and read-only mode.
- [ ] Build argv through the version-specific mount capability helper; no shell string.
- [ ] Persist only safe fingerprint plus permission-gated path detail.
- [ ] Test all rejection paths and exact argv escaping for spaces/commas/equal signs according to the pinned CLI format.
- [ ] Commit: `feat: build task git metadata mounts`.

### Task 5: Integrate the mount into every devcontainer start/reuse/rebuild

**Files:**
- Modify: `apps/engineering-cockpit/backend/cockpit/devcontainers/adapter.py`
- Modify: `apps/engineering-cockpit/backend/cockpit/devcontainers/models.py`
- Modify: `apps/engineering-cockpit/backend/cockpit/devcontainers/service.py`
- Modify: `apps/engineering-cockpit/backend/tests/cockpit/devcontainers/test_adapter_up.py`

- [ ] Discover metadata and build mount before `devcontainer up`.
- [ ] Pass the same mount on first start, normal resume/reuse, stopped/missing recovery, and explicit rebuild.
- [ ] Include mount identity in runtime/trust/config fingerprints and stored workspace metadata.
- [ ] After CLI result, inspect primary/task containers and require exactly one matching read-write bind mount.
- [ ] Reject missing, duplicate, wrong source/target, read-only, or another-repository mount as `GIT_METADATA_MOUNT_MISSING`/identity mismatch.
- [ ] Ensure ordinary resume still does not rebuild.
- [ ] Test first create, reuse, stopped, recreate, rebuild, identity drift, and trust change.
- [ ] Commit: `feat: mount git metadata in task devcontainers`.

### Task 6: Verify Git inside the container

**Files:**
- Create: `apps/engineering-cockpit/backend/cockpit/devcontainers/git_readiness.py`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/devcontainers/test_git_readiness.py`

**Interfaces:**

```python
@dataclass(frozen=True)
class ContainerGitReadiness:
    inside_worktree: bool
    branch: str
    head_sha: str
    common_dir: str
    writable: bool
    hooks_path: str | None
    signing_status: str

async def verify_container_git(... ) -> ContainerGitReadiness: ...
```

- [ ] Execute fixed Git/Python argv through non-TTY devcontainer exec at the remote workspace.
- [ ] Verify worktree, branch, head, common dir, status, and safe lock/write behavior without creating a commit or changing config.
- [ ] Compare branch/head/common-dir against host observations.
- [ ] Inspect `core.hooksPath`, include-file paths, signing program/config, and whether referenced paths/programs are container-visible.
- [ ] Report unavailable hooks/signing as blockers for commit/delivery, not container startup if analysis remains possible.
- [ ] Test permission denied, wrong branch/head, missing hooks, signing unavailable, remote user root, and tampered `.git` after start.
- [ ] Commit: `feat: verify container git readiness`.

### Task 7: Audit unexpected shared metadata changes

**Files:**
- Create: `apps/engineering-cockpit/backend/cockpit/git/metadata_audit.py`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/git/test_metadata_audit.py`

**Interfaces:**

```python
@dataclass(frozen=True)
class GitMetadataSnapshot:
    refs_hash: str
    config_hash: str
    hooks_hash: str
    worktrees_hash: str

class GitMetadataAuditService:
    async def snapshot(... ) -> GitMetadataSnapshot: ...
    def compare(before: GitMetadataSnapshot, after: GitMetadataSnapshot, allowed: set[str]) -> MetadataChangeAssessment: ...
```

- [ ] Snapshot safe hashes/identities, not object contents or secret config values.
- [ ] Around trusted control-plane Git mutations, declare expected change categories.
- [ ] Detect unexpected config/hooks/other-branch/worktree administration changes and emit audit/recovery warning.
- [ ] Do not continuously hash the entire object database.
- [ ] Test expected branch commit/ref update, unexpected config/hook/ref change, concurrent other task update, and false-positive containment.
- [ ] Commit: `feat: audit shared git metadata changes`.

### Task 8: Add target-container residual-risk diagnostics

**Files:**
- Modify: `apps/engineering-cockpit/backend/cockpit/repositories/diagnostics.py`
- Modify: `apps/engineering-cockpit/backend/cockpit/security/trust.py`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/security/test_git_metadata_trust.py`

- [ ] Show that the trusted task container receives read-write shared Git metadata and explain the effect during trust approval.
- [ ] Include source/target hashes, remote user, sandbox capability, hook/signing readiness, and last verification time.
- [ ] If the pinned Codex sandbox cannot prevent agent access to the mount, record this as an explicit known limitation/residual risk.
- [ ] Untrusted repository or changed mount fingerprint blocks start.
- [ ] Test public path redaction, manager detail, and changed common-dir identity.
- [ ] Commit: `security: expose git metadata mount risk`.

### Task 9: Integrate cleanup ordering

**Files:**
- Modify: `apps/engineering-cockpit/backend/cockpit/cleanup/planner.py`
- Modify: `apps/engineering-cockpit/backend/cockpit/cleanup/service.py`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/cleanup/test_git_metadata_mount_cleanup.py`

- [ ] Add blocker for active process/Git operation/container using the common-dir mount.
- [ ] Stop exact container before host `git worktree remove`.
- [ ] Re-read `.git`/common-dir/mount identity immediately before removal.
- [ ] Never delete the common-directory source or another worktree administrative entry directly.
- [ ] Test normal cleanup, active Git process, stale lock, tampered `.git`, missing container, crash after stop, and unrelated worktree survival.
- [ ] Commit: `feat: clean linked worktrees after container stop`.

### Task 10: Run real two-worktree Git concurrency acceptance

**Files:**
- Create: `apps/engineering-cockpit/scripts/check-linked-worktree-devcontainer-git.sh`
- Create: `apps/engineering-cockpit/backend/tests/manual/linked_worktree_git_mount.md`

- [ ] Use a disposable current full-stack-template clone under WSL.
- [ ] Create two linked worktrees/branches and start two devcontainers with the verified mount.
- [ ] In both containers run status/diff/log, modify/stage distinct files, run hooks, and create distinct commits under the selected repository lock policy.
- [ ] Verify host and container branch/head/index agreement and shared object health (`git fsck` on disposable repository where appropriate).
- [ ] Test parallel status, serialized/parallel distinct commits as policy allows, lock contention, and signing behavior.
- [ ] Stop/remove one task and prove the other worktree/container/Git operations remain healthy.
- [ ] Record Git/Docker/Dev Container CLI versions, mount inspection, remote UID, hook/signing result, and residual risk without source content.
- [ ] Commit: `test: verify linked worktree git mounts`.

### Task 11: Complete subsystem verification

```bash
cd apps/engineering-cockpit
uv run pytest backend/tests/cockpit/git/test_metadata.py backend/tests/cockpit/git/test_repository_locks.py backend/tests/cockpit/git/test_metadata_audit.py backend/tests/cockpit/devcontainers/test_mount_capabilities.py backend/tests/cockpit/devcontainers/test_git_metadata_mount.py backend/tests/cockpit/devcontainers/test_git_readiness.py backend/tests/cockpit/cleanup/test_git_metadata_mount_cleanup.py backend/tests/cockpit/security/test_git_metadata_trust.py -q
uv run mypy backend/cockpit/git backend/cockpit/devcontainers
uv run ruff check backend/cockpit/git backend/cockpit/devcontainers
bash scripts/check-linked-worktree-devcontainer-git.sh
```

- [ ] Update subsystem 05 compatibility documentation and subsystem 11 prerequisites with the recorded mechanism/result.
- [ ] Add the acceptance evidence to subsystem 15's release matrix.
- [ ] Commit: `test: verify git metadata mount compatibility`.

## Exit criteria

Subsystem 05a is complete when the pinned Dev Container CLI exposes a verified additional-mount mechanism, every task container has the exact canonical Git common directory at the worktree-referenced path, Git/hooks/signing are verified or explicitly blocked, shared metadata mutations are coordinated/audited, and two concurrent linked-worktree containers can commit and clean up without corrupting each other.
