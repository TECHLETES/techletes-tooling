# Pre-commit scope fix report

## Scope

- Worktree: `/home/thom/worktrees/techletes-tooling/cockpit-01-precommit-scope`
- Branch: `feature/cockpit-01-precommit-scope`
- Confirmed prerequisite: nested cockpit pre-commit configuration was evaluating
  parent-repository files.
- State files were not changed.

## Changes

- Added the top-level pre-commit `files` selector
  `^apps/engineering-cockpit/`.
- Preserved the existing cockpit hooks and their root-relative helper commands.
- Added `apps/engineering-cockpit/tests/scripts/test_pre_commit_scope.sh`, a
  narrow safe check that runs only the non-mutating `check-yaml` hook against:
  - the parent workflow, which must be skipped;
  - the cockpit Compose file, which must pass.
- The check compares `git status --short` before and after execution and fails
  if pre-commit changes any file.

## Verification

Passed:

```text
bash -n apps/engineering-cockpit/tests/scripts/test_pre_commit_scope.sh
uv run pre-commit validate-config apps/engineering-cockpit/.pre-commit-config.yaml
bash apps/engineering-cockpit/tests/scripts/test_pre_commit_scope.sh
```

Observed behavior:

- Parent workflow: `check yaml ... Skipped`.
- Cockpit Compose file: `check yaml ... Passed`.
- Working tree status was unchanged by the verification.

Also passed:

```text
git diff --check
```

No full pre-commit run was performed because many inherited hooks are
auto-modifying or invoke broader project tooling; the requested narrow scope
check is intentionally limited to the safe filtering proof.

## Commit status

Committed as `ba2d2a1` (`fix: scope cockpit pre-commit hooks`) with signing
disabled as authorized. The commit contains only the three files listed above.
No push, merge, `git add .`, hook bypass, or state-file update was performed.
