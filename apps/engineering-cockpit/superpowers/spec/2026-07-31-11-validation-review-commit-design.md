# 11 — Validation, Quality Gates, Change Review, and Explicit Commit Preparation Specification

## Purpose

Define how the cockpit validates task changes inside the same devcontainer used by Codex, presents a trustworthy Git review, and creates a local commit only after explicit user confirmation and fresh-state checks.

This subsystem stops at a verified local commit. Push, pull request, CI, and review monitoring are subsystem 12.

## Critical Git-in-devcontainer prerequisite

A linked Git worktree contains a `.git` file that points to the main repository's Git common directory, normally an absolute WSL path outside the worktree. Mounting only the worktree at `/workspaces/app` is insufficient for Git commands inside the container.

Subsystem 05 must start task devcontainers with an additional bind mount:

```text
source=<canonical git common directory>
target=<the same absolute path inside the container>
type=bind
```

The pinned Dev Container CLI must support the additional mount option, and startup verifies inside the container:

```bash
git -C <remote-workspace-folder> rev-parse --git-common-dir
git -C <remote-workspace-folder> status --porcelain=v2 -z
```

This mount exposes shared repository metadata to a trusted task container. It does not mount other worktree source directories. The model's sandbox should remain workspace-limited; trusted control-plane `devcontainer exec` commands may write Git metadata for staging/commit. Untrusted repositories cannot receive the credential/Git-metadata mount.

## Validation source of truth

Validation commands come from versioned repository configuration, never directly from the model prompt or browser free text.

```yaml
validation:
  profiles:
    quick:
      steps: [...]
    full:
      steps: [...]
    delivery:
      steps: [...]
```

Repository onboarding may generate a reviewed default from the template's actual scripts. It must not assume stale paths. For the current full-stack template, expected candidates include:

- backend test/lint scripts under `backend/scripts/`;
- frontend `bun run lint`, `bun run typecheck`, and Playwright commands;
- lock checks and pre-commit hooks;
- generated API client/i18n checks when relevant.

The resolved profile and configuration hash are snapshotted on every run.

## Validation step model

```yaml
- id: backend-tests
  argv: ["bash", "scripts/test.sh"]
  cwd: backend
  required: true
  mutates_workspace: false
  timeout_seconds: 900
  retries: 0
  artifacts:
    - backend/coverage.xml
```

Fields:

- stable step ID and display name;
- argv array or reviewed repository script reference;
- relative working directory under worktree;
- required/optional;
- mutates-workspace flag;
- timeout;
- retry count limited by policy;
- environment variable **names** allowed from the inherited container environment;
- artifact paths under worktree;
- continue-on-failure only for optional informational checks.

Arbitrary shell text is disabled by default. A shell step is allowed only when committed in trusted repository config, explicitly marked, and executed through a fixed shell with no browser/model interpolation.

## Preconditions

Validation starts only when:

- task has a worktree and healthy verified devcontainer;
- no active turn or pending server request exists;
- task lock is held;
- current Git status/head is captured;
- selected profile is allowed;
- no cleanup/rebuild/synchronization operation is active.

The cockpit transitions to `VALIDATING` and records the profile/config/status fingerprints.

## Execution

Steps run sequentially through trusted `devcontainer exec` processes. Each step receives:

- verified remote workspace/cwd;
- inherited container environment plus an allowlisted override map;
- no prompt-provided executable or arguments;
- bounded stdout/stderr capture and rotated full diagnostic log;
- process timeout and cancellation handling.

Required step failure stops later required steps by default. Optional steps may continue. Retry is manual unless the config explicitly allows a bounded automatic retry for known transient checks.

## Workspace mutation

Some template commands format or regenerate files. A step marked `mutates_workspace: true` may modify the worktree.

Rules:

- capture Git status/hash before and after every mutating step;
- emit changed-path events;
- run a later non-mutating check for the generated/formatted output;
- fail the run if an unmarked step mutates the worktree;
- never discard changes produced by validation.

No app-server turn runs concurrently, so changes cannot race the agent.

## Result model

A validation run records:

- task/profile/config hash;
- head SHA and worktree-status hash at start/end;
- step order and attempts;
- argv identifier and cwd, not secret environment values;
- timestamps, duration, exit code, timeout/cancel state;
- bounded sanitized output tails and diagnostic log ID;
- artifact metadata/hash where configured;
- changed paths;
- aggregate `passed`, `failed`, `cancelled`, or `stale` result.

If files/head change from another source during a supposedly non-mutating run, mark it `stale` and require rerun.

After completion, the task returns to `READY_FOR_REVIEW` so the user can inspect/fix changes. The latest quality-gate status is a separate derived field. Delivery is blocked while required validation status is not `passed`, unless a `cockpit:manage` user records an explicit override with reason. No failed validation is hidden behind a successful-looking state.

## Change review

REST review endpoints expose:

- current head/base/merge-base;
- staged/unstaged/untracked/conflicted status;
- diff statistics and changed paths;
- bounded unified patch per file/on demand;
- binary/oversized/generated-file markers;
- latest validation result and head/status fingerprint;
- app-server final-message reference and deterministic activity summary.

The server reads paths from Git's effective changed set and verifies requested paths; browser input cannot read arbitrary files.

Diff rendering is plain text with escaped content. ANSI and HTML are not interpreted. Secrets redaction is applied to logs, but source diff redaction must not silently change the review; instead sensitive-pattern detection warns and blocks delivery pending review.

## Validation versus review freshness

A validation result is current only when:

- current head SHA equals the run's end head SHA;
- current worktree-status hash equals the run's end status hash;
- profile/config hash is unchanged.

Any subsequent edit, staging change, commit, synchronization, or config change makes it stale.

## Commit preparation

Commit is an explicit user action and requires:

- no active turn/request/validation;
- current review snapshot hash supplied by browser and matching server state;
- no unmerged conflicts;
- selected files are exactly current changed paths;
- required delivery validation current and passed, or authorized override;
- commit message supplied/approved by user;
- task branch checked out and head unchanged.

### Staging

The user may select all task changes or an explicit subset. The server passes selected NUL-safe paths after validating them against current status. It does not use `git add .` implicitly.

### Commit execution

Run Git through a trusted control-plane command inside the task devcontainer so repository hooks and project tooling execute in the intended environment. The Git common-directory mount makes this possible.

```text
git -C <remote-workspace> add -- <exact paths>
git -C <remote-workspace> commit -m <message>
```

Use argv arrays. Do not pass `--no-verify`, disable signing, or bypass hooks. Respect repository/user signing configuration; if signing cannot complete headlessly, fail with actionable diagnostics.

After commit, verify:

- new head differs and parent contains expected previous head;
- commit message/author metadata are safe to display;
- committed paths match staged review;
- worktree status is refreshed;
- validation becomes stale unless the exact committed tree equals the validated status and policy accepts carry-forward.

MVP may conservatively require a short delivery validation after commit.

## Commit message

Codex may propose a message, but the browser user approves/edits it. Validation includes:

- non-empty subject;
- no control characters;
- configured length policy;
- optional conventional-commit policy;
- no automatically inserted secrets or issue-closing keywords unless user selected them.

## Cancellation

Validation cancellation terminates the current owned process with graceful/force sequence, records partial results, refreshes Git status, and returns task to review. It does not delete generated changes.

## Failure taxonomy

- `VALIDATION_PROFILE_MISSING`
- `VALIDATION_CONFIG_INVALID`
- `VALIDATION_COMMAND_NOT_ALLOWED`
- `VALIDATION_STEP_FAILED`
- `VALIDATION_STEP_TIMEOUT`
- `VALIDATION_CANCELLED`
- `VALIDATION_UNEXPECTED_MUTATION`
- `VALIDATION_STALE`
- `REVIEW_SNAPSHOT_STALE`
- `REVIEW_PATH_INVALID`
- `SENSITIVE_CHANGE_DETECTED`
- `COMMIT_VALIDATION_REQUIRED`
- `COMMIT_CONFLICTED_WORKTREE`
- `COMMIT_STAGE_FAILED`
- `COMMIT_HOOK_FAILED`
- `COMMIT_SIGNING_FAILED`
- `COMMIT_HEAD_CHANGED`

## Testing strategy

- strict config parsing, argv/cwd containment, shell rejection;
- sequential required/optional steps, timeout, retry, cancel;
- stdout/stderr bounds and artifact containment;
- marked/unmarked workspace mutation;
- stale result after file/head/config change;
- review path traversal, binary/oversized diff, generated files, ANSI/HTML;
- sensitive-pattern warning without diff alteration;
- stage all/subset, stale review hash, conflict, hook failure, signing failure;
- exact commit path/head verification;
- Git inside a linked-worktree devcontainer with the additional common-dir mount;
- no `--no-verify` or implicit `git add .`.

## Acceptance criteria

- Validation runs only configured commands inside the task devcontainer.
- Results are durable, bounded, and tied to an exact Git/config snapshot.
- Unexpected mutation/staleness is visible.
- Review endpoints cannot read outside changed paths.
- A commit requires current review and passed gates/explicit override.
- Staging uses exact selected paths and hooks/signing are respected.
- Git works inside the devcontainer because the common directory is mounted and verified.

## Research basis

- [Git worktree](https://git-scm.com/docs/git-worktree)
- [Git status porcelain](https://git-scm.com/docs/git-status)
- [Pre-commit](https://pre-commit.com/)
- [Techletes full-stack template development commands](https://github.com/TECHLETES/full-stack-template)
- [Dev Container CLI mounts](https://github.com/devcontainers/cli)
