# 01 — Template Bootstrap and WSL Runtime Topology Specification

## Purpose

Define exactly how the Engineering Cockpit is created from `TECHLETES/full-stack-template` while remaining inside `TECHLETES/techletes-tooling`, and define where each process runs during development and normal use.

This subsystem must be completed before application features are added. Its output is a clean, reproducible project baseline with no ambiguity about host paths, Docker ownership, database services, or process topology.

## Current template facts

The current template provides:

- FastAPI and SQLModel with Alembic migrations;
- PostgreSQL and Redis services;
- React, TypeScript, Vite, TanStack Router, TanStack Query, Tailwind, shadcn/ui, i18n, and a generated OpenAPI client;
- Playwright frontend tests and Pytest backend tests;
- a Compose-based devcontainer whose primary service is `app` and whose workspace is `/workspaces/app`;
- Docker-outside-of-Docker, GitHub CLI, Node 22, Bun, uv, and Codex CLI;
- a `vscode` remote user;
- a host `~/.codex` bind mount and `CODEX_HOME=/home/vscode/.codex`;
- host GitHub CLI credentials mounted into the devcontainer;
- shared uv and pre-commit download caches;
- project-local `.venv` through `UV_PROJECT_ENVIRONMENT=${containerWorkspaceFolder}/.venv`.

The template's `AGENTS.md` requires downstream projects to update `AGENTS.md` and `README.md` before feature work. The cockpit bootstrap must obey that requirement.

## Selected topology

### Source and development environment

The application source lives at:

```text
TECHLETES/techletes-tooling/apps/engineering-cockpit/
```

The current full-stack template is copied into that directory without its Git history. The existing `superpowers/` planning directory is preserved.

The inherited devcontainer remains the canonical development and CI-like test environment for developers working on the cockpit source.

### Operational control plane

The normal local cockpit daemon runs directly in WSL, not inside the cockpit's own devcontainer:

```text
Windows browser
  -> 127.0.0.1
WSL host
  -> one FastAPI/Uvicorn control-plane process
  -> one frontend dev server during development, or compiled frontend in normal use
  -> Git, GitHub CLI, Docker CLI, Dev Container CLI
  -> owned `devcontainer exec` and app-server child processes
Docker Desktop WSL integration
  -> cockpit PostgreSQL and Redis support services
  -> task devcontainers
```

The backend is run with exactly one Uvicorn worker. Live task runtimes are owned by in-memory asyncio objects and stdio pipes; multiple server workers would create independent process registries and unsafe split ownership.

RQ and Redis workers are not used to own app-server connections. RQ may remain available from the template for unrelated bounded jobs, but interactive task supervision stays in the control-plane process.

### Why the control plane is host-native

Docker bind mounts are resolved by the Docker daemon host, not by an arbitrary client container. The cockpit must pass real WSL paths such as `/home/thom/worktrees/project/task` to Dev Container CLI and Docker. Running the controller directly on WSL avoids:

- mounting broad host repository roots into another privileged controller container;
- translating controller-container paths back to Docker-daemon host paths;
- accidental binds of nonexistent paths on the daemon host;
- permission and ownership differences across nested container boundaries;
- losing direct ownership of subprocess stdin/stdout when the development container is stopped or rebuilt.

This does not change the requirement that Codex itself runs inside each target repository's devcontainer.

## Supporting services

The cockpit retains PostgreSQL and Redis from the full-stack template.

For host-native development and normal local use, a dedicated Compose file starts only supporting services and binds them to loopback:

```text
PostgreSQL: 127.0.0.1:${COCKPIT_POSTGRES_PORT:-55432}
Redis:      127.0.0.1:${COCKPIT_REDIS_PORT:-56379}
```

The ports are configurable to avoid collisions. The Compose project name is explicit and cockpit-specific. No support service is exposed on `0.0.0.0`.

PostgreSQL is the durable source of orchestration state. Redis is used only where its transient pub/sub or existing notification patterns are useful; correctness and event replay do not depend on Redis.

## Bootstrap method

Because the application is a subdirectory of an existing repository, it cannot use GitHub's normal “create repository from template” operation. The bootstrap uses a deterministic template snapshot:

1. Fetch `TECHLETES/full-stack-template` at an explicit commit.
2. Export the commit with `git archive`.
3. Extract it into `apps/engineering-cockpit/` while preserving `superpowers/`.
4. Record the source repository, branch, and commit in `apps/engineering-cockpit/.techletes-template-source.yml`.
5. Adapt project identity and monorepo paths.
6. Move or recreate root-level GitHub workflows under `TECHLETES/techletes-tooling/.github/workflows/` with cockpit path filters, because nested `.github/workflows` directories do not run.

The recorded source commit is informational and supports later template-sync work. Automatic template synchronization is outside this subsystem.

## Required project specialization

Before feature code:

- replace template name, description, URLs, frontend metadata, and visible copy with Engineering Cockpit values;
- update `apps/engineering-cockpit/AGENTS.md` with the architecture and verification commands from this planning package;
- update `apps/engineering-cockpit/README.md` with host-runtime and devcontainer-development instructions;
- preserve template security, typing, generated-client, migration, service-layer, translation, and testing conventions;
- remove or disable template example routes/pages only after the baseline passes and only in a separately reviewed change;
- avoid deleting auth/RBAC until the security specification decides which inherited controls remain active.

## Runtime commands

Canonical host commands are exposed through scripts rather than requiring contributors to remember raw invocations:

```text
scripts/cockpit-services-up.sh
scripts/cockpit-services-down.sh
scripts/cockpit-dev.sh
scripts/cockpit-preflight.sh
```

`cockpit-dev.sh` must:

1. verify it is running under WSL/Linux;
2. verify required binaries and versions;
3. start or verify support services;
4. run database migrations;
5. launch one backend worker bound to loopback;
6. launch the frontend development server bound to loopback;
7. forward termination signals and clean up child processes without removing databases.

Normal compiled operation can serve the frontend through the FastAPI static mount inherited from the template.

## Configuration boundary

Host paths and ports are runtime configuration, never committed personal values. Required settings include:

```text
COCKPIT_REPOSITORY_ROOTS
COCKPIT_WORKTREE_ROOT
COCKPIT_POSTGRES_PORT
COCKPIT_REDIS_PORT
COCKPIT_BACKEND_PORT
COCKPIT_FRONTEND_PORT
COCKPIT_MAX_ACTIVE_TASKS
COCKPIT_MAX_CONCURRENT_CONTAINER_STARTS
```

`COCKPIT_REPOSITORY_ROOTS` is an explicit allowlist of absolute WSL paths. Repository registration cannot escape these roots.

## Risks and mitigations

### Template drift

Risk: copied files become stale relative to the template.

Mitigation: record the exact template commit, preserve its sync metadata where useful, and add a later explicit template-sync workflow rather than silently copying latest files during normal execution.

### Monorepo workflow mismatch

Risk: template workflows assume repository-root paths.

Mitigation: create root workflows with `working-directory: apps/engineering-cockpit` and path filters. Verify every inherited command from that directory.

### Two runtime environments

Risk: development in the devcontainer differs from operational WSL-host execution.

Mitigation: use the same uv and Bun lockfiles, run contract tests in both modes, pin CLI version floors, and keep all external-tool calls behind adapters.

### Multiple backend processes

Risk: split ownership of child processes and WebSocket subscribers.

Mitigation: enforce one worker in scripts, expose the current process/instance ID in diagnostics, and fail startup when a second local control plane holds the instance lock.

### Local port collisions

Mitigation: configurable loopback ports, a diagnostics command that reports owners, and no automatic killing of unrelated processes.

## Verification strategy

The subsystem is accepted only when:

1. the copied template commit is recorded;
2. `AGENTS.md` and `README.md` describe the cockpit rather than the template;
3. backend tests and frontend lint/typecheck/build pass without cockpit features;
4. the inherited devcontainer builds and runs the baseline;
5. the host-mode scripts start PostgreSQL, Redis, one backend worker, and the frontend from WSL;
6. the browser reaches the backend health endpoint and frontend through loopback;
7. a diagnostic test proves the backend sees WSL repository paths and the host Docker daemon;
8. a second control-plane instance refuses to start cleanly.

## Research basis

- [Techletes full-stack template](https://github.com/TECHLETES/full-stack-template)
- [Development Containers specification](https://containers.dev/)
- [Dev Container CLI](https://github.com/devcontainers/cli)
- [Docker bind mounts](https://docs.docker.com/engine/storage/bind-mounts/)
- [Uvicorn deployment and workers](https://www.uvicorn.org/deployment/)
