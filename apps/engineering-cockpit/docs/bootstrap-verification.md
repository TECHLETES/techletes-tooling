# Engineering Cockpit bootstrap verification

Verification date: 2026-07-31

Closeout fix commit: `b55e94f`

## Provenance

- Template: `TECHLETES/full-stack-template`
- Template branch: `main`
- Template commit: `5388b49919cf4bae16b4764b3711099c1dffa047`
- Imported at: `2026-07-31`

## Verified tool versions

- Python: `3.12.3`
- uv: `0.11.7 (x86_64-unknown-linux-gnu)`
- Bun: `1.3.13`
- Node: `v25.2.1`
- Docker: `29.5.0`, build `98f1464`
- Codex CLI: `codex-cli 0.146.0`
- Dev Container CLI: `0.88.0`, invoked as `bunx --bun @devcontainers/cli`

## Baseline results

| Check | Result | Evidence |
| --- | --- | --- |
| `bunx --bun @devcontainers/cli up --workspace-folder . --skip-post-attach` | Passed | Returned `outcome: success`, container `1d009a1c…`, and `/workspaces/app`. |
| Normal Dev Container attach | Blocked by environment credentials | The inherited `postAttachCommand` reaches the private Techletes marketplace through SSH; this environment cannot authenticate to `git@github.com:TECHLETES/techletes-tooling.git`. No credential workaround was added. |
| Devcontainer `uv lock --check` | Passed | Ran inside `/workspaces/app`. |
| Devcontainer `pre-commit run --all-files` | Blocked by subsystem dependency | The nested app bind mount has no `.git`; pre-commit exits with `FatalError: git failed`. Mounting linked-worktree Git metadata is expressly owned by subsystem 05a. |
| `bash scripts/cockpit-services-up.sh` | Passed | PostgreSQL and Redis reported healthy on `127.0.0.1:55432` and `127.0.0.1:56379`. |
| `bash scripts/cockpit-preflight.sh` | Passed | Verified WSL/Linux plus Docker, Compose, Dev Container CLI, Codex, Python, uv, Bun, Node, curl, Git, and GitHub CLI. |
| Host `bash scripts/cockpit-dev.sh` | Passed | One Uvicorn worker bound to `127.0.0.1:8000`; Vite bound to `127.0.0.1:5173`. |
| Host health and frontend checks | Passed | `curl --fail` returned `true` from `/api/v1/utils/health-check/`; the frontend root returned success. |
| Second host launcher | Passed | Exited before migration/frontend startup with `control plane already running` for the runtime lock. |
| `docker info >/dev/null` | Passed | Exit code `0`. |
| `uv lock --check` | Passed | Exit code `0` from `apps/engineering-cockpit`. |
| `pre-commit run --all-files` | Passed | All configured cockpit hooks passed. |
| `backend/scripts/test.sh -n 0` | Passed | With `AZURE_TENANT_ID=test-tenant` and host test containers; 206 passed, 8 skipped. Serial execution is required because the app intentionally enforces one runtime lock. |
| `backend/scripts/lint.sh` | Known inherited baseline deviation | Black passed, but the script's unrestricted mypy invocation reports existing untyped migration/test-helper errors. The configured pre-commit mypy hook passed. |
| `frontend bun run lint` | Passed | Exit code `0`. |
| `frontend bun run typecheck` | Passed | Exit code `0`. |
| `frontend bun run build` | Passed | Exit code `0`. |
| Launcher migration ordering | Passed | Focused regression verifies migrations execute before Uvicorn is execed while the inherited runtime lock remains held. |
| CI-safe post-attach behavior | Passed | Focused regression verifies `DEVCONTAINER_CI=true` skips private plugin setup and performs no template-remote or network setup. |

No credentials or complete environment dumps are included. The devcontainer Git
metadata gap is a recorded dependency contradiction between this Task 6
baseline and the later subsystem 05a ownership boundary; it must be resolved
by an approved plan correction before subsystem 01 can satisfy that exact
in-container pre-commit step.

The normal parallel `backend/scripts/test.sh` invocation also conflicts with
the newly enforced singleton runtime lock because multiple xdist workers start
the FastAPI lifespan concurrently. The verified baseline uses `-n 0`; changing
test parallelism or lock semantics is outside this closeout scope.
