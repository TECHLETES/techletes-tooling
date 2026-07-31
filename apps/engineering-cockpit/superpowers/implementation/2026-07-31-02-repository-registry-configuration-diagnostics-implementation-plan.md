# 02 — Repository Registry, Configuration, Diagnostics, and Instruction Discovery Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `techletes-superpowers:subagent-driven-development` or `techletes-superpowers:executing-plans`. Execute in a dedicated worktree and track progress with the checkboxes below.

**Goal:** Add a secure repository registry that validates WSL paths and GitHub identity, parses strict versioned cockpit configuration, reports non-mutating diagnostics, and produces an instruction manifest for later task execution.

**Architecture:** Repository records use the inherited SQLModel/PostgreSQL stack. Pure parsers and path policy live under `backend/cockpit/repositories/`; routes use the template's dependency and permission patterns. Static diagnostics call bounded subprocess adapters. Active checks are registered through a protocol so later devcontainer and app-server subsystems can contribute checks without circular imports.

**Tech Stack:** FastAPI, SQLModel, Alembic, Pydantic v2, Git CLI, GitHub CLI, Dev Container CLI `read-configuration`, generated OpenAPI client, React service/hook conventions.

## Global Constraints

- Depend on the completed subsystem 01 baseline.
- Accept only canonical WSL/Linux paths below configured allowlisted roots.
- Use argument arrays and `create_subprocess_exec`; never build shell command strings.
- Unknown configuration fields are errors.
- Registration performs no container creation.
- Never return raw credentials, environment values, or unsanitized CLI output.
- All database models remain in `backend/models.py` as required by the template.

## Dependencies

- Subsystem 01: bootstrap and WSL runtime topology.

## Deliverables

- Repository and diagnostic SQLModel schemas/migration.
- Strict configuration and provenance model.
- Filesystem/Git identity validation.
- Static diagnostic pipeline and extensible active-check interface.
- Instruction manifest and preset discovery.
- Authenticated repository APIs and generated frontend client methods.

---

### Task 1: Add global allowed-root and version settings

**Files:**
- Modify: `apps/engineering-cockpit/backend/core/config.py`
- Create: `apps/engineering-cockpit/backend/cockpit/repositories/path_policy.py`
- Test: `apps/engineering-cockpit/backend/tests/cockpit/repositories/test_path_policy.py`

**Interfaces:**

```python
class RepositoryPathPolicy:
    def canonical_repository_path(self, candidate: Path) -> Path: ...
    def canonical_worktree_root(self, candidate: Path) -> Path: ...
```

Settings:

```python
COCKPIT_REPOSITORY_ROOTS: list[Path]
COCKPIT_WORKTREE_ROOT: Path
COCKPIT_ALLOW_MNT_C: bool = False
```

- [ ] **Step 1: Write path-policy tests**

Cover valid child paths, exact-root rejection, `..` traversal, symlink escape, `/mnt/c` rejection, missing paths, control characters, and a writable worktree root.

```python
def test_symlink_escape_is_rejected(tmp_path: Path) -> None:
    allowed = tmp_path / "allowed"
    outside = tmp_path / "outside"
    allowed.mkdir()
    outside.mkdir()
    (allowed / "link").symlink_to(outside, target_is_directory=True)
    policy = RepositoryPathPolicy([allowed], tmp_path / "worktrees")
    with pytest.raises(PathNotAllowed):
        policy.canonical_repository_path(allowed / "link")
```

- [ ] **Step 2: Run and verify failure**

```bash
cd apps/engineering-cockpit
uv run pytest backend/tests/cockpit/repositories/test_path_policy.py -v
```

Expected: FAIL because the policy does not exist.

- [ ] **Step 3: Add strict settings parsing**

Parse roots from a JSON array or comma-separated environment value into resolved `Path` objects. Reject an empty list at startup. Do not create repository roots automatically.

- [ ] **Step 4: Implement containment with `Path.relative_to` after resolution**

Reject any candidate containing `\n`, `\r`, `\0`, or other ASCII control characters before subprocess use. Require the worktree root to exist or create only that dedicated root with mode `0700`.

- [ ] **Step 5: Run tests and commit**

```bash
uv run pytest backend/tests/cockpit/repositories/test_path_policy.py -v
git add apps/engineering-cockpit
git commit -m "feat: add cockpit repository path policy"
```

### Task 2: Implement strict versioned repository configuration

**Files:**
- Create: `backend/cockpit/repositories/config.py`
- Create: `backend/cockpit/repositories/defaults.py`
- Test: `backend/tests/cockpit/repositories/test_config.py`
- Fixture: `backend/tests/cockpit/repositories/fixtures/cockpit-v1.yml`

**Interfaces:**

```python
class CockpitRepositoryConfigV1(BaseModel): ...
class EffectiveRepositoryConfig(BaseModel):
    value: CockpitRepositoryConfigV1
    provenance: dict[str, ConfigurationSource]

def load_repository_config(repository_path: Path, global_config: GlobalConfig) -> EffectiveRepositoryConfig: ...
```

- [ ] **Step 1: Write tests for schema and merge behavior**

Test valid v1, missing file defaults, unknown field, unsupported version, command as string rejection, escaping `cwd`, invalid branch prefix, explicit override provenance, and immutable task-disallowed values.

- [ ] **Step 2: Define nested Pydantic models with `extra="forbid"`**

Use enums/literals for sandbox and approval policy. Validation commands use:

```python
class ValidationCommandConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    name: str = Field(pattern=r"^[a-z][a-z0-9-]{0,62}$")
    command: tuple[str, ...] = Field(min_length=1)
    cwd: PurePosixPath = PurePosixPath(".")
    required: bool = True
    timeout_seconds: int = Field(default=900, ge=1, le=7200)
```

Reject empty arguments and control characters.

- [ ] **Step 3: Implement deterministic layer merge and provenance**

Do not use recursive untyped dictionaries as the public interface. Merge validated model dumps, then validate the final model again. Record provenance using dotted field names.

- [ ] **Step 4: Run tests**

```bash
uv run pytest backend/tests/cockpit/repositories/test_config.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add apps/engineering-cockpit
git commit -m "feat: add versioned cockpit repository configuration"
```

### Task 3: Add repository and diagnostic persistence

**Files:**
- Modify: `backend/models.py`
- Create: `backend/alembic/versions/<revision>_add_cockpit_repository_registry.py`
- Test: `backend/tests/cockpit/repositories/test_repository_models.py`

**Interfaces:**

Add SQLModel classes:

```python
class CockpitRepositoryBase(SQLModel): ...
class CockpitRepositoryCreate(CockpitRepositoryBase): ...
class CockpitRepositoryUpdate(SQLModel): ...
class CockpitRepository(CockpitRepositoryBase, table=True): ...
class CockpitRepositoryPublic(CockpitRepositoryBase): ...
class CockpitRepositoriesPublic(SQLModel): ...

class CockpitDiagnosticResult(SQLModel, table=True): ...
class CockpitDiagnosticResultPublic(SQLModel): ...
```

- [ ] **Step 1: Write model tests**

Test UUIDs, unique canonical path, unique Git common directory, unique GitHub full name per active record, soft-disable, diagnostic relationship, UTC timestamps, and public schemas excluding internal output.

- [ ] **Step 2: Add models using existing template timestamp and relationship patterns**

Store paths as normalized strings. Store diagnostic details/remediation as bounded text and structured non-secret JSON. Add indexes on `enabled`, `github_full_name`, and `checked_at`.

- [ ] **Step 3: Generate and review migration**

```bash
cd backend
uv run alembic revision --autogenerate -m "add_cockpit_repository_registry"
uv run alembic upgrade head
uv run alembic downgrade -1
uv run alembic upgrade head
```

Expected: upgrade/downgrade/upgrade all succeed.

- [ ] **Step 4: Run tests and commit**

```bash
cd ..
uv run pytest backend/tests/cockpit/repositories/test_repository_models.py -v
git add apps/engineering-cockpit
git commit -m "feat: persist cockpit repository registry"
```

### Task 4: Implement Git identity and GitHub remote parsing

**Files:**
- Create: `backend/cockpit/repositories/git_identity.py`
- Test: `backend/tests/cockpit/repositories/test_git_identity.py`

**Interfaces:**

```python
@dataclass(frozen=True)
class RepositoryIdentity:
    worktree_root: Path
    git_common_dir: Path
    is_main_worktree: bool
    origin_url: str
    github_full_name: str
    current_branch: str | None

async def inspect_repository_identity(path: Path, runner: ProcessRunner) -> RepositoryIdentity: ...
```

- [ ] **Step 1: Write contract tests with temporary repositories**

Create a bare remote, clone it, create a linked worktree, configure HTTPS/SSH GitHub remotes, and test malformed/non-GitHub remotes.

- [ ] **Step 2: Implement Git calls**

Use:

```text
git -C <path> rev-parse --show-toplevel
git -C <path> rev-parse --path-format=absolute --git-common-dir
git -C <path> remote get-url origin
git -C <path> branch --show-current
git -C <path> worktree list --porcelain -z
```

Parse `--porcelain -z`, not localized display output. Identify the first/main worktree and reject linked worktree registration.

- [ ] **Step 3: Parse supported GitHub URL forms**

Support:

```text
https://github.com/OWNER/REPO.git
git@github.com:OWNER/REPO.git
ssh://git@github.com/OWNER/REPO.git
```

Normalize owner/repo while preserving case as returned; compare case-insensitively for uniqueness.

- [ ] **Step 4: Run tests and commit**

```bash
uv run pytest backend/tests/cockpit/repositories/test_git_identity.py -v
git add apps/engineering-cockpit
git commit -m "feat: inspect cockpit repository identity"
```

### Task 5: Build the diagnostic framework and static checks

**Files:**
- Create: `backend/cockpit/repositories/diagnostics.py`
- Create: `backend/cockpit/repositories/diagnostic_checks.py`
- Test: `backend/tests/cockpit/repositories/test_diagnostics.py`

**Interfaces:**

```python
class DiagnosticCheck(Protocol):
    code: str
    category: str
    async def run(self, context: RepositoryDiagnosticContext) -> DiagnosticResult: ...

class DiagnosticRegistry:
    def register_static(self, check: DiagnosticCheck) -> None: ...
    def register_active(self, check: DiagnosticCheck) -> None: ...
    async def run_static(self, context: RepositoryDiagnosticContext) -> list[DiagnosticResult]: ...
    async def run_active(self, context: RepositoryDiagnosticContext) -> list[DiagnosticResult]: ...
```

- [ ] **Step 1: Write tests for ordering, timeout, exception conversion, redaction, and static/active separation**

- [ ] **Step 2: Implement static checks**

Required codes:

```text
path.allowed
git.identity
git.origin
git.base_branch
git.worktree_root
devcontainer.configuration
tooling.git
tooling.gh
tooling.docker
tooling.devcontainer
tooling.codex
github.authentication
instructions.required
```

Use `devcontainer read-configuration --workspace-folder <path>` for configuration validation. Registration must not call `devcontainer up`.

- [ ] **Step 3: Add version policy**

Create `backend/cockpit/repositories/tool_versions.py` with parsed semantic versions and tested ranges. A newer untested Codex version yields a warning, not silent pass.

- [ ] **Step 4: Persist result summaries**

Delete/replace only the previous results for the same diagnostic run ID; retain historical runs according to the operations retention policy later.

- [ ] **Step 5: Run tests and commit**

```bash
uv run pytest backend/tests/cockpit/repositories/test_diagnostics.py -v
git add apps/engineering-cockpit
git commit -m "feat: add repository static diagnostics"
```

### Task 6: Build instruction and preset manifests

**Files:**
- Create: `backend/cockpit/repositories/instructions.py`
- Test: `backend/tests/cockpit/repositories/test_instructions.py`

**Interfaces:**

```python
class InstructionReference(BaseModel):
    relative_path: PurePosixPath
    sha256: str
    kind: InstructionKind
    precedence: int
    required: bool

class InstructionManifest(BaseModel):
    repository_id: UUID
    references: tuple[InstructionReference, ...]
    required_skill_names: tuple[str, ...]
    preset_name: str | None
```

- [ ] **Step 1: Test root instructions, missing required files, symlink escape, stable hashes, preset merge, and duplicate skill names**

- [ ] **Step 2: Read only contained regular files**

Open files with containment re-checks. Cap an individual instruction file at 1 MiB and total manifest content at 4 MiB; larger inputs fail with remediation.

- [ ] **Step 3: Produce references and hashes**

Do not persist full instruction content in repository records. Task creation later snapshots the exact manifest and issue input used for reproducibility.

- [ ] **Step 4: Add active skill-check extension point**

Define an `AvailableSkillProvider` protocol returning names and absolute container paths. The app-server subsystem implements it using `skills/list`; until then, active diagnostics report `unknown`, never false success.

- [ ] **Step 5: Run tests and commit**

```bash
uv run pytest backend/tests/cockpit/repositories/test_instructions.py -v
git add apps/engineering-cockpit
git commit -m "feat: discover cockpit repository instructions"
```

### Task 7: Add repository service and API routes

**Files:**
- Create: `backend/cockpit/repositories/service.py`
- Create: `backend/api/routes/cockpit_repositories.py`
- Modify: `backend/api/main.py`
- Modify: `backend/core/rbac.py` or the current permission declaration source
- Test: `backend/tests/api/routes/test_cockpit_repositories.py`

**Interfaces:**

Routes from the specification under `/api/v1/cockpit/repositories`.

- [ ] **Step 1: Write API tests**

Test authenticated authorized access, forbidden user, valid create, duplicate, disallowed path, list, detail, config/provenance, static diagnostics, active diagnostics registration, instruction manifest, soft-disable, and sanitized errors.

- [ ] **Step 2: Implement service transaction boundaries**

Perform filesystem/subprocess inspection before opening a write transaction. Open a short SQLModel session only to persist the final record and diagnostics. Revalidate uniqueness inside the transaction.

- [ ] **Step 3: Add permission**

Register `cockpit:manage` using the template's permission discovery/seeding pattern and require it on every route.

- [ ] **Step 4: Register router**

```python
from backend.api.routes import cockpit_repositories
api_router.include_router(cockpit_repositories.router)
```

- [ ] **Step 5: Run API tests**

```bash
uv run pytest backend/tests/api/routes/test_cockpit_repositories.py -v
```

Expected: PASS.

- [ ] **Step 6: Generate frontend client and verify**

```bash
cd frontend
bun run generate-client
bun run typecheck
```

Expected: generated cockpit repository endpoints/types exist and TypeScript passes.

- [ ] **Step 7: Commit**

```bash
git add apps/engineering-cockpit
git commit -m "feat: add cockpit repository registry API"
```

## Verification Matrix

Run:

```bash
cd apps/engineering-cockpit
uv run pytest backend/tests/cockpit/repositories -v
uv run pytest backend/tests/api/routes/test_cockpit_repositories.py -v
pre-commit run --all-files
cd frontend && bun run typecheck
```

Manual acceptance:

1. Register a clean WSL clone of `TECHLETES/full-stack-template`.
2. Confirm registration does not start a container.
3. Inspect effective config and provenance.
4. Run active diagnostics and confirm the UI/API clearly reports the runtime side effect.
5. Attempt to register a linked worktree, symlink escape, `/mnt/c` clone, duplicate clone, and non-GitHub remote; each must fail with its stable code.

## Exit Criteria

- Repository records are unique by canonical clone identity.
- Configuration is strict, versioned, merged, and attributable.
- Static diagnostics are non-mutating and sanitized.
- Active diagnostics are extensible and never report unavailable checks as pass.
- Instruction manifests are contained, hashed, and reproducible.
- The API and generated frontend client are complete and permission-protected.
