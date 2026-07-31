# 04 — Git Worktrees, Branches, Synchronization, Overlap, and Safe Removal Specification

## Purpose

Define how the cockpit creates and owns one isolated Git workspace per task, how it names branches within Techletes rules, how it detects divergence and overlap between concurrent tasks, and when it may safely remove a worktree.

Git remains authoritative for commits, refs, worktree registration, and working-tree status. The cockpit persists identifiers and observations but does not emulate Git state.

## Scope

This subsystem covers:

- canonical repository identity;
- fetch and base-ref resolution;
- branch and worktree creation;
- status and diff collection;
- concurrent-task overlap assessment;
- base-branch divergence and synchronization recommendations;
- worktree locking/repair/pruning diagnostics;
- guarded removal.

Push, pull-request creation, and CI are subsystem 12. Devcontainer cleanup is subsystem 14.

## Repository and worktree identity

A registered repository is identified by:

- canonical main-worktree real path;
- `git rev-parse --git-common-dir` real path;
- GitHub full name;
- remote name, normally `origin`;
- configured base branch.

A task worktree is identified by:

- task UUID;
- absolute real path under `COCKPIT_WORKTREE_ROOT`;
- branch name;
- base ref and base SHA at creation;
- Git common directory;
- current head SHA.

The cockpit parses `git worktree list --porcelain -z`; it never derives ownership from directory naming alone.

## Branch naming

Branch names must pass the existing Techletes branch validator. Allowed prefixes currently include:

```text
feature/
bug/
refactor/
security/
breaking/
question/
docs/
```

The cockpit does not introduce `chore/`, `codex/`, or `agent/` prefixes unless the shared policy changes first.

Default task-type mapping:

- feature request or ordinary issue: `feature/`
- confirmed defect: `bug/`
- structural/template synchronization: `refactor/`
- dependency vulnerability remediation: `security/`
- potentially incompatible migration: `breaking/`
- investigation without planned code delivery: `question/`
- documentation-only task: `docs/`

The slug is lowercase ASCII, hyphenated, bounded to keep the full ref below 120 characters, and ends with a six-character task-ID suffix when necessary for collision avoidance. An issue task uses the issue number near the start, for example `feature/62-remember-filters-a1b2c3`.

Branch creation is always explicit from a fetched remote base ref:

```text
refs/remotes/origin/staging
```

The cockpit never creates a task from an uncommitted local base branch.

## Worktree creation flow

1. Acquire the task lock and global worktree-operation semaphore.
2. Verify the repository and target path remain within allowed roots.
3. Run `git fetch <remote> --prune`.
4. Resolve the configured remote base ref to an immutable SHA.
5. Confirm branch and target path are unused locally and not already registered as another active cockpit workspace.
6. Create the branch/worktree with `git worktree add -b <branch> <path> <base-ref>`.
7. Parse `git worktree list --porcelain -z` and verify the new entry.
8. Persist path, branch, Git common dir, base SHA, and head SHA.
9. Transition the task to `WORKTREE_READY`.

On failure after Git creates a partial entry, the adapter inspects before cleanup. It never recursively deletes an arbitrary path.

## Status model

Use machine-readable commands:

- `git status --porcelain=v2 -z --branch`
- `git diff --binary --no-ext-diff`
- `git diff --cached --binary --no-ext-diff`
- `git ls-files --others --exclude-standard -z`
- `git rev-list --left-right --count <base>...HEAD`
- `git merge-base <base> HEAD`

The normalized status includes:

- current branch and head SHA;
- detached-head flag;
- staged, unstaged, deleted, renamed, and untracked paths;
- ahead/behind counts against the latest remote base;
- committed changed files since merge base;
- all effective task-changed files, including working-tree changes;
- submodule warnings;
- conflict/unmerged entries.

Diff payloads are bounded for API use. Full diffs are read on demand and may be stored in rotated local files, not unrestricted database JSON.

## Concurrent overlap assessment

Worktree isolation prevents filesystem interference but not semantic divergence. The cockpit computes overlap for active tasks in the same repository.

### Inputs

For each task:

- merge base with current `origin/<base>`;
- committed diff from merge base to `HEAD`;
- staged and unstaged diffs;
- untracked path list;
- rename map;
- optional parsed hunk line ranges for text patches.

### Levels

- `NONE`: no shared effective paths.
- `FILE_OVERLAP`: tasks touch one or more same paths but no overlapping hunks are detected.
- `HUNK_OVERLAP`: text hunks overlap or one task deletes/renames a path changed by another.
- `BASE_CONFLICT_RISK`: a dry merge analysis reports conflict, or the task depends on a base ref that changed incompatibly.
- `UNKNOWN`: binary/submodule/oversized diff prevents reliable assessment.

File overlap is a warning, not proof of a merge conflict. Binary, generated, lockfile, migration, route-tree, and shared configuration files receive elevated risk because small independent edits frequently conflict semantically.

## Refresh triggers

Recalculate status and overlap after:

- app-server file-change/diff events, debounced;
- validation completion;
- commit;
- base branch fetch;
- another task's PR merge observation;
- explicit user refresh.

Do not run a full diff on every token or message delta.

## Base synchronization

The cockpit reports:

- creation base SHA;
- current remote base SHA;
- ahead/behind counts;
- whether another active/merged cockpit task changed overlapping paths.

It never automatically rebase-merges a task. The user chooses a synchronization action after reviewing risk:

- merge current remote base into the task branch;
- rebase task commits onto current remote base;
- defer synchronization.

For the first release, synchronization is initiated as a dedicated task command and delegated to Codex only after Git creates a recovery point and the user approves the chosen strategy. Force push remains explicit and uses `--force-with-lease`, never `--force`.

A dry conflict probe may use a temporary index/worktree or a supported `git merge-tree` invocation, but its output is advisory and version-tested. The cockpit must not mutate the task branch merely to calculate risk.

## Worktree locking, pruning, and repair

Local worktrees normally remain registered while their directories exist. The cockpit:

- never runs global `git worktree prune` automatically;
- exposes stale administrative entries as diagnostics;
- may run `git worktree repair <path>` only through an explicit repair action;
- uses `git worktree lock --reason <task-id>` only when a task worktree must temporarily live on a path Git could otherwise consider prunable; normal local paths do not require locking;
- removes its lock before normal removal.

## Safe removal preconditions

Default cleanup is refused when any condition holds:

- staged, unstaged, unmerged, or untracked changes exist;
- commits are ahead of the remote base and not reachable from an accepted remote branch/PR;
- the branch has not been pushed when policy requires push;
- an app-server process or validation command still owns the worktree;
- the devcontainer is still being modified by another operation;
- Git reports the path as another task's worktree;
- the worktree is the primary registered repository path.

Normal removal uses `git worktree remove <path>` followed by targeted `git worktree prune --expire now` only for the removed entry if required. Branch deletion is a separate explicit decision.

Force removal requires a typed confirmation that displays the dirty paths, unpushed commits, and exact directory. It still refuses paths outside the configured worktree root.

## Path security

- Resolve parent real paths before creation.
- Reject symlink escapes.
- Create the task directory only through the adapter.
- Never pass user input as a shell command; use argument arrays and `git -C`.
- Treat filenames as bytes/zero-delimited command output; do not parse line-delimited porcelain.
- Do not assume UTF-8 filenames for safety decisions.

## Error taxonomy

- `GIT_NOT_REPOSITORY`
- `GIT_FETCH_FAILED`
- `GIT_BASE_REF_MISSING`
- `GIT_BRANCH_EXISTS`
- `GIT_WORKTREE_PATH_EXISTS`
- `GIT_WORKTREE_REGISTERED`
- `GIT_STATUS_PARSE_FAILED`
- `GIT_DETACHED_HEAD`
- `GIT_UNMERGED_STATE`
- `GIT_UNSAFE_REMOVAL`
- `GIT_REPAIR_REQUIRED`

## Testing strategy

Contract tests create a temporary bare remote and two clones/worktrees. Required scenarios:

- creation from an exact remote base SHA;
- branch-name policy and collision suffix;
- same branch cannot be checked out twice;
- spaces and unusual characters in repository paths;
- staged/unstaged/untracked/renamed/deleted/conflicted status parsing;
- two tasks touching different files, same file/different hunks, same hunk, delete-versus-edit, binary file, lockfile, and migration ordering;
- remote base advancing while a task remains active;
- safe cleanup, unpushed commits, dirty worktree, primary-worktree refusal, force confirmation, and stale registration repair;
- command failure leaves no untracked arbitrary directory deletion.

## Acceptance criteria

- Two tasks for one repository receive separate valid branches and worktrees.
- Every worktree is verified against Git's porcelain listing before persistence.
- Status and changed paths include committed and uncommitted work.
- Overlap is evidence-based and explicitly distinguishes warning from confirmed conflict risk.
- Base divergence is visible and no branch is silently rebased or merged.
- Default cleanup cannot lose uncommitted or unpushed work.
- All paths remain under configured WSL roots.

## Research basis

- [Git worktree](https://git-scm.com/docs/git-worktree)
- [Git status porcelain v2](https://git-scm.com/docs/git-status)
- [Git diff](https://git-scm.com/docs/git-diff)
- [Git merge-tree](https://git-scm.com/docs/git-merge-tree)
- [Techletes branch validator](https://github.com/TECHLETES/techletes-tooling)
