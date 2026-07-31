# 08 — Codex Authentication, `CODEX_HOME`, Techletes Skills, Instructions, and Permissions Specification

## Purpose

Define how every task devcontainer receives authenticated Codex access, discovers the approved Techletes skills, applies repository instructions, and runs under a predictable sandbox/approval profile without leaking credentials or granting delivery permissions to the model.

This subsystem configures the app-server session created in subsystem 07. It does not implement browser approval handling; subsystem 09 owns individual server requests.

## Selected authentication strategy

The MVP uses one host-controlled Codex home per developer, shared across trusted task devcontainers:

```text
WSL host:        ${HOME}/.codex
container mount: /home/<remote-user>/.codex
remote env:      CODEX_HOME=/home/<remote-user>/.codex
```

The current full-stack template already mounts host `~/.codex` to `/home/vscode/.codex`, sets `CODEX_HOME`, installs Codex CLI, and uses remote user `vscode`. Repository diagnostics require an equivalent arrangement.

Authentication is bootstrapped deliberately by the developer with the official Codex login flow before cockpit tasks start. The cockpit does not copy opaque credential files, print tokens, or log in/out independently in every task container.

## Shared-home concurrency policy

Multiple app-server processes may read/write thread/session data under the same Codex home. This is accepted only after a real concurrency test with the pinned Codex version.

Rules:

- task sessions may call read-only account/model/skills endpoints and create their own distinct threads;
- login, logout, global config mutation, plugin/skill installation, and other shared-home administrative changes are serialized by one global `CodexHomeMutationLock`;
- tasks do not edit `config.toml` directly;
- the cockpit records only home strategy/path fingerprint and non-secret account status;
- a failed concurrency test blocks the release and concurrent real tasks; it does not silently copy authentication material into per-task homes.

An isolated-home strategy is not implemented until OpenAI exposes and the project validates a safe narrow authentication handoff. No plan may invent credential filenames or copy secrets based on assumptions.

## Authentication diagnostics

Active diagnostics run inside the target devcontainer and verify:

- `CODEX_HOME` is set and absolute;
- the path exists, is owned/usable by the remote user, and is writable where thread persistence requires it;
- `codex --version` matches subsystem 07;
- app-server initializes;
- the schema-defined account-read method reports authenticated status;
- no login flow is currently pending;
- optional model listing succeeds when supported.

The public diagnostic response may include provider/account type and login-required boolean only if returned as non-secret metadata. It never includes tokens, credential paths below the home root, email unless needed/approved, or raw account responses.

A missing login is `CODEX_AUTH_REQUIRED`, not a generic app-server failure. The UI shows the exact WSL/devcontainer command required to authenticate and then offers a recheck.

## Trusted repository boundary

Mounting a writable Codex home into a devcontainer grants code running in that container access to sensitive local agent state. Therefore:

- only repositories registered under approved roots and marked trusted can run authenticated tasks;
- active diagnostics display all host credential mounts before first run;
- untrusted/external repositories default to analysis without Codex-home mount and cannot start authenticated app-server tasks;
- repository trust changes require `cockpit:manage` permission and an audit event;
- no target repository may mount the Docker socket unless separately approved.

Subsystem 14 enforces and audits this trust boundary.

## Skill discovery strategy

Techletes workflow skills are installed or synchronized into a host-controlled location visible through `CODEX_HOME` or another explicitly mounted read-only skill root. The cockpit does not assume a sibling WSL repository path is visible inside every target devcontainer.

Repository/global configuration declares **container-visible** roots, for example:

```yaml
agent:
  skill_roots:
    - ${CODEX_HOME}/skills
  required_skills:
    - techletes-superpowers:using-superpowers
```

For each new app-server process generation:

1. resolve configured roots inside the target container;
2. validate containment and readability;
3. call the current schema-defined extra-roots method (for supported versions, `skills/extraRoots/set`);
4. call `skills/list` or the current equivalent;
5. require configured skill names and capture their version/source metadata;
6. persist a sanitized skill-manifest fingerprint;
7. fail task startup if a required skill is missing or shadowed ambiguously.

Extra roots are process/session configuration and must be reapplied after every app-server restart.

Skill installation/update is an administrative workflow protected by the shared-home mutation lock and is outside a task turn.

## Skill invocation

The cockpit's initial task input names only the required workflow skill(s) and task intent. It does not paste entire skill files into the prompt.

Default first instruction for meaningful implementation work:

```text
Use techletes-superpowers:using-superpowers to select the smallest appropriate workflow, then follow the repository's AGENTS.md and the referenced subsystem specification and implementation plan.
```

When a task is executing one child plan, the task input includes exact paths to that spec/plan. Explicit user-selected workflow skills are added only when compatible with repository policy.

The app-server's version-supported skill input item/capability-root mechanism is preferred over plain prompt naming when available and schema-tested. The fallback is a clear text instruction plus successful `skills/list` verification.

## Instruction assembly and precedence

Codex itself is responsible for its native instruction-loading behavior. The cockpit does not claim to override platform/system policy.

The cockpit assembles a bounded task context from:

1. the user's task text or GitHub issue snapshot;
2. repository `.techletes/cockpit.yaml` policy;
3. paths to relevant committed spec/plan documents;
4. explicit required skill names;
5. task metadata such as branch/worktree and allowed delivery scope.

Repository `AGENTS.md` remains in the workspace for Codex's native discovery. The cockpit avoids duplicating its full contents unless diagnostics prove the installed Codex version does not load it.

Prompt assembly is deterministic and hashable. The stored task record includes the context fingerprint and source references, not secret-bearing environment data.

## Permission profiles

The cockpit defines stable product profiles and maps them to the pinned app-server schema's sandbox and approval-policy fields.

### `analysis`

- read-only sandbox;
- no file modifications;
- no Git writes;
- no delivery actions;
- network disabled unless repository policy explicitly requires read-only external research.

### `development`

- workspace-write sandbox limited to the task worktree and supported runtime paths;
- approval policy that surfaces commands outside ordinary workspace-safe operations;
- no push, PR, merge, or deployment credentials/actions delegated to Codex;
- network follows repository policy.

### `dependency_update`

- workspace-write;
- package-manager network access only when the pinned sandbox model can express/test it;
- lockfile and dependency commands allowed;
- no delivery actions.

### `diagnostic_repair`

- same workspace boundary as development;
- additional approved runtime inspection commands;
- no destructive Docker/Git cleanup without a separate cockpit action.

`danger-full-access` and unrestricted host filesystem access are not MVP profiles. Experimental app-server permission APIs are used only when included in the pinned compatibility manifest; otherwise profiles map to stable sandbox/approval fields.

## Delivery separation

Codex may create/modify/validate files and propose a commit message. The cockpit, not the agent, owns explicit commit, push, PR creation, force operations, merge, and deployment actions through subsystems 11/12/14.

The initial prompt states this boundary. GitHub credentials may be present in the devcontainer for developer convenience, but task policy instructs Codex not to use them for delivery; hard enforcement occurs by running delivery through the control-plane APIs and by permission/sandbox restrictions where supported.

## Approval reliability risk

App-server approval behavior is version-sensitive. The compatibility suite must verify that command/file-change approval requests are actually emitted for each selected policy. If a request can stall without surfacing:

- the pinned version/profile is marked unsupported;
- a watchdog reports `APPROVAL_PROTOCOL_STALLED` with evidence;
- the user can interrupt or force-stop;
- the cockpit does not silently switch to a less restrictive profile.

## Configuration model

```yaml
agent:
  protocol: app-server
  execution_profile: development
  skill_roots:
    - ${CODEX_HOME}/skills
  required_skills:
    - techletes-superpowers:using-superpowers
  model: null
  reasoning_effort: null
  network_policy: repository_default
```

Global policy can reduce permissions; repository config cannot exceed the global maximum. Task creation may choose only an allowed profile.

## Persisted non-secret metadata

- Codex-home strategy and path hash;
- remote user/home;
- authentication state and check time;
- Codex/account provider type when safe;
- skill root hashes and resolved skill names/versions;
- instruction/context fingerprint;
- permission profile and resolved sandbox/approval fingerprint;
- model/reasoning selection when returned.

## Failure taxonomy

- `CODEX_HOME_MISSING`
- `CODEX_HOME_PERMISSION_DENIED`
- `CODEX_HOME_UNTRUSTED_REPOSITORY`
- `CODEX_AUTH_REQUIRED`
- `CODEX_ACCOUNT_READ_FAILED`
- `CODEX_SHARED_HOME_CONCURRENCY_FAILED`
- `CODEX_SKILL_ROOT_MISSING`
- `CODEX_REQUIRED_SKILL_MISSING`
- `CODEX_SKILL_AMBIGUOUS`
- `CODEX_PERMISSION_PROFILE_UNSUPPORTED`
- `CODEX_APPROVAL_POLICY_UNVERIFIED`
- `CODEX_INSTRUCTION_CONTEXT_TOO_LARGE`

## Testing strategy

- template and non-template remote user/home paths;
- missing, read-only, wrong-owner, and symlinked Codex home;
- authenticated/unauthenticated account-read responses;
- two concurrent real app-server processes creating/resuming separate threads in shared home;
- serialized login/config mutation lock;
- skill roots re-applied after process restart;
- required skill present, missing, duplicate/shadowed, and unreadable;
- prompt/context fingerprint determinism and size limits;
- each permission profile's generated thread/turn params;
- attempted profile escalation blocked by global policy;
- approval-emission acceptance scenarios;
- no secret values in diagnostics, database events, or logs.

## Acceptance criteria

- A trusted target devcontainer can initialize authenticated app-server without copying secrets.
- Concurrent task sessions pass the pinned-version shared-home test.
- Required Techletes skills are discoverable and verified after every process start.
- Task context references the exact child spec/plan and workflow skill.
- Permission profiles are deterministic, version-tested, and cannot exceed global policy.
- Delivery remains outside the model-controlled task turn.
- Missing auth/skills/approval support fails before implementation work begins.

## Research basis

- [OpenAI Codex app-server README](https://github.com/openai/codex/blob/main/codex-rs/app-server/README.md)
- [Techletes Superpowers skills](https://github.com/TECHLETES/techletes-tooling/tree/main/plugins/techletes-superpowers/skills)
- [Dev Container mounts and environment](https://containers.dev/implementors/json_reference/)
- [Techletes full-stack template devcontainer](https://github.com/TECHLETES/full-stack-template/tree/main/.devcontainer)
