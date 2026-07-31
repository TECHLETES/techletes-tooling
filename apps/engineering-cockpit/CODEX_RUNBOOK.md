# Engineering Cockpit Codex Runbook

This is the operational guide for implementing the Engineering Cockpit with local Codex CLI sessions.

The implementation must remain portable across machines and Codex installations. Repository files and Git history are therefore the source of truth. Saved Codex sessions are a convenience only.

The Sol/Terra/Luna workflow in this document applies to implementation of this repository. It is not functionality that must be built into the Engineering Cockpit product.

## Implementation roles

### Main controller

The user starts every implementation session with either:

- GPT-5.6 Sol; or
- GPT-5.6 Terra.

That main session acts as the controller: thinker, planner, coordinator, review adjudicator, integrator, and final verifier.

### Subagents

The controller uses `techletes-superpowers:subagent-driven-development` and dispatches every subagent explicitly with:

```yaml
model: gpt-5.6-luna
reasoning_effort: medium
```

This fixed subagent model applies to exploration, implementation, task review, fixes, and final whole-branch review.

Read [`DEVELOPMENT_ORCHESTRATION.md`](DEVELOPMENT_ORCHESTRATION.md) for the binding role and execution contract.

## Sources of truth

Read these in order at the beginning of every new controller session:

1. [`AGENTS.md`](AGENTS.md) — mandatory implementation and architecture rules.
2. [`DEVELOPMENT_ORCHESTRATION.md`](DEVELOPMENT_ORCHESTRATION.md) — Sol/Terra controller and Luna subagent workflow.
3. [`PROJECT_STATE.md`](PROJECT_STATE.md) — current subsystem, branch, verified checkpoint, blocker, and next action.
4. [`.superpowers/sdd/progress.md`](../../.superpowers/sdd/progress.md) — task-level implementer/reviewer ledger.
5. [`IMPLEMENTATION.md`](IMPLEMENTATION.md) — implementation entry point.
6. [`superpowers/INDEX.md`](superpowers/INDEX.md) — complete subsystem map and dependencies.
7. The current subsystem specification.
8. The current subsystem implementation plan.
9. [`SESSION_LOG.md`](SESSION_LOG.md) — recent controller-session history and handoffs.

Detailed completion remains recorded in the child-plan checkboxes. `PROJECT_STATE.md` summarizes project state; the SDD ledger tracks task dispatch and review state.

## Recommended execution model

- Implement one subsystem at a time.
- Use one branch and worktree per subsystem.
- Use one or more Sol/Terra controller sessions to complete that subsystem.
- Within a controller session, dispatch a fresh Luna Medium implementer per plan task.
- Dispatch a fresh Luna Medium task reviewer after every implementation task.
- Continue through the approved child plan without asking whether to proceed between tasks.
- Stop only for a user interruption, unresolved blocker, material plan contradiction, unsafe environment condition, or completed child plan and final review.
- Merge the subsystem before creating the next subsystem branch.
- Never ask one Luna subagent to implement the entire application or entire subsystem.

Recommended branch names:

```text
feature/cockpit-01-bootstrap
feature/cockpit-02-repository-registry
feature/cockpit-03-task-domain
...
feature/cockpit-05a-worktree-git-mount
...
feature/cockpit-15-release-proof
```

These are the canonical subsystem branch names. Child implementation plans,
`PROJECT_STATE.md`, and session handoffs must use the matching
`feature/cockpit-<id>-<slug>` name; do not introduce alternate names for the
same subsystem.

## One-time local setup

From WSL:

```bash
git clone git@github.com:TECHLETES/techletes-tooling.git ~/code/techletes/techletes-tooling
cd ~/code/techletes/techletes-tooling
git fetch origin --prune
```

Create an isolated implementation worktree for subsystem 01:

```bash
mkdir -p ~/worktrees/techletes-tooling

git worktree add \
  ~/worktrees/techletes-tooling/cockpit-01-bootstrap \
  -b feature/cockpit-01-bootstrap \
  origin/main

cd ~/worktrees/techletes-tooling/cockpit-01-bootstrap/apps/engineering-cockpit
```

If the repository's actual integration branch is not `main`, replace `origin/main` with the confirmed branch and record the choice in `PROJECT_STATE.md`.

Verify the starting point:

```bash
git status --short --branch
git log -5 --oneline
codex --version
```

## First controller session

Select GPT-5.6 Sol or GPT-5.6 Terra using the Codex model selector you normally use. Then start Codex from `apps/engineering-cockpit/` so the directory-scoped `AGENTS.md` applies:

```bash
codex --sandbox workspace-write
```

Paste this kickoff prompt:

```text
Act as the Sol/Terra controller for implementation of the Techletes Engineering Cockpit repository.

This Sol/Terra/Luna workflow is only for implementing the repository. Do not interpret it as Engineering Cockpit product functionality.

I explicitly authorize use of techletes-superpowers:subagent-driven-development for the active child implementation plan recorded in PROJECT_STATE.md.

Before changing anything:

1. Read AGENTS.md.
2. Read DEVELOPMENT_ORCHESTRATION.md.
3. Read CODEX_RUNBOOK.md.
4. Read PROJECT_STATE.md.
5. Read the repository-root .superpowers/sdd/progress.md.
6. Read IMPLEMENTATION.md.
7. Read superpowers/INDEX.md, the master specification, and the master roadmap.
8. Read the exact specification and implementation plan for the current subsystem recorded in PROJECT_STATE.md.
9. Inspect git status, the current branch, worktree path, HEAD, recent commits, and any existing task report/review artifacts.
10. Reconcile PROJECT_STATE.md, the SDD ledger, child-plan checkboxes, and Git evidence before implementation.
11. Read and follow techletes-superpowers:subagent-driven-development.

Controller responsibilities:

- remain the main thinker, planner, coordinator, integration owner, and final verifier;
- perform the required pre-flight plan review before dispatching Task 1;
- initialize or reconcile the durable SDD task ledger;
- create precise task briefs and report paths;
- dispatch a fresh implementer for each plan task;
- dispatch a fresh task reviewer after every implementation;
- dispatch fix subagents for Critical or Important findings and re-review;
- resolve reviewer items that cannot be verified from the diff;
- dispatch one final whole-branch reviewer after all tasks pass;
- update durable progress only from verified evidence.

Every subagent dispatch, including exploration, implementation, review, fix, and final review, must explicitly use:

model: gpt-5.6-luna
reasoning_effort: medium

Do not perform normal feature implementation directly while the subagent workflow is available. You may perform coordination edits, progress/state updates, planning corrections, conflict resolution, and integration work.

Sequential implementers use the current subsystem checkout. Never run parallel implementers in the same checkout. Parallel work is allowed only with separately assigned worktrees.

After the pre-flight review, execute the active child plan continuously through fresh Luna Medium subagents. Do not ask whether to continue between tasks. Stop only when:

- I interrupt or request closeout;
- a blocker cannot be resolved;
- the specification or plan is materially contradictory;
- the environment prevents safe continuation; or
- the child plan, task reviews, final branch review, and exit criteria are complete.

Do not continue into the next subsystem.

Before ending the controller session:

- stop dispatching new tasks;
- safely conclude or record any active subagent;
- run or confirm required verification;
- update only reviewed and verified child-plan checkboxes;
- update .superpowers/sdd/progress.md;
- update PROJECT_STATE.md atomically;
- append a concise SESSION_LOG.md entry;
- record branch, worktree, HEAD, task statuses, implementer commits, reports, reviews, tests, findings, blockers, working-tree state, and one exact next action;
- commit only at an authorized plan boundary;
- leave the working tree clean, or explicitly record every uncommitted file and why it remains.
```

## Beginning every later controller session

A new controller session must not depend on the previous chat. Start from the same subsystem worktree:

```bash
cd ~/worktrees/techletes-tooling/cockpit-01-bootstrap/apps/engineering-cockpit
git status --short --branch
git log -5 --oneline
codex --sandbox workspace-write
```

Select Sol or Terra, then paste:

```text
Resume as the Sol/Terra controller for the Engineering Cockpit implementation from repository state, not assumed chat memory.

This controller/subagent workflow is for implementation of the repository only, not cockpit product functionality.

I explicitly authorize techletes-superpowers:subagent-driven-development for the currently active child implementation plan.

Read AGENTS.md, DEVELOPMENT_ORCHESTRATION.md, CODEX_RUNBOOK.md, PROJECT_STATE.md, the repository-root .superpowers/sdd/progress.md, IMPLEMENTATION.md, superpowers/INDEX.md, the active subsystem specification and plan, and the latest SESSION_LOG.md entries.

Inspect the branch, worktree, HEAD, status, recent commits, task reports, and review packages. Reconcile Git evidence, child-plan checkboxes, PROJECT_STATE.md, and the SDD ledger. Do not redispatch any task already marked review_passed unless objective evidence shows the ledger is wrong.

Use techletes-superpowers:subagent-driven-development. Remain the controller and dispatch every fresh exploration, implementer, reviewer, fixer, and final-review subagent explicitly with:

model: gpt-5.6-luna
reasoning_effort: medium

Resume at the first incomplete or interrupted task. Continue through the active child plan without asking between tasks. Apply the full implement-review-fix-re-review loop and final whole-branch review. Stop only for my interruption, an unresolved blocker or contradiction, unsafe execution conditions, or completed child-plan exit criteria. Do not enter the next subsystem.

Perform the mandatory durable closeout before the session ends.
```

## Resuming a saved Codex session

On the same machine, Codex can resume a saved conversation:

```bash
codex resume
```

Or resume the latest session without the picker:

```bash
codex resume --last
```

Use this only as a convenience. After resuming, still reconcile repository state. Saved context can be stale after rebases, commits from another machine, branch changes, or subagent work completed elsewhere.

## Ending a controller session deliberately

When you want to stop, send:

```text
Close out this Sol/Terra controller session now. Do not dispatch another task and do not enter another subsystem.

This is repository implementation closeout, not cockpit product behavior.

1. Stop dispatching new subagents.
2. Let any active subagent finish safely, or record it as interrupted with its exact task, checkout, report path, and partial state.
3. Confirm required tests and verification for all work being marked complete.
4. Review the integrated diff for scope, correctness, generated artifacts, migrations, secrets, and prohibited shortcuts.
5. Mark child-plan checkboxes only for tasks that passed implementation, task review, and required verification.
6. Update the repository-root .superpowers/sdd/progress.md with exact task states, base/HEAD commits, report paths, review packages, findings, and next action.
7. Update PROJECT_STATE.md with subsystem, branch, worktree, HEAD, completed work, verification, blockers, clean/dirty state, and one exact next action.
8. Append SESSION_LOG.md using its required format.
9. Create only an authorized plan-boundary or progress/handoff commit.
10. Report final branch, HEAD, working-tree state, task/review status, verification results, blockers, and next action, then stop.
```

Do this before switching machines, before a long interruption, or whenever the controller context is becoming crowded.

## Moving to another machine or fresh clone

First ensure the implementation branch and progress commits have been pushed explicitly:

```bash
git status --short --branch
git push -u origin feature/cockpit-01-bootstrap
```

On the new machine:

```bash
git clone git@github.com:TECHLETES/techletes-tooling.git ~/code/techletes/techletes-tooling
cd ~/code/techletes/techletes-tooling
git fetch origin --prune

git worktree add \
  ~/worktrees/techletes-tooling/cockpit-01-bootstrap \
  feature/cockpit-01-bootstrap

cd ~/worktrees/techletes-tooling/cockpit-01-bootstrap/apps/engineering-cockpit
codex --sandbox workspace-write
```

Select Sol or Terra and use the resume prompt above. No prior Codex session is required because the branch contains implementation, plan checkboxes, project state, the SDD ledger, reports, reviews, and session log.

## Completing a subsystem

A subsystem is complete only when:

1. every required implementation-plan checkbox is verified;
2. every task passed its Luna Medium task review;
3. all Critical and Important findings were fixed and re-reviewed;
4. one Luna Medium final reviewer approved the complete branch diff;
5. all subsystem exit criteria pass;
6. `PROJECT_STATE.md` marks the subsystem complete and identifies the next dependency-valid subsystem;
7. `.superpowers/sdd/progress.md` contains the final task and review evidence;
8. `SESSION_LOG.md` contains the final evidence summary;
9. the working tree is clean;
10. commits are reviewable and pushed only after explicit approval;
11. the subsystem branch is reviewed and merged according to repository policy.

After merge, create the next subsystem branch from the updated integration branch. Do not continue using the merged branch for the next subsystem. Start a new Sol/Terra session and provide fresh explicit consent for the next child plan.

## State-file rules

### `PROJECT_STATE.md`

- Current compact project/subsystem truth.
- Overwritten in place at each verified checkpoint.
- Must agree with Git, the child plan, and the SDD ledger.
- Must never contain secrets, access tokens, or copied terminal logs.

### `.superpowers/sdd/progress.md`

- Task-level controller ledger for the active child plan.
- Records implementer bases/commits, report paths, review packages, reviewer result, findings, and next action.
- Tasks marked `review_passed` are not redispatched.
- Controlled by the Sol/Terra controller, not independently rewritten by subagents.
- Implementation workflow only; never application runtime state.

### Child implementation plans

- Detailed truth for completed plan requirements.
- Check a box only after stated verification and required review pass.
- Never bulk-check tasks based on intent or partial work.

### `SESSION_LOG.md`

- Append-only human-readable controller-session history.
- One concise entry per meaningful session or recovery event.
- Do not paste full command output; record commands, results, and evidence locations.

### Git commits

- Portable memory and recovery boundary.
- Prefer verified commits at plan boundaries.
- Never claim portability for uncommitted work.

## Handling discoveries and plan changes

When implementation reveals that a specification is wrong or impossible:

1. stop the affected task;
2. record the finding and evidence in `PROJECT_STATE.md`, `.superpowers/sdd/progress.md`, and `SESSION_LOG.md`;
3. update the affected child specification;
4. update the matching implementation plan;
5. review downstream subsystem contracts for impact;
6. obtain a human decision when a reviewer finding conflicts with plan-mandated behavior;
7. resume implementation only after the planning documents are internally consistent.

Do not silently work around a failed architecture assumption.

## Appropriate Luna task size

A good Luna implementer assignment covers one bounded unit such as:

- one database model/migration slice plus tests;
- one adapter interface and contract-test slice;
- one API endpoint group plus generated client update;
- one frontend workflow plus Playwright coverage;
- one external-tool compatibility experiment and documented decision;
- one child-plan commit boundary.

The Sol/Terra controller may execute multiple such assignments in one session, but each Luna subagent remains fresh, bounded, reviewed, and independently evidenced.
