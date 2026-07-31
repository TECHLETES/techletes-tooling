# 04 — Git Worktrees, Branches, Synchronization, Overlap, and Safe Removal Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `techletes-superpowers:subagent-driven-development` or `techletes-superpowers:executing-plans`. Subsystems 01–03 must be complete. Use `techletes-superpowers:using-git-worktrees` when executing this plan in a development branch.

**Goal:** Implement a machine-safe Git adapter that creates one verified branch/worktree per cockpit task, reports complete status and divergence, assesses overlap between concurrent tasks, and prevents unsafe removal.

**Architecture:** Run Git through argument arrays from the WSL control plane. Parse only NUL-delimited porcelain formats. Persist immutable base/head identifiers through the task store. Keep synchronization advisory and user-initiated.

**Tech stack:** Git 2.45+ (record the tested floor), Python 3.12, asyncio subprocess runner, SQLModel store, Pytest temporary repositories.

## Global constraints

- Branches must pass the existing Techletes validator.
- Create from a fetched remote-tracking ref, never an uncommitted local branch.
- The same branch cannot be active in two worktrees.
- Never parse human-oriented Git output for safety decisions.
- Never automatically rebase, merge, force-push, prune all worktrees, or delete a directory recursively.
- Worktree paths must remain under the configured WSL worktree root after real-path resolution.

---

### Task 1: Add bounded command execution for short Git commands

**Files:**
- Create: `apps/engineering-cockpit/backend/cockpit/runtime/command.py`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/runtime/test_command.py`

**Interfaces:**

```python
@dataclass(frozen=True)
class CommandResult:
    argv: tuple[str, ...]
    cwd: Path
    exit_code: int
    stdout: bytes
    stderr: bytes
    duration_ms: int

class CommandRunner:
    async def run(
        self,
        argv: Sequence[str],
        *,
        cwd: Path,
        timeout: float,
        max_output_bytes: int,
        env: Mapping[str, str] | None = None,
    ) -> CommandResult: ...
```

- [ ] Write tests for non-zero exit, timeout, output limit, cancellation, paths with spaces, and binary/NUL output.
- [ ] Implement with `asyncio.create_subprocess_exec`; never use `shell=True`.
- [ ] Kill the process group on timeout and preserve a bounded stderr tail.
- [ ] Store sanitized argv metadata without environment values.
- [ ] Run focused tests and commit: `feat: add bounded command runner`.

### Task 2: Implement branch policy and collision-safe naming

**Files:**
- Create: `apps/engineering-cockpit/backend/cockpit/git/branching.py`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/git/test_branching.py`

**Interfaces:**

```python
class TaskKind(str, Enum): ...

def build_branch_name(
    *,
    task_kind: TaskKind,
    title: str,
    task_id: UUID,
    issue_number: int | None,
) -> str: ...

def validate_branch_name(branch: str) -> None: ...
```

- [ ] Test every task-kind prefix, Unicode transliteration/drop behavior, punctuation, duplicate slugs, 120-character cap, issue-number placement, and reserved/bare refs.
- [ ] Call the shared validator script from `TECHLETES/techletes-tooling/scripts/validate-branch-name.py` in a contract test so local logic cannot drift silently.
- [ ] Reject `..`, `@{`, trailing dots/slashes, control characters, and other invalid Git ref syntax.
- [ ] Commit: `feat: add cockpit branch naming policy`.

### Task 3: Parse Git worktree porcelain output

**Files:**
- Create: `apps/engineering-cockpit/backend/cockpit/git/worktree_parser.py`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/git/test_worktree_parser.py`

**Interfaces:**

```python
@dataclass(frozen=True)
class GitWorktreeEntry:
    path: Path
    head_sha: str
    branch_ref: str | None
    is_bare: bool
    is_detached: bool
    is_locked: bool
    prunable_reason: str | None


def parse_worktree_porcelain(payload: bytes) -> list[GitWorktreeEntry]: ...
```

- [ ] Fixture-test multiple entries, detached worktree, locked/prunable metadata, paths containing spaces/newlines, and malformed fields.
- [ ] Parse `git worktree list --porcelain -z` as bytes; decode paths with `os.fsdecode`.
- [ ] Reject duplicate paths or branch refs in one response as a typed parse error.
- [ ] Commit: `feat: parse git worktree metadata`.

### Task 4: Implement worktree creation and verification

**Files:**
- Create: `apps/engineering-cockpit/backend/cockpit/git/adapter.py`
- Create: `apps/engineering-cockpit/backend/cockpit/git/errors.py`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/git/test_worktree_adapter.py`

**Interfaces:**

```python
class GitAdapter:
    async def inspect_repository(self, path: Path) -> GitRepositoryInfo: ...
    async def fetch(self, repository: CockpitRepositorySnapshot) -> None: ...
    async def resolve_ref(self, repository_path: Path, ref: str) -> str: ...
    async def create_worktree(
        self,
        *,
        repository_path: Path,
        worktree_path: Path,
        branch_name: str,
        base_ref: str,
    ) -> GitWorktreeEntry: ...
```

- [ ] Build contract fixtures with a bare remote, primary clone, `main`, and `staging` refs.
- [ ] Test success from exact `refs/remotes/origin/staging`, missing base, existing branch, existing path, registered path, same branch already checked out, and fetch failure.
- [ ] Resolve and persist the base SHA before `git worktree add`.
- [ ] After creation, re-list porcelain entries and require exact path, branch ref, and expected head SHA.
- [ ] On partial failure, inspect Git registration and return `GIT_REPAIR_REQUIRED`; do not delete unknown files.
- [ ] Commit: `feat: create verified git worktrees`.

### Task 5: Implement complete machine-readable status parsing

**Files:**
- Create: `apps/engineering-cockpit/backend/cockpit/git/status.py`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/git/test_status.py`

**Interfaces:**

```python
@dataclass(frozen=True)
class GitPathChange:
    path: str
    original_path: str | None
    index_status: str
    worktree_status: str
    kind: str

@dataclass(frozen=True)
class GitStatusSnapshot:
    branch: str | None
    head_sha: str
    detached: bool
    changes: tuple[GitPathChange, ...]
    untracked_paths: tuple[str, ...]
    unmerged_paths: tuple[str, ...]
    ahead: int
    behind: int
    merge_base_sha: str
```

- [ ] Add binary fixtures for porcelain-v2 ordinary, rename/copy, unmerged, untracked, ignored, and branch headers.
- [ ] Test filenames with whitespace, tabs, newlines, and non-UTF-8 bytes through `os.fsdecode` round trips.
- [ ] Execute `git status --porcelain=v2 -z --branch`, `git merge-base`, and `git rev-list --left-right --count` separately.
- [ ] Include committed changes since merge base plus staged, unstaged, and untracked paths in the effective path set.
- [ ] Bound diff reads and return a typed oversized-diff result instead of truncating silently.
- [ ] Commit: `feat: report cockpit git status and divergence`.

### Task 6: Implement overlap assessment

**Files:**
- Create: `apps/engineering-cockpit/backend/cockpit/git/overlap.py`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/git/test_overlap.py`

**Interfaces:**

```python
class OverlapLevel(str, Enum):
    NONE = "none"
    FILE_OVERLAP = "file_overlap"
    HUNK_OVERLAP = "hunk_overlap"
    BASE_CONFLICT_RISK = "base_conflict_risk"
    UNKNOWN = "unknown"

@dataclass(frozen=True)
class OverlapAssessment:
    level: OverlapLevel
    shared_paths: tuple[str, ...]
    overlapping_hunks: tuple[HunkOverlap, ...]
    reasons: tuple[str, ...]
```

- [ ] Test distinct paths, same file/different hunks, same hunk, rename-versus-edit, delete-versus-edit, binary, lockfile, Alembic migration heads, generated route tree, and oversized diff.
- [ ] Parse unified diff hunk headers without interpreting file contents.
- [ ] Elevate known coordination-sensitive paths through a configurable rule set.
- [ ] Keep `FILE_OVERLAP` separate from confirmed conflict risk in API copy.
- [ ] Add a service that compares all active task pairs in one repository after debounced status refresh.
- [ ] Commit: `feat: assess concurrent task overlap`.

### Task 7: Add base synchronization diagnostics

**Files:**
- Create: `apps/engineering-cockpit/backend/cockpit/git/synchronization.py`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/git/test_synchronization.py`

**Interfaces:**

```python
@dataclass(frozen=True)
class SynchronizationAssessment:
    creation_base_sha: str
    current_base_sha: str
    ahead: int
    behind: int
    overlap_level: OverlapLevel
    recommended_action: str
```

- [ ] Advance the remote base in fixtures and test clean fast-forward, independent divergence, overlapping divergence, and already-current branch.
- [ ] Add an advisory dry-conflict probe behind a Git-version capability check; do not mutate the task worktree.
- [ ] Return recommendations (`none`, `fetch_only`, `merge_or_rebase_review`, `sequence_after_other_task`) rather than performing them.
- [ ] Commit: `feat: report task base synchronization risk`.

### Task 8: Implement guarded worktree removal

**Files:**
- Create: `apps/engineering-cockpit/backend/cockpit/git/cleanup.py`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/git/test_cleanup.py`

**Interfaces:**

```python
@dataclass(frozen=True)
class WorktreeRemovalAssessment:
    safe: bool
    blockers: tuple[RemovalBlocker, ...]
    dirty_paths: tuple[str, ...]
    unpushed_commits: tuple[str, ...]

class GitCleanupService:
    async def assess(... ) -> WorktreeRemovalAssessment: ...
    async def remove(..., force: bool, confirmation_path: str | None) -> None: ...
```

- [ ] Test clean merged branch, dirty files, untracked files, unmerged index, unpushed commit, pushed branch, primary-worktree refusal, active runtime blocker, stale registration, and symlink escape.
- [ ] Require exact normalized path confirmation for force removal.
- [ ] Use `git worktree remove`; do not call `rm -rf`.
- [ ] Keep branch deletion separate and unset by default.
- [ ] Expose explicit repair and prune diagnostics without running global prune automatically.
- [ ] Commit: `feat: guard git worktree cleanup`.

### Task 9: Integrate task state and events

**Files:**
- Create: `apps/engineering-cockpit/backend/cockpit/git/service.py`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/git/test_git_service.py`

- [ ] Wrap fetch/create/status/remove operations with subsystem 03 task locks and state transitions.
- [ ] Persist intent before mutation and result after verification.
- [ ] Transition `PREPARING_WORKTREE -> WORKTREE_READY` only after porcelain verification.
- [ ] Emit normalized events for status refresh, overlap changes, divergence, and cleanup blockers.
- [ ] Make repeated create requests idempotent when the persisted workspace matches Git exactly; otherwise return a typed conflict.
- [ ] Commit: `feat: integrate git workspace lifecycle`.

### Task 10: Complete subsystem verification

- [ ] Run:

```bash
cd apps/engineering-cockpit
uv run pytest backend/tests/cockpit/git backend/tests/cockpit/runtime/test_command.py -q
uv run mypy backend/cockpit/git backend/cockpit/runtime/command.py
uv run ruff check backend/cockpit/git backend/cockpit/runtime/command.py
```

- [ ] Run the contract suite against the installed Git version and record it in diagnostics.
- [ ] Manually create two real worktrees for a disposable repository, edit overlapping files, verify the warning level, and verify default cleanup refuses both dirty and unpushed states.
- [ ] Commit: `test: verify cockpit git lifecycle`.

## Exit criteria

Subsystem 04 is complete when branch names comply with shared Techletes policy, every task worktree is created from and verified against an immutable fetched base SHA, status parsing is NUL-safe, overlap/divergence is visible without mutating branches, and cleanup cannot lose work by default.
