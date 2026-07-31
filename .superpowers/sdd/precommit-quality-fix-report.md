# Pre-commit quality and security baseline fix report

## Scope

- Worktree: `/home/thom/worktrees/techletes-tooling/cockpit-01-precommit-quality`
- Branch: `feature/cockpit-01-precommit-quality`
- State files were not changed.
- Only confirmed pre-commit/configuration and Bandit baseline defects were repaired.

## Changes

- Prefixed hook exclusion regexes with `apps/engineering-cockpit/` so they
  match filenames supplied from the parent Git root. Generated client,
  generated email templates, assets, OpenAPI, and coverage exclusions remain
  scoped and effective.
- Replaced the isolated mypy mirror hook with a local hook that runs
  `uv run mypy --config-file pyproject.toml` from the cockpit directory.
- Added a line-level detect-secrets allowlist pragma only to the public
  `TECHLETES/full-stack-template` source commit SHA. A generated high-entropy
  token still fails the same helper, so real secrets are not hidden.
- Replaced the Bandit B108 `/tmp` default with `XDG_RUNTIME_DIR`, falling back
  to a per-user cache directory. Lock parent directories are created with
  mode `0700`.
- Extended the existing parent-root scope check with regression checks for
  exclusions, mypy, detect-secrets, and the default lock location.

## Verification

Passed:

```text
bash -n apps/engineering-cockpit/tests/scripts/test_pre_commit_scope.sh
uv run --project apps/engineering-cockpit pre-commit validate-config apps/engineering-cockpit/.pre-commit-config.yaml
bash apps/engineering-cockpit/tests/scripts/test_pre_commit_scope.sh
uv run --project apps/engineering-cockpit pre-commit run bandit --config apps/engineering-cockpit/.pre-commit-config.yaml --files apps/engineering-cockpit/backend/main.py apps/engineering-cockpit/backend/cockpit/runtime_instance.py
git diff --check
```

The regression script observed parent workflow skipping, cockpit YAML passing,
generated/coverage/test exclusions skipping, mypy passing from the cockpit
environment, detect-secrets passing for the public SHA, and the default lock
path resolving under `/run/user/1234`.

An independent generated high-entropy token check returned detect-secrets exit
code `1`.

`pre-commit run --all-files` was not run because the inherited configuration
contains auto-mutating hooks (Black, nbstripout, jupytext, Ruff `--fix`,
frontend tooling, and client generation); it cannot be considered a
mutation-free narrow verification.

## Commit

The implementation is committed as `c38a7d3` (`fix: repair cockpit pre-commit
security baseline`) with local signing disabled as authorized.
