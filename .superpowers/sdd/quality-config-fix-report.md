# Quality/config fix report

## Changes

- Updated `apps/engineering-cockpit/.pre-commit-config.yaml` so local hooks,
  helper working directories, and path filters work when pre-commit is invoked
  from the repository root.
- Formatted the Task 4 runtime module with Ruff. The Task 4 test and launcher
  files were already formatted and were not changed.
- No project state files were modified.

## Verification

Passed:

- `uv run --directory apps/engineering-cockpit pre-commit validate-config .pre-commit-config.yaml`
- Root-invoked `validate-branch-name` hook using the app config
- `uv run ruff format --check backend/cockpit/runtime_instance.py backend/tests/cockpit/test_runtime_instance.py`
- `uv run ruff check backend/cockpit/runtime_instance.py backend/tests/cockpit/test_runtime_instance.py`
- `bash -n scripts/cockpit-dev.sh`
- `git diff --check`
- `uv run pytest backend/tests/cockpit/test_runtime_instance.py -v --noconftest` — 4 passed

Full repository pre-commit and test suites were not run.

## Commit status

The requested commit was attempted, but Git could not create it because this
checkout's required SSH signing agent (`op-ssh-sign-wsl.exe` via 1Password) is
unavailable in the environment. No signing or verification bypass was used.
