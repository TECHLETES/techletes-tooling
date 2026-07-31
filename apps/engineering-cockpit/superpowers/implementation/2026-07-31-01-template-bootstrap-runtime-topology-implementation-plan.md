# 01 — Template Bootstrap and WSL Runtime Topology Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `techletes-superpowers:subagent-driven-development` (recommended) or `techletes-superpowers:executing-plans` to implement this plan task-by-task. Use `techletes-superpowers:using-git-worktrees` before modifying the repository. Track progress with the checkboxes below.

**Goal:** Bootstrap `apps/engineering-cockpit/` from an explicit `TECHLETES/full-stack-template` commit and provide a verified single-process WSL runtime with loopback-only PostgreSQL and Redis support services.

**Architecture:** The inherited devcontainer is used to develop and test the cockpit. The operational FastAPI control plane runs directly in WSL with one Uvicorn worker so it owns real host paths, Docker/Dev Container CLI calls, and long-lived app-server stdio connections. PostgreSQL and Redis run as local Docker support services.

**Tech Stack:** Current Techletes full-stack template, Python/uv, FastAPI/Uvicorn, SQLModel/Alembic, PostgreSQL, Redis, React/Vite/Bun, Docker Compose, WSL2.

## Global Constraints

- Preserve `apps/engineering-cockpit/superpowers/` during bootstrap.
- Record an immutable source commit for `TECHLETES/full-stack-template`.
- Update project `AGENTS.md` and `README.md` before feature code.
- Run the operational backend with exactly one worker.
- Bind browser, database, and Redis ports to `127.0.0.1`.
- Do not expose or copy secret values into committed files.
- Do not remove inherited auth/RBAC/example features in this plan.

### Task applicability

These are subsystem exit constraints, not a direction to alter the imported
template during Task 1. Task 1 must import and record the current template
snapshot unchanged except for preserving `superpowers/` and adding source
metadata. Task 2 owns project identity and documentation, Task 3 owns the
loopback-only local support services, and Task 4 owns the single-worker,
loopback-bound operational launcher. Review each task against its stated
scope while preserving these constraints as the subsystem completion gate.

## Dependencies

None. This is the first implementation plan.

## Deliverables

- A complete template-derived app under `apps/engineering-cockpit/`.
- Recorded template source metadata.
- Project-specific instructions and README.
- Loopback support-service Compose configuration.
- Single-instance WSL launch and preflight scripts.
- Root GitHub workflow for the nested app.
- Passing template baseline in devcontainer and host modes.

---

### Task 1: Snapshot and import the current full-stack template

**Files:**
- Preserve: `apps/engineering-cockpit/superpowers/**`
- Create: `apps/engineering-cockpit/.techletes-template-source.yml`
- Populate: all other template files under `apps/engineering-cockpit/`

**Interfaces:**
- `.techletes-template-source.yml` contains exactly `repository`, `branch`, `commit`, and `imported_at`.

- [x] **Step 1: Create an isolated implementation worktree**

```bash
git fetch origin
mkdir -p ~/worktrees/techletes-tooling
git worktree add ~/worktrees/techletes-tooling/cockpit-01-bootstrap \
  -b feature/cockpit-01-bootstrap origin/main
cd ~/worktrees/techletes-tooling/cockpit-01-bootstrap
```

Expected: `git branch --show-current` prints `feature/cockpit-01-bootstrap`.

- [x] **Step 2: Fetch the template into a temporary remote**

```bash
git remote add full-stack-template https://github.com/TECHLETES/full-stack-template.git
git fetch --no-tags full-stack-template main
TEMPLATE_COMMIT="$(git rev-parse full-stack-template/main)"
printf '%s\n' "$TEMPLATE_COMMIT"
```

Expected: a 40-character commit SHA.

- [x] **Step 3: Back up the planning directory and import the snapshot**

```bash
mkdir -p /tmp/engineering-cockpit-superpowers
cp -a apps/engineering-cockpit/superpowers/. \
  /tmp/engineering-cockpit-superpowers/

git archive "$TEMPLATE_COMMIT" | tar -x -C apps/engineering-cockpit

rm -rf apps/engineering-cockpit/superpowers
mkdir -p apps/engineering-cockpit/superpowers
cp -a /tmp/engineering-cockpit-superpowers/. \
  apps/engineering-cockpit/superpowers/
```

Expected: `apps/engineering-cockpit/backend/main.py`, `frontend/package.json`, `.devcontainer/devcontainer.json`, and `superpowers/README.md` all exist.

- [x] **Step 4: Record source metadata**

Create `apps/engineering-cockpit/.techletes-template-source.yml`:

```yaml
repository: TECHLETES/full-stack-template
branch: main
commit: REPLACE_WITH_TEMPLATE_COMMIT
imported_at: 2026-07-31
```

Replace `REPLACE_WITH_TEMPLATE_COMMIT` with the actual SHA from Step 2.

- [x] **Step 5: Verify no nested Git metadata was imported**

```bash
test ! -e apps/engineering-cockpit/.git
git status --short apps/engineering-cockpit | head -20
```

Expected: the test exits `0`; imported files are shown as repository changes.

- [x] **Step 6: Commit the snapshot separately**

```bash
git add apps/engineering-cockpit
git commit -m "feat: bootstrap engineering cockpit from full-stack template"
```

### Task 2: Specialize project identity and agent instructions

**Files:**
- Modify: `apps/engineering-cockpit/AGENTS.md`
- Modify: `apps/engineering-cockpit/README.md`
- Modify: `apps/engineering-cockpit/pyproject.toml`
- Modify: `apps/engineering-cockpit/frontend/package.json`
- Modify: `apps/engineering-cockpit/.devcontainer/devcontainer.json`
- Modify: project-visible metadata/config files containing `full-stack-template`
- Test: `apps/engineering-cockpit/backend/tests/cockpit/test_project_identity.py`

**Interfaces:**
- Python project name: `engineering-cockpit`.
- Frontend package name: `engineering-cockpit-frontend`.
- Devcontainer name: `Techletes Engineering Cockpit`.

- [x] **Step 1: Write the identity regression test**

Create `backend/tests/cockpit/test_project_identity.py`:

```python
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]


def test_template_identity_is_replaced() -> None:
    assert 'name = "engineering-cockpit"' in (
        PROJECT_ROOT / "pyproject.toml"
    ).read_text()
    assert '"name": "engineering-cockpit-frontend"' in (
        PROJECT_ROOT / "frontend/package.json"
    ).read_text()
    assert '"name": "Techletes Engineering Cockpit"' in (
        PROJECT_ROOT / ".devcontainer/devcontainer.json"
    ).read_text()
```

- [x] **Step 2: Run the test and verify failure**

```bash
cd apps/engineering-cockpit
uv run pytest backend/tests/cockpit/test_project_identity.py -v
```

Expected: FAIL because template identifiers are still present.

- [x] **Step 3: Replace identity and documentation**

Update the listed files. `AGENTS.md` must describe:

- the WSL-local single-process control plane;
- target devcontainer execution;
- no multiple Uvicorn workers;
- generated app-server schemas;
- exact backend/frontend validation commands;
- the planning index at `superpowers/README.md`.

`README.md` must explain development mode, host operational mode, required WSL tools, and the issue link.

- [x] **Step 4: Scan for stale user-facing template identity**

```bash
rg -n "full-stack-template|Fullstack Template|Full Stack FastAPI Template" \
  AGENTS.md README.md pyproject.toml frontend/package.json \
  .devcontainer/devcontainer.json
```

Expected: no stale project identity remains; explanatory references to the source template are allowed only in the bootstrap section.

- [x] **Step 5: Run the regression test**

```bash
uv run pytest backend/tests/cockpit/test_project_identity.py -v
```

Expected: PASS.

- [x] **Step 6: Commit**

```bash
git add apps/engineering-cockpit
git commit -m "docs: specialize engineering cockpit project identity"
```

### Task 3: Add loopback-only PostgreSQL and Redis support services

**Files:**
- Create: `apps/engineering-cockpit/docker-compose.local-services.yml`
- Create: `apps/engineering-cockpit/.env.local.example`
- Create: `apps/engineering-cockpit/scripts/cockpit-services-up.sh`
- Create: `apps/engineering-cockpit/scripts/cockpit-services-down.sh`
- Test: `apps/engineering-cockpit/tests/scripts/test_local_services_config.sh`

**Interfaces:**
- Compose project name: `techletes-engineering-cockpit`.
- Defaults: PostgreSQL `55432`, Redis `56379`.
- Both ports bind only to `127.0.0.1`.

- [x] **Step 1: Write a failing shell configuration test**

Create `tests/scripts/test_local_services_config.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

compose_file="docker-compose.local-services.yml"
grep -F 'name: techletes-engineering-cockpit' "$compose_file"
grep -F '127.0.0.1:${COCKPIT_POSTGRES_PORT:-55432}:5432' "$compose_file"
grep -F '127.0.0.1:${COCKPIT_REDIS_PORT:-56379}:6379' "$compose_file"
! grep -E '(^|[[:space:]])-[[:space:]]*"?(0\.0\.0\.0:)?(5432|6379):' "$compose_file"
```

- [x] **Step 2: Run and verify failure**

```bash
bash tests/scripts/test_local_services_config.sh
```

Expected: FAIL because the Compose file does not exist.

- [x] **Step 3: Create the service Compose file**

```yaml
name: techletes-engineering-cockpit
services:
  db:
    image: postgres:18-alpine
    restart: unless-stopped
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-postgres}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:?Set POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB:-engineering_cockpit}
    ports:
      - "127.0.0.1:${COCKPIT_POSTGRES_PORT:-55432}:5432"
    volumes:
      - cockpit-postgres-data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U $${POSTGRES_USER} -d $${POSTGRES_DB}"]
      interval: 5s
      timeout: 5s
      retries: 12
  redis:
    image: redis:8-alpine
    restart: unless-stopped
    ports:
      - "127.0.0.1:${COCKPIT_REDIS_PORT:-56379}:6379"
    healthcheck:
      test: ["CMD-SHELL", "redis-cli ping | grep PONG"]
      interval: 5s
      timeout: 5s
      retries: 12
volumes:
  cockpit-postgres-data:
```

- [x] **Step 4: Add safe launch scripts**

`cockpit-services-up.sh` must load `.env.local`, validate required values, run `docker compose ... up -d --wait`, and print loopback endpoints without printing passwords. `cockpit-services-down.sh` must run `down` without `--volumes` unless a separate explicit destructive command is added later.

- [x] **Step 5: Validate rendered Compose configuration**

```bash
POSTGRES_PASSWORD=test-only \
  docker compose -f docker-compose.local-services.yml config >/tmp/cockpit-compose.yml
bash tests/scripts/test_local_services_config.sh
```

Expected: PASS and no `0.0.0.0` binding in `/tmp/cockpit-compose.yml`.

- [x] **Step 6: Start and health-check services**

```bash
cp .env.local.example .env.local
# Set a local development password in .env.local.
bash scripts/cockpit-services-up.sh
docker compose -f docker-compose.local-services.yml ps
```

Expected: `db` and `redis` report healthy.

- [x] **Step 7: Commit**

```bash
git add apps/engineering-cockpit
git commit -m "build: add cockpit local support services"
```

### Task 4: Add a single-instance WSL process launcher

**Files:**
- Create: `apps/engineering-cockpit/backend/cockpit/runtime_instance.py`
- Create: `apps/engineering-cockpit/scripts/cockpit-dev.sh`
- Test: `apps/engineering-cockpit/backend/tests/cockpit/test_runtime_instance.py`

**Interfaces:**
- `RuntimeInstanceLock.acquire(path: Path) -> RuntimeInstanceLock`.
- A second live process receives `RuntimeInstanceAlreadyRunning`.
- Stale lock metadata is recoverable after PID validation.

- [x] **Step 1: Write tests for live and stale locks**

```python
from pathlib import Path

import pytest

from backend.cockpit.runtime_instance import (
    RuntimeInstanceAlreadyRunning,
    RuntimeInstanceLock,
)


def test_second_instance_is_rejected(tmp_path: Path) -> None:
    first = RuntimeInstanceLock.acquire(tmp_path / "instance.lock")
    try:
        with pytest.raises(RuntimeInstanceAlreadyRunning):
            RuntimeInstanceLock.acquire(tmp_path / "instance.lock")
    finally:
        first.release()


def test_released_lock_can_be_reacquired(tmp_path: Path) -> None:
    path = tmp_path / "instance.lock"
    RuntimeInstanceLock.acquire(path).release()
    RuntimeInstanceLock.acquire(path).release()
```

- [x] **Step 2: Run and verify failure**

```bash
uv run pytest backend/tests/cockpit/test_runtime_instance.py -v
```

Expected: FAIL because the module does not exist.

- [x] **Step 3: Implement an OS file lock**

Use `fcntl.flock(..., LOCK_EX | LOCK_NB)` on Linux. Store non-secret JSON metadata containing PID, start time, and application version. Hold the file descriptor for the process lifetime.

- [x] **Step 4: Implement `scripts/cockpit-dev.sh`**

The script must:

```bash
#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

[[ "$(uname -s)" == "Linux" ]]
grep -qi microsoft /proc/version

bash scripts/cockpit-services-up.sh
cd backend
uv run alembic upgrade head
uv run uvicorn backend.main:app \
  --host 127.0.0.1 \
  --port "${COCKPIT_BACKEND_PORT:-8000}" \
  --workers 1 &
backend_pid=$!
cd ../frontend
bun run dev --host 127.0.0.1 \
  --port "${COCKPIT_FRONTEND_PORT:-5173}" &
frontend_pid=$!
trap 'kill "$backend_pid" "$frontend_pid" 2>/dev/null || true' EXIT INT TERM
wait -n "$backend_pid" "$frontend_pid"
```

Integrate the Python instance lock during application lifespan, not solely in Bash.

- [x] **Step 5: Run tests**

```bash
uv run pytest backend/tests/cockpit/test_runtime_instance.py -v
```

Expected: PASS.

- [x] **Step 6: Manually verify second-instance rejection**

Start `scripts/cockpit-dev.sh`, then in another terminal run the same script. Expected: the second backend exits with a clear “control plane already running” diagnostic without stopping the first.

- [x] **Step 7: Commit**

```bash
git add apps/engineering-cockpit
git commit -m "feat: add single-instance WSL cockpit launcher"
```

### Task 5: Adapt CI for the nested application

**Files:**
- Create: `.github/workflows/engineering-cockpit-ci.yml`
- Modify/remove: `apps/engineering-cockpit/.github/workflows/**` after equivalent root workflows exist

**Interfaces:**
- Workflow triggers only when `apps/engineering-cockpit/**` or its workflow changes.
- Backend and frontend jobs use `working-directory` explicitly.

- [x] **Step 1: Inventory inherited workflows**

```bash
find apps/engineering-cockpit/.github/workflows -maxdepth 1 -type f -print
```

- [x] **Step 2: Create the root workflow**

The workflow must include:

```yaml
on:
  pull_request:
    paths:
      - "apps/engineering-cockpit/**"
      - ".github/workflows/engineering-cockpit-ci.yml"
  push:
    branches: [main]
    paths:
      - "apps/engineering-cockpit/**"
      - ".github/workflows/engineering-cockpit-ci.yml"
```

Backend steps run `uv sync --frozen`, migration checks, lint, mypy, and tests from `apps/engineering-cockpit`. Frontend steps run `bun install --frozen-lockfile`, lint, typecheck, and build from `apps/engineering-cockpit/frontend`.

- [x] **Step 3: Validate workflow syntax and local commands**

```bash
cd apps/engineering-cockpit
uv lock --check
pre-commit run --all-files
cd frontend
bun install --frozen-lockfile
bun run lint
bun run typecheck
bun run build
```

Expected: all commands exit `0`.

- [x] **Step 4: Remove nested workflow copies only after parity review**

Nested `.github/workflows` do not execute in the parent repository. Preserve non-workflow GitHub instructions and templates.

- [x] **Step 5: Commit**

```bash
git add .github/workflows/engineering-cockpit-ci.yml \
  apps/engineering-cockpit/.github
git commit -m "ci: add engineering cockpit path-scoped checks"
```

### Task 6: Complete baseline verification

**Files:**
- Create: `apps/engineering-cockpit/docs/bootstrap-verification.md`

**Dependency clarification (2026-07-31):** This application is a nested
directory in the `techletes-tooling` Git worktree, whereas the inherited
template devcontainer mounts only the application directory. Consequently the
container has no usable `.git` metadata and cannot run `pre-commit
run --all-files`. The exact linked-worktree Git common-directory mount is
owned by subsystem 05a. Record `uv lock --check` and the host quality baseline
here, but leave this in-container pre-commit gate blocked until the 05a
contract is implemented and verified; do not introduce that future runtime
architecture as an unreviewed Task 6 workaround.

- [ ] **Step 1: Verify inherited devcontainer**

```bash
devcontainer up --workspace-folder apps/engineering-cockpit
```

Expected final JSON includes `"outcome":"success"`, a container ID, and `remoteWorkspaceFolder` `/workspaces/app`.

- [ ] **Step 2: Run backend baseline inside the devcontainer**

```bash
devcontainer exec --workspace-folder apps/engineering-cockpit -- \
  bash -lc 'cd /workspaces/app && uv lock --check && pre-commit run --all-files'
```

Expected: exit `0`.

- [ ] **Step 3: Run host-mode baseline**

```bash
cd apps/engineering-cockpit
bash scripts/cockpit-dev.sh
```

In a second terminal:

```bash
curl --fail http://127.0.0.1:8000/api/v1/utils/health-check/
curl --fail http://127.0.0.1:5173/
docker info >/dev/null
devcontainer --version
```

Expected: both HTTP requests succeed and Docker/Dev Container CLI are visible from WSL.

- [ ] **Step 4: Document exact verified versions and deviations**

Record template commit, Python, uv, Bun, Node, Docker, Dev Container CLI, and Codex versions in `docs/bootstrap-verification.md`. Do not record credentials or complete environment dumps.

- [ ] **Step 5: Run full preflight and commit**

```bash
cd apps/engineering-cockpit
uv lock --check
pre-commit run --all-files
cd backend && ./scripts/test.sh && ./scripts/lint.sh
cd ../frontend && bun run lint && bun run typecheck && bun run build
```

Expected: all commands exit `0`.

```bash
git add apps/engineering-cockpit .github/workflows/engineering-cockpit-ci.yml
git commit -m "docs: verify engineering cockpit bootstrap baseline"
```

## Exit Criteria

- The app is demonstrably derived from a recorded full-stack-template commit.
- Project instructions and metadata are cockpit-specific.
- Devcontainer development works.
- WSL host operation works with loopback PostgreSQL and Redis.
- Only one control-plane process can own live sessions.
- Nested workflow assumptions have been corrected.
- All baseline quality checks pass before subsystem 02 starts.
