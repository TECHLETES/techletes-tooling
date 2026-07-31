# 02 — Repository Registry, Configuration, Diagnostics, and Instruction Discovery Specification

## Purpose

Define how the cockpit discovers, validates, stores, and prepares local repositories before any task is allowed to run. Repository onboarding is a security and correctness boundary: a malformed path, wrong base branch, missing devcontainer, stale credentials, or undiscovered instructions must fail before a worktree or agent process is created.

## Scope

This subsystem owns:

- allowed filesystem roots;
- repository identity and GitHub remote resolution;
- versioned `.techletes/cockpit.yaml` parsing;
- effective configuration merging;
- static and active readiness diagnostics;
- discovery of `AGENTS.md`, Techletes skill roots, and task presets;
- repository registration/list/detail/disable APIs.

It does not create worktrees, start devcontainers, start Codex, or fetch GitHub issues. Those actions belong to later subsystems.

## Repository identity

A repository is identified by both:

1. canonical main-worktree path (`Path.resolve()`); and
2. Git common directory returned by `git rev-parse --git-common-dir`.

This prevents the same clone from being registered multiple times through symlinks or linked worktrees. Registration accepts a primary clone or main worktree, not a task-created linked worktree.

Required stored fields:

```text
id UUID
name
local_path canonical absolute path
git_common_dir canonical absolute path
github_full_name owner/repository
default_base_branch
devcontainer_config_path relative path
configuration_version
enabled
last_diagnostics_status
last_diagnosed_at
created_by / created_at / updated_at
```

`github_full_name` is derived from an explicit config value or an `origin` URL. Supported GitHub.com URL forms include HTTPS and SSH. Non-GitHub remotes are rejected in the MVP because issue and pull-request delivery requires GitHub.

## Filesystem policy

Global configuration provides one or more allowed absolute WSL roots, for example:

```text
/home/thom/code/techletes
/home/thom/worktrees
```

Registration rules:

- resolve symlinks before comparison;
- require the repository path to be below an allowed repository root;
- reject `/mnt/c` by default, with a deliberate opt-in override only for diagnostics/testing;
- reject paths containing NUL, newline, or control characters;
- never construct shell command strings from paths;
- reject a path that is itself a linked task worktree;
- require the path to be readable and writable by the cockpit user;
- do not follow repository-controlled symlinks when reading configuration files outside the repository root.

## Configuration layers

Effective repository configuration is merged in this order, lowest precedence first:

1. application defaults;
2. global user configuration;
3. repository `.techletes/cockpit.yaml`;
4. explicit task overrides allowed by policy.

Unknown fields are errors. Configuration is versioned and parsed with strict Pydantic models.

### Repository configuration schema v1

```yaml
version: 1

repository:
  github: TECHLETES/example
  base_branch: staging

worktree:
  root: /home/thom/worktrees
  branch_prefixes:
    feature: feature
    bug: bug
    refactor: refactor
    security: security
    docs: docs

runtime:
  devcontainer_config: .devcontainer/devcontainer.json
  require_lockfile: false
  keep_container_on_stop: true
  startup_timeout_seconds: 900

agent:
  required_skills:
    - techletes-superpowers:using-superpowers
  extra_skill_roots: []
  default_sandbox: workspace-write
  default_approval_policy: on-request
  max_turn_minutes: 90

validation:
  commands:
    - name: lock
      command: ["uv", "lock", "--check"]
      cwd: "."
      required: true
    - name: pre-commit
      command: ["pre-commit", "run", "--all-files"]
      cwd: "."
      required: true

delivery:
  create_draft_pr: true
  merge_enabled: false
  target_branch: staging

presets:
  implement-issue:
    execution_profile: standard-development
    required_skills:
      - techletes-superpowers:using-superpowers
      - techletes-superpowers:test-driven-development
```

Commands are arrays, not shell strings. Relative `cwd` values are resolved under the task worktree and cannot escape it.

The configuration parser must distinguish absent values from explicit values. It must produce a normalized effective configuration and a provenance map showing which layer supplied each setting.

## Global configuration

Global non-secret configuration lives under the WSL user configuration directory, for example:

```text
~/.config/techletes-cockpit/config.toml
```

Environment variables may override deployment-level values. Secrets remain in environment variables, 1Password execution context, GitHub CLI storage, Codex storage, or existing template mechanisms; they are never copied into repository config.

## Instruction discovery

Before a task starts, the cockpit builds an `InstructionManifest` containing references, hashes, and precedence—not an uncontrolled concatenation of every file.

Discover:

- root `AGENTS.md`;
- any repository-specific instruction paths declared by config;
- `.techletes/cockpit.yaml`;
- relevant `README.md` and architecture references declared by config;
- available Codex skills reported later by app-server `skills/list`;
- configured extra skill roots, including the Techletes plugin source when mounted into the target devcontainer;
- task preset and GitHub issue content when applicable.

The manifest stores:

```text
relative path
content SHA-256
kind
precedence
required/optional
validation errors
```

The cockpit does not duplicate Codex's own AGENTS discovery semantics. It verifies important files exist and supplies explicit skill input items where required. Codex app-server remains responsible for loading the actual skill instructions from their paths.

## Diagnostics model

Diagnostics are structured checks with stable codes:

```text
code
category
status: pass | warning | fail | unknown
summary
details (sanitized)
remediation
checked_at
duration_ms
```

### Static diagnostics

Run without creating a container:

- path is canonical and inside allowed roots;
- path is a Git worktree and represents the main registered clone;
- no unsupported Git repository state blocks task creation;
- `origin` resolves to expected GitHub repository;
- configured base branch exists remotely after `git fetch --prune` when the user requests a refreshed check;
- devcontainer config exists and parses through `devcontainer read-configuration`;
- required repository instruction/config files exist;
- configured worktree root is writable and outside the source repository;
- branch prefix values satisfy Techletes naming rules;
- host binaries exist and meet minimum versions: Git, GitHub CLI, Docker, Dev Container CLI, Codex;
- Docker daemon is reachable;
- GitHub CLI authentication is available for the repository.

### Active readiness diagnostics

Explicitly requested because they may start or mutate runtime state:

- `devcontainer up` succeeds for the source repository;
- `devcontainer exec ... codex --version` succeeds;
- `codex app-server generate-json-schema` succeeds;
- app-server initializes and `account/read` reports an authenticated account;
- configured skill roots are visible in the container;
- the target container user can read/write the workspace and `CODEX_HOME`;
- a no-op command can be executed through the same adapter path used by tasks.

Registration runs static diagnostics only. Active diagnostics require a separate user action.

## Version compatibility

Persist detected versions and compare them against a tested compatibility policy. A diagnostic can be:

- fail: below required minimum or missing required command;
- warning: newer untested major/minor with potentially changed schema;
- pass: inside tested range;
- unknown: command did not expose machine-readable version.

The supported Codex version is especially important because generated app-server schemas are version-specific.

## API

```text
GET    /api/v1/cockpit/repositories
POST   /api/v1/cockpit/repositories
GET    /api/v1/cockpit/repositories/{repository_id}
PATCH  /api/v1/cockpit/repositories/{repository_id}
POST   /api/v1/cockpit/repositories/{repository_id}/diagnostics/static
POST   /api/v1/cockpit/repositories/{repository_id}/diagnostics/active
GET    /api/v1/cockpit/repositories/{repository_id}/configuration
GET    /api/v1/cockpit/repositories/{repository_id}/instructions
DELETE /api/v1/cockpit/repositories/{repository_id}
```

Delete is soft-disable while tasks/history exist. Physical deletion is an operations action covered later.

All routes require the cockpit management permission defined in the security subsystem.

## Error behavior

Errors are typed and actionable:

- `path_not_allowed`;
- `not_git_repository`;
- `linked_worktree_cannot_be_registered`;
- `duplicate_repository`;
- `github_remote_missing`;
- `base_branch_missing`;
- `devcontainer_config_invalid`;
- `configuration_version_unsupported`;
- `configuration_field_unknown`;
- `required_instruction_missing`;
- `binary_missing`;
- `version_unsupported`;
- `github_auth_unavailable`;
- `docker_unavailable`.

Do not return raw command output, environment variables, or credential paths in public API details.

## Risks and mitigations

### Diagnostics that change state

Mitigation: separate static and active diagnostics. UI must label active diagnostics as starting the repository devcontainer.

### Config-driven command injection

Mitigation: command arrays, no `shell=True`, path containment checks, restricted task overrides, and user-visible effective configuration.

### Stale repository identity

Mitigation: revalidate common Git directory, origin, and canonical path before each task start. If identity changed, block execution until the record is reviewed.

### Skill path mismatch between WSL and container

Mitigation: store both host and expected container paths, validate them during active diagnostics, and use app-server `skills/list` rather than assuming discovery succeeded.

### Expensive repeated checks

Mitigation: cache diagnostic results with timestamps, but rerun critical identity checks at task start.

## Testing strategy

- Unit tests for URL parsing, path containment, strict config parsing, merge/provenance, branch-prefix rules, and sanitized diagnostics.
- Contract tests with temporary Git repositories, symlinks, linked worktrees, fake `gh`, fake `docker`, fake `devcontainer`, and fake `codex` binaries.
- API tests for create/list/detail/disable and static-vs-active behavior.
- Security tests for traversal, symlink escape, malformed remote, unsupported config version, and command arrays containing control characters.
- A real-repository acceptance test against a clean clone of `TECHLETES/full-stack-template`.

## Acceptance criteria

- A valid Techletes repository can be registered without starting its container.
- Duplicate paths, linked worktrees, disallowed roots, invalid configs, and missing GitHub identity are rejected.
- Effective configuration and provenance are visible without exposing secrets.
- Static diagnostics are deterministic and non-mutating.
- Active diagnostics prove the actual devcontainer, Codex, app-server, auth, and skill environment.
- Instruction manifests are stable, hashed, and used by later task creation.
