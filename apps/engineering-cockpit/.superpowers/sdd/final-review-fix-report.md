# Final-review fix report

Implementation commit: `1f74c2607e283310d76b649e129951b6369b7713`

## Fixed findings

- Replaced stale template identity with `Techletes Engineering Cockpit` and
  `engineering-cockpit`.
- Closed the launcher startup race by acquiring the runtime lock in the
  backend-launch process before Uvicorn starts, passing the lock descriptor
  through `exec`, and having FastAPI lifespan adopt and release it. The
  launcher still uses exactly one Uvicorn worker and loopback binding.
- Added `scripts/cockpit-preflight.sh` for WSL/Linux, Docker and Compose, Dev
  Container CLI, Codex, Python, uv, Bun, Node, curl, Git, and GitHub CLI checks.
- Added focused identity, preflight, concurrent-launch, and inherited-lock
  regression tests.

## Verification

- `backend/tests/cockpit/test_runtime_instance.py`: 5 passed.
- Launcher shell regressions: lock preflight, backend readiness, and concurrent
  start all passed.
- Identity and preflight shell tests passed.
- `bash -n` passed for launcher, preflight, and shell tests.
- Ruff, Black, mypy, Bandit, pydocstyle, detect-secrets, pip-audit, and other
  applicable pre-commit checks passed.
- Real `scripts/cockpit-preflight.sh` passed in WSL: Docker 29.5.0, Compose
  5.1.3, Dev Container CLI 0.88.0, Codex 0.146.0, uv 0.11.7, Bun 1.3.13,
  Node 25.2.1, Git 2.43.0, and gh 2.45.0.

## Unresolved environment issue

The repository branch hook rejects the assigned `fix/cockpit-01-final-review`
name because it only permits `bug/`, `feature/`, and other listed prefixes.
The frontend SDK pre-commit hook could not run because `openapi-ts` is not
installed in this isolated worktree. Both were explicitly skipped for the
quality rerun; direct backend and focused shell verification passed.
