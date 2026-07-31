# Techletes Engineering Cockpit Design

## Status

Authoritative product and architecture specification for `TECHLETES/techletes-tooling#7`.

## Goal

Build a local-first engineering cockpit that lets a Techletes developer launch, monitor, interact with, validate, and complete multiple Codex development tasks across multiple repositories from one browser interface.

Each task is isolated as:

```text
Repository
  -> task branch
  -> Git worktree
  -> repository devcontainer
  -> codex app-server process
  -> persistent Codex thread
  -> validation
  -> explicit commit/push/draft PR
```

## Bootstrap requirement

Implementation must start from the current `TECHLETES/full-stack-template`.

Before cockpit-specific code is written:

1. Inspect the current template, `AGENTS.md`, devcontainer, CI, backend, frontend, tests, and dependency conventions.
2. Bootstrap `apps/engineering-cockpit/` from that template.
3. Preserve the template's FastAPI/React architecture and quality tooling.
4. Adapt paths in the implementation plan to the actual template layout.
5. Do not create a competing project structure beside the template structure.

## Supported environment

```text
Windows 11
  -> WSL2 Ubuntu
      -> repositories/worktrees on the Linux filesystem
      -> Docker Desktop WSL integration
      -> Git and GitHub CLI
      -> Dev Container CLI
      -> Codex CLI with app-server
      -> FastAPI cockpit backend
  -> browser on localhost
```

Preferred paths:

```text
/home/<user>/code/techletes/<repository>
/home/<user>/worktrees/<repository>/<task-slug>
```

`/mnt/c/...` is not the preferred repository or worktree location.

## Primary architecture decision

`codex app-server` inside each task's devcontainer is the required primary integration from the first real vertical slice.

```text
Browser
  <-> REST and WebSocket
FastAPI backend in WSL
  <-> newline-delimited JSON-RPC over owned stdin/stdout
`devcontainer exec`
  -> `codex app-server` inside task devcontainer
      -> persistent thread for the task
      -> task worktree as workspace
```

The backend owns the child process and all pipes. It must not scrape the Codex TUI to determine state.

`codex exec --json` is allowed only as a fake/test fixture, degraded one-shot fallback, or diagnostic command. tmux and PTY terminal views are optional diagnostics, not the orchestration protocol.

## Product goals

1. Register and validate local repositories.
2. Start a task from free text, a preset, or a GitHub issue.
3. Create a dedicated branch and worktree from the configured base branch.
4. Start or reuse the repository devcontainer through the official Dev Container CLI.
5. Start Codex app-server inside that devcontainer.
6. Start or resume one persistent Codex thread per task.
7. Stream structured progress, messages, commands, file changes, diffs, errors, token metadata, and turn completion.
8. Surface clarification and approval requests in the browser and return responses to the exact JSON-RPC request.
9. Support follow-up turns, steering, interruption, and safe resume.
10. Run repository validation inside the same devcontainer.
11. Show Git status, diff, validation, PR, CI, and overlap risk centrally.
12. Preserve task state across browser closure and recover conservatively after backend restart.
13. Require explicit user actions for commit, push, PR creation, force operations, cleanup, and merging.

## Non-goals for MVP

- automatic merging or production deployment;
- multi-user SaaS or remote worker pools;
- Kubernetes;
- generic support for every agent provider;
- autonomous semantic merge-conflict resolution;
- multi-agent collaboration within one task;
- billing or token accounting;
- attaching to arbitrary externally started Codex TUI/Desktop sessions.

## Core domain objects

### Repository

Stores local path, GitHub full name, base branch, devcontainer config path, cockpit config path, and enabled state.

### Task

Stores title, prompt, source type/reference, lifecycle state, branch name, repository, and timestamps.

### Workspace

Stores worktree path, base ref, container ID, remote workspace folder, devcontainer config hash, Codex-home strategy, and inspection metadata.

### Agent session

Stores provider, protocol, app-server process metadata, thread ID, active turn ID, capability snapshot, and status.

### Protocol request

Stores task/session, exact JSON-RPC request ID, request kind, prompt/options, pending/answered/rejected/expired state, and response.

### Event

Append-only normalized event with monotonic ID, task ID, sanitized payload, and timestamp.

### Validation and pull request

Persist validation commands/results and GitHub PR/CI/review metadata.

## Task lifecycle

```text
CREATED
-> PREPARING_WORKTREE
-> STARTING_CONTAINER
-> STARTING_APP_SERVER
-> INITIALIZING_APP_SERVER
-> STARTING_THREAD or RESUMING_THREAD
-> STARTING_TURN
-> RUNNING
-> WAITING_FOR_INPUT or WAITING_FOR_APPROVAL
-> RUNNING
-> VALIDATING
-> READY_FOR_REVIEW
-> COMMITTING
-> PUSHING
-> CREATING_PR
-> WAITING_FOR_CI
-> READY_TO_MERGE
-> COMPLETED
```

Exceptional states:

```text
STOPPING
STOPPED
FAILED
CANCELLED
RECOVERY_REQUIRED
CLEANUP_PENDING
```

All transitions are explicit, persisted, and validated server-side.

## App-server protocol requirements

### Process transport

The backend starts app-server through `devcontainer exec`, retains stdin, continuously reads stdout, captures stderr separately, and parses newline-delimited JSON-RPC. Do not require a TTY or expose the experimental app-server WebSocket listener.

### Initialization and compatibility

The adapter must perform initialization, inspect capabilities/version, and fail with a typed compatibility error if required methods or events are unavailable.

### Thread and turn operations

Use current v2 thread/turn APIs where available. Required capabilities include:

- starting and resuming threads;
- reading/reconciling thread history;
- starting turns;
- steering an active turn;
- interrupting an active turn;
- observing thread, turn, item, command, file-change, diff, error, and completion events.

Persist exact external thread, turn, item, and request IDs. Never infer identity from display text.

### Clarification and approvals

For each server-to-client user-input or approval request:

1. Persist the request and exact JSON-RPC request ID before browser notification.
2. Transition to `WAITING_FOR_INPUT` or `WAITING_FOR_APPROVAL`.
3. Send a structured WebSocket event.
4. Render protocol-provided options and/or free-text input.
5. Submit the browser response against the exact request ID.
6. Reject duplicate or stale responses.
7. Return to `RUNNING` only after acceptance.

### Follow-up and interruption

- A follow-up after turn completion starts a new turn on the same thread.
- Additional context during a compatible active turn uses steering with the expected turn ID.
- Stop uses protocol interruption first and waits for the terminal completion event.
- Killing the process is a distinct force-stop action.

## Devcontainer integration

Use the official `devcontainer` CLI; do not reimplement the Dev Container specification.

Required operations:

```text
devcontainer up --workspace-folder <worktree>
devcontainer exec --workspace-folder <worktree> -- <command...>
```

Normal resume must not rebuild. Rebuild is explicit or used only after a diagnosed unusable runtime.

Images/build layers and download caches may be shared. Mutable project environments (`.venv`, `node_modules`) and stateful application data remain task/worktree-specific. Repositories must avoid fixed `container_name` and fixed host-port assumptions.

## Codex authentication and persistence

Codex credentials and thread metadata must be available inside each task container without logging secrets.

Preferred MVP strategy:

- mount a persistent, host-controlled `CODEX_HOME` into the devcontainer;
- derive the target path from the remote user;
- validate permissions and authentication during diagnostics;
- persist the strategy/path and non-secret authentication status;
- verify concurrent use safety before sharing one writable Codex home across multiple containers.

If concurrency/locking is unsafe, use isolated runtime homes with a narrowly scoped authentication handoff.

## Browser and backend recovery

### Browser reconnect

The backend, not the browser, owns the process. Closing the browser does not stop the task. Events are persisted before fan-out and replayed after the client's last event ID.

### Backend restart

A restart loses the owned stdio connection. Recovery must:

1. load non-terminal tasks;
2. verify worktree and container state;
3. identify an orphaned known app-server process without pretending it remains controllable;
4. apply explicit orphan cleanup logic;
5. start and initialize a fresh app-server process;
6. resume the persisted thread;
7. read history and reconcile completed turns;
8. mark ambiguous in-flight turns `RECOVERY_REQUIRED`.

MVP does not promise transparent continuation of a model turn after its stdio owner dies. It preserves the worktree/thread and enables a safe resumed follow-up.

## Repository configuration

```yaml
# .techletes/cockpit.yaml
version: 1
repository:
  base_branch: staging
worktree:
  root: /home/<user>/worktrees
  branch_prefix: feature
devcontainer:
  config_path: .devcontainer/devcontainer.json
  keep_running_on_stop: true
validation:
  commands:
    - uv lock --check
    - pre-commit run --all-files
    - uv run pytest
github:
  create_draft_pr: true
  merge_enabled: false
agent:
  protocol: app-server
  instructions:
    - Follow AGENTS.md and repository conventions.
    - Do not merge pull requests.
    - Ask before destructive changes.
```

## API surface

Repositories:

- `GET/POST /api/repositories`
- `GET /api/repositories/{id}`
- `POST /api/repositories/{id}/validate`

Tasks:

- `GET/POST /api/tasks`
- `GET /api/tasks/{id}`
- `POST /api/tasks/{id}/start`
- `POST /api/tasks/{id}/message`
- `POST /api/tasks/{id}/steer`
- `POST /api/tasks/{id}/interrupt`
- `POST /api/tasks/{id}/resume`
- `POST /api/tasks/{id}/validate`
- `POST /api/tasks/{id}/commit`
- `POST /api/tasks/{id}/push`
- `POST /api/tasks/{id}/pull-request`
- `POST /api/tasks/{id}/cleanup`

Protocol requests:

- `POST /api/protocol-requests/{id}/resolve`

Streaming:

- `WS /api/events`, with task subscriptions and replay after an event ID.

## Security

- bind to `127.0.0.1` by default;
- never persist environment-variable values or credentials;
- redact common secret patterns;
- avoid `shell=True` for subprocesses;
- require explicit approval before force push, force cleanup, destructive Docker cleanup, or merge;
- no automatic merge or deployment;
- use typed execution profiles for analysis, development, dependency updates, and release maintenance.

## UI

Three-column initial layout:

```text
Repositories | Tasks and state | Selected task
```

Task detail tabs:

- Activity
- Agent conversation
- Pending input/approvals
- Changes and current diff
- Validation
- Pull request and CI
- Runtime diagnostics

Status comes from the backend's normalized state/events, never client inference or terminal regexes.

## Concurrency and overlap

Every task receives separate branch, worktree, devcontainer, app-server process, thread, and mutable runtime data.

The cockpit compares active tasks in one repository and reports:

- no shared changed files: low risk;
- shared files: medium risk;
- overlapping hunks/dependent changes: high risk/manual sequencing.

It recommends synchronization/merge order but does not claim to solve semantic conflicts.

## Testing

Unit tests cover transitions, config, branch naming, JSON-RPC correlation, event ordering, redaction, overlap detection, and protocol request states.

Contract tests use fake `git`, `devcontainer`, `codex app-server`, and GitHub transports. The fake app-server must emit initialization, thread/turn/item events, clarification requests, approvals, deltas, file changes, interruption, errors, and completion.

Integration tests cover a full fake vertical slice, browser event replay, backend restart, thread resume, stale request rejection, validation, PR lifecycle, and safe cleanup.

Manual acceptance uses a real repository created from `TECHLETES/full-stack-template` and runs two tasks concurrently.

## MVP acceptance criteria

- Repository registration and diagnostics work.
- A task creates a valid branch/worktree from its base branch.
- Its devcontainer starts through the official CLI.
- App-server starts inside that container and initializes successfully.
- A persistent thread and turn are created.
- Structured events stream to and replay in the browser.
- Clarification and approval requests can be answered from the browser.
- Follow-up, steering, and interruption work.
- Browser closure does not stop the task.
- Backend restart preserves worktree/thread and performs conservative recovery.
- Git status/diff and validation results are visible.
- Commit, push, and draft PR are explicit actions.
- Two tasks run concurrently without sharing branch, worktree, app-server connection, thread, project environment, or mutable application data.
- Dirty/unmerged cleanup is refused unless explicitly forced.
