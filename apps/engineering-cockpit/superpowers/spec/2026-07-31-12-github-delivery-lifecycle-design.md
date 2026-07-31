# 12 — GitHub Issue Intake, Push, Draft PR, CI, and Review Monitoring Specification

## Purpose

Define the explicit delivery path from a registered GitHub issue or verified local commit to a pushed task branch and draft pull request, then monitor GitHub checks/reviews without automatically merging or deploying.

GitHub remains authoritative for issues, remote refs, pull requests, checks, reviews, branch protection, and mergeability. The cockpit stores snapshots and normalized status for orchestration and display.

## Selected integration approach

The local WSL control plane uses the installed, authenticated GitHub CLI:

- host `git` for push/ref operations on the WSL worktree;
- `gh issue`, `gh pr`, and `gh api` with explicit JSON output for GitHub resources.

Reasons:

- `gh auth` already matches the developer's local GitHub identity;
- no long-lived personal token needs to be copied into application settings;
- GitHub Enterprise/custom-host behavior is delegated to the configured CLI;
- every command can be contract-tested against a pinned `gh` version and fake executable.

The cockpit never parses human-formatted CLI tables. The supported `gh` version range and JSON fields are pinned/tested in repository diagnostics.

## Authentication diagnostics

Before issue/delivery features are enabled, host diagnostics verify:

- `gh --version` is supported;
- `gh auth status` succeeds for the repository host;
- authenticated user can read the repository;
- remote push URL is present;
- branch push permission is checked where possible;
- Git credentials work without exposing token values;
- rate-limit status is readable.

The public result exposes host, login, scopes/capabilities only when safe, and repository permission level. It never returns the token or raw credential-helper configuration.

## Issue intake

### Preview

```text
GET /api/v1/cockpit/repositories/{repository_id}/issues/{number}
```

Fetch and normalize:

- number, title, body, state, URL;
- labels, assignees, milestone when available;
- author and created/updated timestamps;
- bounded issue comments in chronological order;
- linked PR status when detectable.

The user reviews the snapshot before task creation. Closed issues are allowed only after explicit acknowledgement.

### Snapshot

At task creation, persist an immutable `CockpitIssueSnapshot` with:

- repository/issue identity;
- fetched/updated timestamps;
- content hash;
- normalized body/comments within size limits;
- truncation markers and source URLs.

Later GitHub changes do not silently rewrite the task prompt. The UI can show “issue changed since task start” and let the user explicitly refresh/add a follow-up.

### Prompt-injection boundary

Issue bodies/comments are untrusted external text. The task context labels them as issue content, not instructions that override repository/cockpit policy. The cockpit never extracts and executes commands from issue text. Required Techletes skills and permission profile remain authoritative task configuration.

## Local commit prerequisite

Push requires a verified `CockpitDelivery` commit from subsystem 11 or an explicitly adopted existing commit that passes equivalent checks.

Preconditions:

- task branch/head matches persisted commit SHA;
- no unmerged conflicts;
- required validation is current/passed or an authorized override exists;
- by default, worktree is clean so uncommitted changes are not omitted from the PR accidentally;
- remote/base repository identity still matches registration.

## Push

Endpoint:

```text
POST /api/v1/cockpit/tasks/{task_id}/push
```

Normal first push:

```text
git -C <worktree> push --set-upstream <remote> <branch>
```

The command is an argv array executed on the WSL host. Before and after push, resolve:

- local head SHA;
- current remote branch SHA if it exists;
- configured remote URL/common repository identity.

Outcomes:

- remote absent: push expected head;
- remote equals local head: idempotent success;
- remote is ancestor and ordinary push succeeds: success;
- remote diverged/non-fast-forward: block and report;
- auth/network/ruleset rejection: safe failure with stderr tail.

No automatic force push. A separate explicit force-update command uses `--force-with-lease=<ref>:<expected-remote-sha>` and requires typed confirmation/audit. Plain `--force` is forbidden.

## Draft pull request creation

Endpoint:

```text
POST /api/v1/cockpit/tasks/{task_id}/pull-request
```

Requirements:

- branch is pushed at expected head SHA;
- base branch equals repository policy unless an authorized user explicitly chooses another allowed base;
- no existing conflicting PR for the head branch;
- title/body pass size/control-character validation;
- validation summary and commit/head metadata are current.

Default PR is draft. Body includes:

- concise user-approved summary;
- validation results with exact head SHA;
- changed-path summary;
- issue reference (`Refs #N` by default);
- explicit testing/known-risk section;
- cockpit task reference that contains no local filesystem path or secret.

Closing keywords (`Closes`, `Fixes`) are included only when the user explicitly selects them.

Use `gh pr create` with `--body-file` pointing to a user-only temporary file. Do not interpolate body into a shell command.

If a PR already exists for the branch, attach it idempotently after verifying repository, head branch, and base. Never create duplicates after an ambiguous network result without first searching.

## PR synchronization

Persist:

- PR number/URL/node ID when available;
- head/base refs and head SHA;
- draft/open/closed/merged state;
- merge state/status;
- review decision;
- check rollup;
- latest update time/content hash.

Before every state-changing delivery command, confirm the PR head SHA still matches the task branch. External pushes produce `DELIVERY_HEAD_DIVERGED` and require explicit adoption/reconciliation.

## Monitoring strategy

A local application cannot rely on public inbound webhooks. Use bounded polling while a PR is open and the backend is running.

Preferred normalized source is version-tested `gh pr view --json` fields for:

- head/base OIDs/refs;
- draft/state;
- merge state/status;
- review decision;
- status-check rollup;
- latest review/comments metadata where supported.

Use `gh api` for details not exposed by `gh pr view`, such as paginated check runs, comments, reviews, workflow jobs/logs, and rate limits.

Polling:

- initial interval around 15 seconds while checks are changing;
- exponential/backoff up to 60 seconds;
- jitter to avoid synchronization;
- pause when PR is terminal or backend is draining;
- resume on backend startup through subsystem 10;
- respect GitHub rate-limit headers/status.

GitHub status is always refreshable manually.

## Normalized delivery state

Checks:

```text
NOT_STARTED
PENDING
SUCCESS
FAILURE
CANCELLED
ACTION_REQUIRED
NEUTRAL
UNKNOWN
```

Review:

```text
NONE
REVIEW_REQUIRED
APPROVED
CHANGES_REQUESTED
```

Task reaches `READY_TO_MERGE` only when:

- PR is open and not draft (or policy explicitly treats green draft as ready-for-review only);
- persisted and remote head SHA match;
- required validation is current;
- GitHub reports required checks successful/acceptable;
- review decision satisfies repository policy;
- merge state is not conflicting/blocked.

Because branch protection details may be inaccessible, an unknown result never becomes ready. The cockpit presents GitHub's evidence and does not override rulesets.

The cockpit never invokes merge.

## CI and review details

The user may fetch:

- check/workflow names, URLs, status, conclusion, start/end times;
- bounded failed job/step logs where permissions allow;
- review summaries and requested changes;
- PR conversation comments.

Logs/comments are untrusted external content and are sanitized/bounded. They can be attached to an explicit Codex follow-up for repair after user confirmation. There is no automatic CI-fix loop in MVP.

## Draft/ready transitions

Marking a draft PR ready for review is an explicit user action and audited. Converting back to draft is also explicit where supported. Requesting reviewers is explicit. Auto-merge is never enabled.

## External changes

Detect and report:

- branch pushed by another actor;
- PR base changed;
- PR closed/merged externally;
- check suite rerun;
- review decision changed;
- issue body/comments changed;
- branch deleted.

The cockpit updates its snapshot but never rewrites local state or starts Codex automatically.

## Failure taxonomy

- `GITHUB_CLI_MISSING`
- `GITHUB_CLI_UNSUPPORTED`
- `GITHUB_AUTH_REQUIRED`
- `GITHUB_REPOSITORY_FORBIDDEN`
- `GITHUB_RATE_LIMITED`
- `GITHUB_ISSUE_NOT_FOUND`
- `GITHUB_ISSUE_TOO_LARGE`
- `DELIVERY_COMMIT_REQUIRED`
- `DELIVERY_DIRTY_WORKTREE`
- `DELIVERY_REMOTE_DIVERGED`
- `DELIVERY_PUSH_REJECTED`
- `DELIVERY_FORCE_CONFIRMATION_REQUIRED`
- `DELIVERY_PR_EXISTS_CONFLICT`
- `DELIVERY_PR_CREATE_AMBIGUOUS`
- `DELIVERY_HEAD_DIVERGED`
- `DELIVERY_STATUS_UNKNOWN`
- `DELIVERY_CHECK_LOG_FORBIDDEN`

## Security and audit

- GitHub/SSH tokens are never persisted by the cockpit.
- All commands use argv arrays and bounded output.
- PR body uses a permission-safe temporary file and is deleted after use.
- Issue/PR/comment/log content is treated as untrusted text.
- Push, force update, PR creation/update, draft transition, and reviewer request record actor, expected/local/remote SHAs, and result.
- Local paths are excluded from PR content.

## Testing strategy

Use a deterministic fake `git` remote and fake `gh` executable with scenarios for:

- auth/status/version/permissions/rate limit;
- issue open/closed/comments/pagination/update;
- first push/idempotent push/divergence/ruleset/auth failure;
- force-with-lease success/stale lease;
- PR create success/ambiguous result/existing matching/conflicting PR;
- polling pending/success/failure/cancelled/rate-limited;
- reviews approved/changes requested/unknown;
- head/base external divergence;
- failed log retrieval and sanitization;
- backend restart polling resume;
- no merge/auto-merge invocation.

A manual acceptance uses a disposable Techletes repository/issue and draft PR, not a production project.

## Acceptance criteria

- Issue content is previewed and snapshotted explicitly.
- Push is tied to an expected local/remote SHA and never force-updates silently.
- Draft PR creation is idempotent and user-approved.
- CI/review status is normalized from JSON and resumes after backend restart.
- External divergence blocks readiness rather than being overwritten.
- Failed logs/review content can support an explicit follow-up but never auto-run.
- The cockpit never merges or deploys.

## Research basis

- [GitHub CLI manual](https://cli.github.com/manual/)
- [GitHub REST API](https://docs.github.com/en/rest)
- [GitHub pull request checks](https://docs.github.com/en/pull-requests)
- [Git push](https://git-scm.com/docs/git-push)
