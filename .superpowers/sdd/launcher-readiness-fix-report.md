# Host launcher readiness fix

## Scope

Fixed only the confirmed sequencing defect in `scripts/cockpit-dev.sh`: the
frontend is no longer started until the backend has passed its health check or
the launcher exits with a clear startup failure.

## Root cause

The launcher backgrounded Uvicorn and immediately backgrounded Vite. A second
backend instance could therefore reject the runtime lock while the frontend
still attempted to bind port 5173 first.

## TDD evidence

- RED: `bash tests/scripts/test_launcher_backend_readiness.sh` failed against
  the original launcher because the frontend-start marker was created when the
  simulated backend exited before readiness.
- GREEN: the same test now passes; it observes `backend exited before becoming
  ready`, a non-zero launcher exit, and no frontend-start marker.

## Changes

- Added `tests/scripts/test_launcher_backend_readiness.sh`, using isolated fake
  `docker`, `uv`, and `bun` commands.
- Added backend health polling at
  `/api/v1/utils/health-check/` before launching Vite.
- Installed the existing child cleanup trap before backend startup, preserving
  signal cleanup and `--workers 1`.

## Verification

- `bash tests/scripts/test_launcher_backend_readiness.sh` — PASS
- `bash tests/scripts/test_launcher_import_path.sh` — PASS
- `bash tests/scripts/test_local_services_config.sh` — PASS
- `bash -n scripts/cockpit-dev.sh` — PASS
- `git diff --check` — PASS

No state files were edited. No push, merge, `git add .`, or hook bypass was
used.
