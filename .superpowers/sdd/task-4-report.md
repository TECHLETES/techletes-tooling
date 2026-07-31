# Task 4 implementer report: runtime launcher

## Status

Implemented and committed the bounded Task 4 runtime launcher work.

Commit: `c765b7c` (`feat: add single-instance WSL cockpit launcher`)

## Changes

- Added `backend/cockpit/runtime_instance.py` with:
  - non-blocking Linux `fcntl.flock` ownership;
  - process-lifetime file descriptor retention;
  - JSON metadata containing PID, UTC start time, and application version;
  - clear `RuntimeInstanceAlreadyRunning` diagnostics;
  - idempotent release and context-manager support;
  - stale metadata recovery when the underlying OS lock is not held.
- Added `backend/cockpit/__init__.py`.
- Integrated lock acquisition and guaranteed release into `backend.main.lifespan`.
  The lock path is configurable with `COCKPIT_INSTANCE_LOCK_PATH` and defaults
  to `/tmp/techletes-engineering-cockpit.lock`.
- Added executable `scripts/cockpit-dev.sh` with Linux/WSL checks, support
  service startup, Alembic migration, one-worker loopback backend, loopback
  frontend, and child-process cleanup.
- Added focused lock tests for live contention, release/reacquisition, and
  stale metadata recovery.

## Verification

Passed:

```text
uv run pytest backend/tests/cockpit/test_runtime_instance.py -v --noconftest
3 passed in 3.35s
uv run ruff check backend/cockpit/runtime_instance.py backend/main.py backend/tests/cockpit/test_runtime_instance.py
Found 1 error (1 fixed, 0 remaining).
bash -n scripts/cockpit-dev.sh
git diff --check
```

The focused test command from the brief was also attempted:

```text
uv run pytest backend/tests/cockpit/test_runtime_instance.py -v
```

It could not collect because this checkout has no root `.env` and the global
test `conftest.py` imports settings requiring ten environment variables before
the focused tests run. The isolated command above passed with the repository's
global conftest disabled; it exercises the three lock tests directly.

An additional direct lifespan smoke check passed with required settings supplied:
the first lifespan acquired the lock, the second raised
`RuntimeInstanceAlreadyRunning` with `control plane already running`, and the
first lifespan then released the lock.

## Concerns / follow-up

- The launcher references `scripts/cockpit-services-up.sh`, which is expected
  to be supplied by the support-services task; it was not added or modified in
  this bounded task.
- The requested live two-terminal launcher verification was not run because
  it would invoke the support-services script and require the local service
  environment.
- The report is intentionally outside the application commit scope and does
  not modify controller-owned state files.
