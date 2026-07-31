# Launcher import-path fix report

## Scope

Fixed only the confirmed host-launcher import-path bug. `scripts/cockpit-dev.sh`
now exports the application root in `PYTHONPATH` before changing into `backend`
and invoking Alembic/Uvicorn.

## TDD evidence

- Regression check: `cd apps/engineering-cockpit && bash tests/scripts/test_launcher_import_path.sh`
- Red before implementation: exit `1` because the launcher had no exported root `PYTHONPATH`.
- Green after implementation: exit `0`.

## Verification

- `bash tests/scripts/test_launcher_import_path.sh` — PASS
- `bash -n scripts/cockpit-dev.sh tests/scripts/test_launcher_import_path.sh` — PASS
- `cd backend && PYTHONPATH="$(cd .. && pwd)" uv run python -c 'import backend; print(backend.__file__)'` — PASS
- `uv run --project apps/engineering-cockpit pre-commit run --config apps/engineering-cockpit/.pre-commit-config.yaml --files apps/engineering-cockpit/scripts/cockpit-dev.sh apps/engineering-cockpit/tests/scripts/test_launcher_import_path.sh` — PASS
- `git diff --check` — PASS

## Files changed

- `apps/engineering-cockpit/scripts/cockpit-dev.sh`
- `apps/engineering-cockpit/tests/scripts/test_launcher_import_path.sh`
- This report

No project state, SDD progress, session log, push, merge, or hook bypass was used.

Commit: local signing-disabled commit `fix(cockpit): preserve backend imports in host launcher`.
