# 05a — Linked-Worktree Git Metadata Mount Compatibility Specification

## Purpose

Guarantee that Git, Codex, validation hooks, and commit operations work **inside** a task devcontainer created from a linked Git worktree.

A linked worktree does not contain a normal `.git/` directory. It contains a `.git` file whose `gitdir:` entry points into the primary repository's shared Git common directory, commonly through an absolute WSL path such as:

```text
/home/thom/code/project/.git/worktrees/feature-62
```

When only the worktree directory is bind-mounted into a container, that absolute target usually does not exist inside the container. Source files are visible, but `git status`, repository hooks, Codex repository inspection, staging, and commits may fail.

This subsystem resolves that incompatibility without copying Git metadata or exposing unrelated worktree source directories.

## Selected approach

Use the official Dev Container CLI's supported runtime mount mechanism to bind the canonical Git common directory into the task devcontainer at the **same absolute path** that the worktree's `.git` file references.

Conceptually:

```text
WSL source:
  /home/thom/code/project/.git

Container target:
  /home/thom/code/project/.git

Task workspace:
  /workspaces/project-feature-62
```

The exact CLI option is pinned and contract-tested against the supported Dev Container CLI version. Implementation must first inspect `devcontainer up --help` and the installed CLI source/behavior. It may use the supported additional-mount option or a documented equivalent built into that CLI version. It must not guess an undocumented flag.

If the pinned CLI cannot add the mount without changing repository files, that CLI version is unsupported for cockpit execution until a reviewed, spec-compliant override mechanism is implemented and tested for both image- and Compose-based devcontainers.

## Why the same absolute target path

The `.git` file is owned by Git and commonly stores an absolute `gitdir:` path. Rewriting it per container would mutate shared worktree metadata and create host/container disagreement. Mounting the common directory at the same absolute target lets both host Git and container Git resolve the same metadata without modifying the worktree registration.

## Metadata discovery

From the WSL host, collect using machine-safe Git commands:

- worktree top-level path;
- `.git` file real path and exact `gitdir:` target;
- `git rev-parse --git-common-dir`;
- `git rev-parse --git-path HEAD`;
- primary repository/common-dir real path;
- filesystem ownership and symlink chain.

The adapter resolves the path through the already registered canonical repository. It does not accept a browser/model-provided mount source or target.

## Mount scope

Preferred source is the repository's canonical Git common directory, normally the primary `.git` directory. It contains refs, object database, worktree administrative entries, hooks, config, index metadata, and possibly local credentials/config references.

Rules:

- mount only the Git common directory, not the entire primary checkout;
- mount read-write because task Git operations update index, refs, logs, locks, and worktree metadata;
- preserve exact source/target path;
- do not mount another repository's common directory;
- require repository trust because the target container can now alter shared Git metadata;
- never expose this mount to an untrusted repository;
- do not separately mount sibling worktree source directories;
- include the mount in runtime identity/trust fingerprints.

## Concurrency implications

Separate worktrees have separate indexes and administrative directories, but share object storage, refs, config, hooks, and reflogs. Git's lock files provide low-level safety, but higher-level operations still require coordination.

The cockpit already serializes one task's operations. This subsystem adds a **per-repository Git metadata mutation lock** for operations that can update shared refs/config/worktree administration, including:

- worktree add/remove/repair/prune;
- commit/ref update;
- fetch/push/ref synchronization;
- branch delete;
- shared config/hook changes.

Read-only status/diff operations may run concurrently when no conflicting administrative operation is active. Two independent commits on distinct task branches are permitted only after real concurrency tests prove the repository's hooks/signing configuration is safe; otherwise commits serialize per repository.

## Host and container path visibility

The container target may be outside the remote user's home and outside the normal workspace mount. Docker creates the bind target path as needed. The target's parent path must not already resolve to an incompatible file/symlink in the image.

Startup diagnostics verify:

- source and target are absolute;
- source is the registered repository common directory;
- target equals the absolute path referenced by the worktree `.git` file;
- Docker inspection shows the exact bind mount;
- remote user can traverse/read/write required metadata;
- `git -C <remote-workspace> rev-parse --is-inside-work-tree` succeeds;
- `git rev-parse --git-common-dir` resolves to the expected target;
- `git status --porcelain=v2 -z --branch` succeeds;
- current branch/head match host observations;
- a harmless lock/write test does not mutate user commits or configuration.

## Remote-user permissions

The current template runs as `vscode`, while WSL files may be owned by the WSL user with a different numeric UID. Docker Desktop's WSL bind-mount behavior normally preserves access through the integration layer, but this must be tested rather than assumed.

If the remote user cannot operate the common directory:

- do not run the container as root as a silent workaround;
- do not recursively chown the host repository;
- report `GIT_METADATA_MOUNT_PERMISSION_DENIED` with safe UID/path evidence;
- onboarding must align remote UID/user or document a supported host permission strategy.

## Git hooks and signing

The common directory may reference hooks, include files, signing programs, and credential helpers that exist only on the host. Git working inside the container must be tested for:

- `core.hooksPath` path visibility;
- pre-commit hooks and their tools;
- SSH/GPG/1Password signing configuration;
- credential helper/SSH agent behavior;
- relative and absolute include paths.

The cockpit does not bypass hooks/signing. Missing container-visible dependencies produce diagnostics and block commit/delivery until fixed.

## Security risks

A trusted task container with read-write Git metadata access can:

- alter any ref in the repository;
- modify Git config/hooks;
- inspect object history from other branches;
- interfere with other worktree administration.

Mitigations:

- explicit repository trust and reviewed devcontainer fingerprint;
- Codex sandbox remains limited to task workspace and should not receive unrestricted access to the mount where the pinned sandbox can enforce that;
- trusted control-plane commands perform staging/commit/delivery;
- per-repository mutation lock;
- before/after ref/config/worktree-administration snapshots;
- audit unexpected changes;
- recovery/cleanup never follows arbitrary paths from modified `.git` files without revalidating canonical identity.

A sandbox that cannot prevent model access to the mount is documented as a residual risk. The product does not claim that a devcontainer is a security boundary against a malicious trusted repository.

## Drift and tampering

Before every consequential Git operation inside the container, re-read and verify:

- worktree `.git` file target;
- common-dir canonical path;
- container mount identity;
- task branch/head;
- repository trust fingerprint.

If the `.git` file or mount target changes unexpectedly, stop with `GIT_METADATA_IDENTITY_MISMATCH` and require recovery. Do not follow the new path automatically.

## Cleanup behavior

The common-directory bind mount is removed only by stopping/removing the exact task container. The source directory is never deleted by runtime cleanup.

Worktree cleanup order:

1. stop/close app-server and validation processes;
2. stop exact task container so no Git process holds locks;
3. revalidate host worktree/common-dir identity;
4. run guarded `git worktree remove` from the host;
5. remove container/runtime metadata;
6. preserve common directory and all other worktrees.

## Failure taxonomy

- `GIT_METADATA_MOUNT_UNSUPPORTED`
- `GIT_METADATA_SOURCE_INVALID`
- `GIT_METADATA_TARGET_MISMATCH`
- `GIT_METADATA_MOUNT_MISSING`
- `GIT_METADATA_MOUNT_PERMISSION_DENIED`
- `GIT_METADATA_CONTAINER_GIT_FAILED`
- `GIT_METADATA_IDENTITY_MISMATCH`
- `GIT_METADATA_SHARED_MUTATION_DETECTED`
- `GIT_HOOK_PATH_UNAVAILABLE`
- `GIT_SIGNING_UNAVAILABLE`

## Testing strategy

### Contract tests

- parse relative and absolute `.git` `gitdir:` entries;
- canonical common-dir discovery;
- supported CLI mount option and argv shape;
- Docker inspection exact source/target/read-write mount;
- missing/wrong/duplicate mount;
- symlink/source escape and repository mismatch;
- remote user permission failure;
- `.git` tampering after container start.

### Real linked-worktree tests

For a disposable full-stack-template clone:

1. create two linked worktrees;
2. start two devcontainers with the additional common-dir mount;
3. run Git status/diff/log in both;
4. modify/stage distinct files in both;
5. run hooks and create distinct commits concurrently or under the selected repository lock policy;
6. verify separate branches/indexes and shared objects remain correct;
7. stop/remove one task container/worktree and prove the other remains healthy;
8. test signing or record its supported limitation/remediation.

### Adversarial tests

- malicious worktree `.git` target outside registered common dir;
- target path occupied by symlink/file in image;
- container attempts shared ref/config mutation;
- lock contention and stale Git lock file;
- cleanup while Git process is active;
- unrelated repository common-dir mount is never accepted.

## Acceptance criteria

- Git works inside every linked-worktree devcontainer.
- The mount source is the verified canonical common directory and target is the exact worktree reference path.
- No source checkout other than the task worktree is mounted.
- Remote-user, hooks, and signing behavior are verified or block delivery with actionable diagnostics.
- Shared Git metadata mutations are coordinated and audited.
- Stopping/removing one task cannot delete or corrupt another worktree or the repository common directory.

## Research basis

- [Git worktree](https://git-scm.com/docs/git-worktree)
- [Git repository layout](https://git-scm.com/docs/gitrepository-layout)
- [Dev Container CLI](https://github.com/devcontainers/cli)
- [Development Container JSON reference](https://containers.dev/implementors/json_reference/)
- [Docker bind mounts](https://docs.docker.com/engine/storage/bind-mounts/)
