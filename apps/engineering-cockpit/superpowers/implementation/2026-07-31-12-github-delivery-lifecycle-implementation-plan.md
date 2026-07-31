# 12 — GitHub Issue Intake, Push, Draft PR, CI, and Review Monitoring Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `techletes-superpowers:subagent-driven-development` or `techletes-superpowers:executing-plans`. Subsystems 02–04, 10, and 11 are prerequisites.

**Goal:** Add explicit GitHub issue intake, SHA-safe branch push, idempotent draft PR creation, and durable CI/review monitoring without automatic merge or repair.

**Architecture:** Use host Git for refs/push and a pinned GitHub CLI for authenticated JSON/API operations. Persist immutable issue snapshots and normalized delivery status. Poll open PRs with bounded backoff and resume monitoring through subsystem 10 recovery.

**Tech stack:** Git, pinned `gh`, asyncio command runner, SQLModel/PostgreSQL, FastAPI, Redis/event broker, Pytest fake executable.

## Global constraints

- Never store GitHub tokens.
- Never parse human table output.
- Push/force/PR actions are explicit, versioned, idempotent, and audited.
- Normal push is fast-forward only; force uses exact `--force-with-lease` and separate confirmation.
- PRs are draft by default; no merge, auto-merge, or deployment code.
- Issue/PR/check/review content is untrusted text.

---

### Task 1: Pin and diagnose GitHub CLI behavior

**Files:**
- Modify: `apps/engineering-cockpit/.devcontainer/Dockerfile` or host setup script as appropriate
- Create: `apps/engineering-cockpit/backend/cockpit/github/version.py`
- Create: `apps/engineering-cockpit/backend/cockpit/github/diagnostics.py`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/github/test_diagnostics.py`

**Interfaces:**

```python
@dataclass(frozen=True)
class GitHubCliDiagnostics:
    version: str
    supported: bool
    host: str | None
    login: str | None
    authenticated: bool
    repository_readable: bool
    push_capability: str
    rate_limit_remaining: int | None
```

- [ ] Select a tested `gh` version range and record exact JSON fields/commands used by later tasks.
- [ ] Run `gh auth status` and safe `gh api`/repository checks without echoing tokens.
- [ ] Test missing/unsupported CLI, unauthenticated, wrong host, forbidden repository, read-only, rate-limited, and success.
- [ ] Add to repository active diagnostics.
- [ ] Commit: `build: pin github cli compatibility`.

### Task 2: Build a deterministic fake GitHub CLI

**Files:**
- Create: `apps/engineering-cockpit/backend/tests/cockpit/fakes/fake_gh.py`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/fakes/scenarios/github/*.json`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/github/test_fake_gh.py`

- [ ] Support exact commands used for issue view/comments, PR create/view/edit/ready, API pagination, check runs, reviews/comments, logs, auth, and rate limits.
- [ ] Validate argv shape and emit deterministic JSON/stdout/stderr/exit codes.
- [ ] Include ambiguous PR-create behavior where the operation succeeds remotely but the process exits with a transport error.
- [ ] Keep the fake independent of GitHub credentials/network.
- [ ] Commit: `test: add fake github cli`.

### Task 3: Add issue snapshot persistence

**Files:**
- Modify: `apps/engineering-cockpit/backend/models.py`
- Create: `apps/engineering-cockpit/backend/cockpit/github/issues.py`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/github/test_issues.py`
- Add migration for: `CockpitIssueSnapshot` and bounded comment rows/JSON as selected.

**Interfaces:**

```python
@dataclass(frozen=True)
class GitHubIssueSnapshotData:
    repository: str
    number: int
    title: str
    body: str
    state: str
    url: str
    labels: tuple[str, ...]
    comments: tuple[GitHubIssueComment, ...]
    content_hash: str
    truncated: bool
    updated_at: datetime
```

- [ ] Fetch issue JSON and paginated comments with exact repository/number.
- [ ] Normalize/bound text, labels, comments, and timestamps; retain source URLs/truncation markers.
- [ ] Treat external content as data in the task context.
- [ ] Test open/closed/not found/forbidden, pagination, oversized body/comments, invalid Unicode, update hash, and linked PR metadata.
- [ ] Commit: `feat: snapshot github issues`.

### Task 4: Add issue preview and task-creation integration

**Files:**
- Create: `apps/engineering-cockpit/backend/api/routes/cockpit_github_issues.py`
- Modify: `apps/engineering-cockpit/backend/api/main.py`
- Modify: `apps/engineering-cockpit/backend/cockpit/tasks/service.py`
- Create: `apps/engineering-cockpit/backend/tests/api/routes/test_cockpit_github_issues.py`

**Endpoint:**

```text
GET /api/v1/cockpit/repositories/{repository_id}/issues/{number}
```

- [ ] Require repository access and GitHub diagnostics.
- [ ] Preview safe public snapshot without creating a task.
- [ ] On issue-based task creation, require user-confirmed snapshot hash, persist immutable snapshot, derive branch name through subsystem 04, and reference snapshot in subsystem 08 context.
- [ ] Require explicit acknowledgement for closed issue.
- [ ] Add “source changed” check comparing current GitHub updated/content hash without rewriting the task.
- [ ] Commit: `feat: create cockpit tasks from github issues`.

### Task 5: Implement remote-ref inspection and normal push

**Files:**
- Create: `apps/engineering-cockpit/backend/cockpit/github/push.py`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/github/test_push.py`

**Interfaces:**

```python
@dataclass(frozen=True)
class RemoteBranchState:
    exists: bool
    sha: str | None

class PushService:
    async def push(
        self,
        *,
        task_id: UUID,
        expected_local_sha: str,
        expected_remote_sha: str | None,
    ) -> PushResult: ...
```

- [ ] Resolve local head and remote ref with machine-safe Git commands.
- [ ] Require verified local commit, current validation/policy, branch identity, and clean worktree by default.
- [ ] Persist push intent including expected SHAs, run `git push --set-upstream <remote> <branch>`, then resolve remote SHA.
- [ ] Treat same remote/local SHA as idempotent success.
- [ ] Test absent remote, idempotent, fast-forward, divergent/non-fast-forward, auth/network/ruleset rejection, local-head race, dirty worktree, and ambiguous process result.
- [ ] Never add force flags in this method.
- [ ] Commit: `feat: push verified cockpit branches`.

### Task 6: Implement explicit force-with-lease update

**Files:**
- Modify: `apps/engineering-cockpit/backend/cockpit/github/push.py`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/github/test_force_push.py`

- [ ] Add a separate method/API command requiring `cockpit:manage` or allowed owner permission, expected remote SHA, task/repository/branch typed confirmation, and idempotency key.
- [ ] Execute only:

```text
git push --force-with-lease=<remote-branch-ref>:<expected-remote-sha> <remote> <local-branch>:<remote-branch>
```

- [ ] Reject missing expected SHA and never use plain `--force`.
- [ ] Test success, stale lease, wrong confirmation, remote deleted/changed, auth failure, and repeated idempotent request.
- [ ] Audit actor/old/new SHAs.
- [ ] Commit: `feat: guard cockpit force updates`.

### Task 7: Add PR content validation and builder

**Files:**
- Create: `apps/engineering-cockpit/backend/cockpit/github/pull_request_content.py`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/github/test_pull_request_content.py`

**Interfaces:**

```python
@dataclass(frozen=True)
class PullRequestDraft:
    title: str
    body: str
    base_branch: str
    head_branch: str
    head_sha: str
```

- [ ] Build default body from user-approved summary, validation evidence, changed paths, issue reference, testing, known risks, and opaque cockpit task ID.
- [ ] Exclude local filesystem paths, environment values, raw logs, and credentials.
- [ ] Default issue link is `Refs #N`; closing keyword requires explicit user choice.
- [ ] Validate title/body/control chars/size and allowed base branch.
- [ ] Test injection, Unicode, empty summary, oversized paths, sensitive local path, and closing keyword choice.
- [ ] Commit: `feat: prepare cockpit pull request content`.

### Task 8: Implement idempotent draft PR creation

**Files:**
- Create: `apps/engineering-cockpit/backend/cockpit/github/pull_requests.py`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/github/test_pull_requests.py`

**Interfaces:**

```python
class PullRequestService:
    async def create_or_attach_draft(
        self,
        *,
        task_id: UUID,
        draft: PullRequestDraft,
    ) -> CockpitDeliveryPublic: ...
```

- [ ] Verify remote head/base/repository and required validation immediately before create.
- [ ] Search for existing open/closed PR by exact head branch before creation.
- [ ] Write body to a user-only temporary file; execute `gh pr create --draft ... --body-file <file>` as argv; securely delete file.
- [ ] On ambiguous failure, search again and attach only an exact matching PR.
- [ ] Verify returned/fetched PR head SHA/base and persist number/URL/node ID/state.
- [ ] Test success, existing exact, existing conflicting base/head, ambiguous remote success, validation stale, head divergence, and temp-file cleanup.
- [ ] Commit: `feat: create idempotent draft pull requests`.

### Task 9: Add delivery API routes

**Files:**
- Create: `apps/engineering-cockpit/backend/api/routes/cockpit_delivery.py`
- Modify: `apps/engineering-cockpit/backend/api/main.py`
- Create: `apps/engineering-cockpit/backend/tests/api/routes/test_cockpit_delivery.py`

**Endpoints:**

```text
POST /api/v1/cockpit/tasks/{id}/push
POST /api/v1/cockpit/tasks/{id}/force-update
POST /api/v1/cockpit/tasks/{id}/pull-request
POST /api/v1/cockpit/tasks/{id}/pull-request/ready
POST /api/v1/cockpit/tasks/{id}/pull-request/draft
GET  /api/v1/cockpit/tasks/{id}/delivery
POST /api/v1/cockpit/tasks/{id}/delivery/refresh
```

- [ ] Apply owner/RBAC, task locks, expected versions/SHAs, idempotency keys, and audit events.
- [ ] PR ready/draft transitions are explicit and verify current head.
- [ ] No merge/auto-merge endpoint exists.
- [ ] Test unauthorized, stale task/head, duplicate tab, and each success/error mapping.
- [ ] Commit: `feat: expose cockpit github delivery controls`.

### Task 10: Normalize PR, check, and review status

**Files:**
- Create: `apps/engineering-cockpit/backend/cockpit/github/status.py`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/github/test_status.py`

**Interfaces:**

```python
@dataclass(frozen=True)
class PullRequestStatusSnapshot:
    number: int
    state: str
    draft: bool
    head_sha: str
    base_branch: str
    merge_state: str
    checks: CheckAggregate
    review: ReviewAggregate
    updated_at: datetime
```

- [ ] Parse version-tested `gh pr view --json` fields and use `gh api` pagination for missing details.
- [ ] Normalize all check/review enum values including unknown/new values.
- [ ] Determine readiness only when head/validation/check/review/merge evidence is conclusive.
- [ ] Test pending/success/failure/cancelled/action-required/neutral/unknown, approved/changes-requested/required/none, conflicts, draft, externally closed/merged, and head/base divergence.
- [ ] Never infer required-check success from absence of check data.
- [ ] Commit: `feat: normalize github delivery status`.

### Task 11: Implement bounded PR monitoring

**Files:**
- Create: `apps/engineering-cockpit/backend/cockpit/github/monitor.py`
- Modify: `apps/engineering-cockpit/backend/cockpit/runtime/context.py`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/github/test_monitor.py`

**Interfaces:**

```python
class PullRequestMonitor:
    async def watch(self, task_id: UUID) -> None: ...
    async def resume_all_open(self) -> None: ...
    async def stop(self, task_id: UUID) -> None: ...
```

- [ ] Poll with configurable 15–60 second exponential backoff and jitter.
- [ ] Respect rate-limit status and emit one bounded warning rather than hot-looping.
- [ ] Persist only changed snapshots/events.
- [ ] Transition to `WAITING_FOR_CI`/`READY_TO_MERGE` according to conclusive status; never merge.
- [ ] Stop on terminal PR/task or backend draining; resume open PR monitors after subsystem 10 recovery.
- [ ] Test changing status, duplicate no-change poll, rate limit, CLI failure, external head push, close/merge, cancellation, and restart.
- [ ] Commit: `feat: monitor github pull requests`.

### Task 12: Fetch bounded CI/review details for explicit follow-up

**Files:**
- Create: `apps/engineering-cockpit/backend/cockpit/github/details.py`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/github/test_details.py`

- [ ] Fetch check/workflow/job/step metadata and bounded failed log tails only on user request.
- [ ] Fetch paginated reviews/comments with safe normalized text and source URLs.
- [ ] Enforce rate/size limits, authorization, and redaction; never render raw HTML/ANSI.
- [ ] Provide a user-previewable attachment that subsystem 09 may add to an explicit follow-up.
- [ ] Do not automatically start a repair turn.
- [ ] Test forbidden logs, expired workflow, huge logs, malicious comment, pagination, and rate limit.
- [ ] Commit: `feat: retrieve github failure and review context`.

### Task 13: Add issue/PR/delivery event integration

**Files:**
- Modify: `apps/engineering-cockpit/backend/cockpit/github/issues.py`
- Modify: `apps/engineering-cockpit/backend/cockpit/github/push.py`
- Modify: `apps/engineering-cockpit/backend/cockpit/github/pull_requests.py`
- Modify: `apps/engineering-cockpit/backend/cockpit/github/monitor.py`
- Create: `apps/engineering-cockpit/backend/tests/cockpit/github/test_events.py`

- [ ] Emit durable intent/result/status-change events after database commit.
- [ ] Include actor and expected/local/remote SHA evidence for state-changing actions.
- [ ] Avoid repeated unchanged polling events.
- [ ] Test event ordering/replay and no sensitive CLI output.
- [ ] Commit: `feat: publish github delivery events`.

### Task 14: Add generated frontend service clients

**Files:**
- Regenerate: `apps/engineering-cockpit/frontend/src/client/`
- Create: `apps/engineering-cockpit/frontend/src/services/CockpitIssueService.ts`
- Create: `apps/engineering-cockpit/frontend/src/services/CockpitDeliveryService.ts`

- [ ] Wrap generated issue preview/task source and delivery routes in service methods.
- [ ] Preserve expected SHA/version/idempotency inputs.
- [ ] Expose normalized unknown states without unsafe type casts.
- [ ] Run `bun run generate-client` and `bun run typecheck`.
- [ ] Commit: `feat: add github delivery service clients`.

### Task 15: Run real disposable GitHub acceptance

**Files:**
- Create: `apps/engineering-cockpit/backend/tests/manual/github_delivery.md`

- [ ] Use a disposable Techletes repository/issue and non-production base branch.
- [ ] Preview/snapshot issue, create local commit, push branch, create draft PR, observe checks, mark ready/draft, fetch one failed/success detail where available, and close/delete manually after evidence.
- [ ] Test remote branch divergence and confirm normal push blocks it.
- [ ] Test force-with-lease only on the disposable branch.
- [ ] Confirm no merge or auto-merge command is invoked.
- [ ] Record `gh`, Git, repository ruleset, and API behavior.
- [ ] Commit: `test: verify github delivery lifecycle`.

### Task 16: Complete subsystem verification

```bash
cd apps/engineering-cockpit
uv run pytest backend/tests/cockpit/github backend/tests/api/routes/test_cockpit_github_issues.py backend/tests/api/routes/test_cockpit_delivery.py -q
uv run mypy backend/cockpit/github
uv run ruff check backend/cockpit/github
cd frontend && bun run generate-client && bun run typecheck
```

- [ ] Commit: `test: verify cockpit github integration`.

## Exit criteria

Subsystem 12 is complete when issue snapshots are explicit and immutable, branch pushes are SHA-safe and non-forcing by default, draft PR creation is idempotent, check/review monitoring resumes after restart, external divergence blocks readiness, and no code path can merge, enable auto-merge, or deploy.
