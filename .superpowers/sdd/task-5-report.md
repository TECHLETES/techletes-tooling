# Task 5 report: nested CI

## Status

Implemented the parent-repository Engineering Cockpit CI workflow and removed
the nested reusable CI workflow copies. The non-CI nested automation workflows
(labeler, template synchronization, reconciliation, and staging-to-main gate)
were retained because this task does not provide equivalent parent workflows for
them.

## Changes

- Added `.github/workflows/engineering-cockpit-ci.yml`.
  - Pull requests run only for Engineering Cockpit or this workflow changes.
  - Pushes run only on `main` and only for Engineering Cockpit or this workflow
    changes.
  - Backend job uses PostgreSQL and Redis services, explicit
    `apps/engineering-cockpit` working directories, frozen `uv` installation,
    Alembic migration checks, Ruff, mypy, and pytest.
  - Frontend job uses explicit `apps/engineering-cockpit/frontend` working
    directories, frozen Bun installation, lint, typecheck, and build.
- Removed the nested CI orchestrator and reusable CI copies:
  - `apps/engineering-cockpit/.github/workflows/ci.yml`
  - `test-backend.yml`
  - `test-database.yml`
  - `test-devcontainer.yml`
  - `test-docker-compose.yml`
  - `test-pre-commit.yml`

## Verification

Passed:

- Python YAML parser check for the new workflow.
- `git diff --check`.
- `uv lock --check`.
- `uv sync --frozen`.
- `uv run ruff check backend`.
- `bun install --frozen-lockfile`.
- `bun run lint`.
- `bun run typecheck`.
- `bun run build`.

Did not pass because of existing repository/environment constraints:

- `pre-commit run --all-files` from `apps/engineering-cockpit` fails because
  the inherited root hook configuration resolves missing root-level hook
  scripts, and also reports existing root-project formatting, Bandit,
  pydocstyle, and Ruff findings. It modified files during the run; those
  unrelated generated changes were restored, and no application changes were
  retained.
- `uv run mypy` reports existing errors in `backend/models.py` and
  `backend/api/routes/users.py`.
- `uv run pytest -q` cannot initialize without the required environment
  variables; the new CI job provides them and its PostgreSQL/Redis services.
- `actionlint` is not installed locally. The workflow parses successfully with
  the available YAML parser.

## Scope check

No application source, project state, session log, or progress ledger files
were changed.
