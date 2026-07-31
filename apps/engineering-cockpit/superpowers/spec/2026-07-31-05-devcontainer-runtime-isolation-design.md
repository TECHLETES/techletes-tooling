# 05 — Devcontainer Lifecycle, Docker Isolation, Caching, Paths, and Ports Specification

## Purpose

Define how the cockpit turns a task worktree into a reproducible execution environment using the repository's existing Dev Container configuration. The cockpit must reuse images and download caches where safe, isolate mutable project/application state, and expose enough metadata for process launch, diagnostics, recovery, and cleanup.

The Dev Container specification remains the source of truth. The cockpit orchestrates the official CLI; it does not translate `devcontainer.json` into a home-grown Docker model.

## Supported runtime boundary

The WSL control plane invokes:

```text
devcontainer read-configuration --workspace-folder <worktree>
devcontainer up --workspace-folder <worktree> [supported labels]
devcontainer exec --workspace-folder <worktree> <command...>
```

The installed CLI version is pinned and recorded. The adapter contract is tested against that exact version range.

The Dev Container CLI owns configuration resolution, image building, features, Compose overrides, workspace mounting, remote user selection, environment probing, and lifecycle hooks. Docker CLI/API is used only for operations the Dev Container CLI does not expose cleanly, such as inspecting a persisted container ID and explicitly stopping/removing known runtime resources.

## Runtime identity

Every task runtime stores:

- task and workspace IDs;
- local worktree path;
- devcontainer configuration path;
- supported CLI version;
- resolved configuration snapshot fingerprint;
- primary container ID;
- remote workspace folder;
- remote user and home directory;
- runtime kind (`single_container` or `compose`);
- Compose project label/name when available;
- cockpit ID labels applied at creation;
- container start/create timestamps;
- last inspection status.

The cockpit passes stable ID labels when the pinned CLI supports `--id-label`, for example:

```text
techletes.cockpit.task_id=<uuid>
techletes.cockpit.workspace_id=<uuid>
```

Labels aid diagnostics and cleanup but do not replace persisted container IDs.

## Configuration discovery

Before `up`, run `read-configuration` and validate:

- configuration file exists and is under the repository root;
- workspace folder resolves to the task worktree;
- target service/container can be identified;
- remote user is non-root unless explicitly approved;
- workspace mount points at the task worktree;
- lifecycle commands are present and expected;
- Codex CLI and persistent Codex-home requirements can be satisfied;
- referenced Dockerfile, Compose files, features, mounts, and environment files exist;
- no host path escapes configured repository/credential roots.

Resolved configuration is sensitive: environment values and mount sources may reveal local paths or secret locations. Persist only a sanitized subset and a hash.

## Input fingerprint

Compute a diagnostic fingerprint over content and normalized paths of:

- `.devcontainer/devcontainer.json` or configured file;
- referenced Dockerfiles;
- referenced Compose files;
- local feature definitions;
- scripts directly referenced by lifecycle hooks;
- explicit build context metadata.

The fingerprint is used to explain drift. It does not automatically trigger a rebuild. Rebuild is a user action or a recovery action after a typed unusable-runtime diagnosis.

## Start and reuse semantics

### First start

1. Validate configuration and path policy.
2. Acquire the global container-start semaphore.
3. Persist `STARTING_CONTAINER` intent.
4. Run `devcontainer up` with task labels.
5. Parse the CLI's structured terminal result and capture container ID and remote workspace folder.
6. Inspect the primary container through Docker and verify labels, running state, workspace mount, and remote user.
7. Run a small readiness command through `devcontainer exec`.
8. Persist runtime metadata and transition to `CONTAINER_READY`.

### Existing runtime

On resume:

1. Inspect the persisted container ID.
2. If it is running and matches the workspace/task labels, reuse it.
3. If stopped but intact, let `devcontainer up` start/reconcile it without rebuild.
4. If missing, run normal `up` and treat it as a recreated runtime.
5. If fingerprint changed, report drift and require explicit rebuild unless ordinary `up` can safely reconcile without image replacement.

Normal resume never passes a rebuild flag.

## Lifecycle hooks

`initializeCommand` executes in the WSL host context and can mutate the worktree before container creation. The cockpit records start/result events and applies the same time/output limits as other commands.

`postCreateCommand` may install project dependencies into the worktree. It should run only when the CLI determines the container is newly created. `postStartCommand` may run on later starts. `postAttachCommand` is editor-specific and is not relied upon for headless agent readiness.

Repository onboarding diagnostics flag projects that put required agent setup exclusively in `postAttachCommand`.

## Environment reuse and isolation

### Safe to share

- Docker images and build layers;
- immutable tool images;
- package download caches such as uv, Bun/pnpm, and pre-commit caches;
- read-only source registries;
- the authenticated Codex home only under subsystem 08's concurrency policy.

### Must remain task-specific

- worktree files;
- `.venv` and `node_modules` located in the worktree;
- database, Redis, object-storage, search-index, and application-data volumes;
- temporary files and test artifacts;
- app-server process/thread identity;
- dynamically published host ports.

Named cache volumes may be shared only when their tools are designed for concurrent access. Mutable application volumes must not use external/global names.

## Compose isolation diagnostics

Before start, inspect referenced Compose files and warn or block on:

- fixed `container_name` values;
- top-level `name:` or `COMPOSE_PROJECT_NAME` that makes multiple worktrees share one project;
- external volumes or explicit global volume `name:` for mutable data;
- fixed host ports likely to collide;
- bind mounts pointing outside approved roots;
- Docker socket mounts in target repositories without an explicit policy exception;
- services that use the primary repository path instead of the task worktree.

The static scan is best-effort because Compose interpolation and profiles affect the final model. Start errors remain authoritative. The adapter records the effective Compose labels from created containers.

## Ports

Agent execution and internal tests should use the Compose network and container ports rather than publishing services to WSL.

When a human preview is required:

- prefer dynamic host-port allocation;
- bind to `127.0.0.1`;
- discover the assigned port from Docker inspection;
- persist it as runtime metadata;
- never assume every concurrent task can bind the same fixed port.

A fixed port declared by a repository is a readiness blocker for starting a second concurrent runtime unless the repository provides a per-task override.

## Stop, remove, and rebuild

The Dev Container CLI is used for configuration/up/exec. The cockpit does not assume it provides a portable `down` command.

- **Stop task:** interrupt/stop app-server first; keep the devcontainer running by default for fast resume.
- **Stop runtime:** explicitly stop the known primary container and, for a verified Compose project, its known task-labeled containers. Preserve volumes.
- **Remove runtime:** explicit cleanup in subsystem 14; remove only containers/networks carrying the exact task/workspace identity. Mutable volumes require a second confirmation.
- **Rebuild:** explicit command that records drift, stops app-server, invokes the supported CLI rebuild path, and verifies a new primary container. Never rebuild during transparent resume.

Do not use broad filters, global `docker system prune`, or project-name guesses.

## Resource control

Settings bound:

- concurrent container starts/builds;
- startup timeout;
- lifecycle-hook timeout;
- maximum captured output;
- maximum active task runtimes;
- optional per-container CPU/memory recommendations.

The cockpit reports Docker disk usage and stopped task runtimes but does not silently delete them.

## Failure taxonomy

- `DEVCONTAINER_CONFIG_MISSING`
- `DEVCONTAINER_CONFIG_INVALID`
- `DEVCONTAINER_CLI_UNSUPPORTED`
- `DEVCONTAINER_INITIALIZE_FAILED`
- `DEVCONTAINER_BUILD_FAILED`
- `DEVCONTAINER_LIFECYCLE_FAILED`
- `DEVCONTAINER_START_TIMEOUT`
- `DEVCONTAINER_RESULT_PARSE_FAILED`
- `DEVCONTAINER_IDENTITY_MISMATCH`
- `DEVCONTAINER_STOPPED`
- `DEVCONTAINER_MISSING`
- `DEVCONTAINER_DRIFT_DETECTED`
- `DEVCONTAINER_RESOURCE_CONFLICT`
- `DEVCONTAINER_EXEC_FAILED`

## Testing strategy

A fake `devcontainer` executable provides deterministic `read-configuration`, `up`, and `exec` scenarios. A fake Docker adapter returns inspection data. Contract tests cover:

- valid configuration and sanitized fingerprint;
- first start and reuse;
- stopped/missing primary container;
- explicit rebuild;
- initialize/post-create failure;
- malformed CLI output;
- remote workspace path and user;
- labels and identity mismatch;
- Compose versus single-container runtime;
- fixed container names, project names, host ports, external volumes, and bind escapes;
- shared cache versus mutable volume classification;
- paths containing spaces;
- concurrent start semaphore;
- normal resume proving no rebuild flag is used.

A real smoke test uses a disposable clone of `TECHLETES/full-stack-template`, starts two worktrees, runs `devcontainer up` for both, verifies distinct app/database containers and data volumes, and executes `codex --version` inside both.

## Acceptance criteria

- The official CLI resolves and starts the task worktree's configuration.
- First start and reuse are distinguishable and persisted.
- Normal resume never rebuilds.
- The primary container, remote workspace, remote user, and task labels are verified.
- Concurrent worktrees do not share mutable project/application state.
- Fixed resource conflicts are reported before or immediately after start with actionable evidence.
- A task can execute commands inside its container with bidirectional pipes for subsystem 06.
- Stop/removal never targets containers or volumes not proven to belong to the task.

## Research basis

- [Dev Container CLI](https://github.com/devcontainers/cli)
- [Development Containers specification](https://containers.dev/)
- [Dev Container JSON reference](https://containers.dev/implementors/json_reference/)
- [Docker Compose project names](https://docs.docker.com/compose/how-tos/project-name/)
- [Docker bind mounts](https://docs.docker.com/engine/storage/bind-mounts/)
- [Docker published ports](https://docs.docker.com/engine/network/port-publishing/)
