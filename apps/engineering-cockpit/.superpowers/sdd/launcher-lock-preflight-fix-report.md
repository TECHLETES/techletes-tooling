# Launcher lock preflight fix

## Scope

- Centralized configured/default runtime-lock path resolution in
  `backend.cockpit.runtime_instance`.
- Reused that resolver from backend lifespan ownership and
  `scripts/cockpit-dev.sh`.
- Added a launcher regression that holds the actual `fcntl` lock and verifies
  the launcher exits before migration, backend, or Vite invocation.

## TDD evidence

- RED: `tests/scripts/test_launcher_lock_preflight.sh` failed against the
  pre-fix launcher with `Error: backend exited before becoming ready`; the
  test's migration marker was reached.
- GREEN: the same test passed after the preflight was restored and reported
  `Error: control plane already running (...)`; no migration, backend, or
  frontend marker was created.

## Verification

- `tests/scripts/test_launcher_lock_preflight.sh` — PASS
- `SECRET_KEY=... FRONTEND_HOST=... PROJECT_NAME=... POSTGRES_SERVER=...
  POSTGRES_USER=... POSTGRES_PASSWORD=... POSTGRES_DB=... FIRST_SUPERUSER=...
  FIRST_SUPERUSER_PASSWORD=... REDIS_URL=... uv run pytest
  backend/tests/cockpit/test_runtime_instance.py -q` — 4 passed
- `bash tests/scripts/test_launcher_backend_readiness.sh` — PASS
- `bash tests/scripts/test_launcher_import_path.sh` — PASS
- `bash tests/scripts/test_pre_commit_scope.sh` — PASS
- `uv run mypy` pre-commit hook on changed Python files — PASS
- `uv run pre-commit run pydocstyle --files ...` — PASS
- `uv run ruff check ...` — PASS
- `uv run black --check ...` — PASS
- Bash syntax, Python compilation, and `git diff --check` — PASS

Durable state files were not edited. Remote CI was not run.
