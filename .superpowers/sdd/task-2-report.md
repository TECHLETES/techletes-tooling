# Task 2 report: project identity and documentation

## Status

Complete on branch `feature/cockpit-01-task-02-identity`.

## Changes

- Replaced the Python project identity with `engineering-cockpit` and updated
  project description, keywords, and Techletes Tooling URLs.
- Replaced the frontend package identity with
  `engineering-cockpit-frontend`.
- Updated the corresponding `uv.lock` and `frontend/bun.lock` workspace
  metadata.
- Renamed the devcontainer display name to `Techletes Engineering Cockpit`.
- Rewrote `AGENTS.md` with the WSL-native single-process control-plane model,
  isolated target-devcontainer execution, generated app-server schema rule,
  validation commands, and `superpowers/README.md` planning index.
- Rewrote `README.md` for Engineering Cockpit development mode, WSL host
  operational mode, required tools, repository layout, bootstrap provenance,
  and planning issue #7.
- Added the identity regression test at
  `backend/tests/cockpit/test_project_identity.py`.

## Verification

Passed:

```text
SECRET_KEY=test-secret FRONTEND_HOST=http://localhost:5173 \
PROJECT_NAME='Techletes Engineering Cockpit' POSTGRES_SERVER=localhost \
POSTGRES_USER=test POSTGRES_PASSWORD=test POSTGRES_DB=test \
FIRST_SUPERUSER=admin@example.com FIRST_SUPERUSER_PASSWORD=test-password \
REDIS_URL=redis://localhost:6379/0 \
uv run pytest backend/tests/cockpit/test_project_identity.py -v
```

Result: `1 passed`.

Also passed:

- stale identity scan over `AGENTS.md`, `README.md`, `pyproject.toml`,
  `frontend/package.json`, and `.devcontainer/devcontainer.json`; only the
  two allowed bootstrap-provenance references remain;
- `uv lock --check`;
- JSON parsing of `frontend/package.json` and
  `.devcontainer/devcontainer.json`;
- `git diff --check`.

## Concerns and limits

- The imported test configuration constructs application settings at collection
  time, so the focused pytest command requires the repository's normal
  environment variables. The verification used non-secret local placeholder
  values and did not write an `.env` file.
- Pytest emitted existing coverage no-data and Starlette/httpx deprecation
  warnings; the test itself passed.
- The full backend and frontend suites were not run because this task is limited
  to identity/docs and its focused regression test.
