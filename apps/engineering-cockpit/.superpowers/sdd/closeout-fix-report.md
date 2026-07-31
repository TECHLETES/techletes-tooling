# Subsystem 01 closeout fix report

## Scope

This closeout fix is limited to the host launcher and the existing post-attach
focused regression test.

## Changes

- The launcher now acquires the runtime instance lock, runs Alembic migrations,
  and only then execs the one-worker Uvicorn process. The lock file descriptor
  remains inherited by Uvicorn, and the existing shell cleanup trap is retained.
- The obsolete template-remote post-attach test now verifies the current
  `DEVCONTAINER_CI=true` behavior: Codex installation is attempted through the
  safe command boundary, private plugin setup is skipped, and no remote or
  network setup is attempted.
- The launcher ordering regression now asserts migrations occur before the
  backend process is execed.

## Verification

Focused checks passed:

```text
bash tests/scripts/test_launcher_import_path.sh
bash tests/scripts/test_post_attach_template_remote.sh
bash tests/scripts/test_launcher_lock_preflight.sh
bash tests/scripts/test_launcher_concurrent_start.sh
bash tests/scripts/test_launcher_backend_readiness.sh
bash tests/scripts/test_launcher_preflight_invocation.sh
bash -n scripts/cockpit-dev.sh .devcontainer/post-attach.sh tests/scripts/test_launcher_import_path.sh tests/scripts/test_post_attach_template_remote.sh
git diff --check
```

## Notes

No controller state, progress ledger, or session log files were changed by
this bounded fixer.
