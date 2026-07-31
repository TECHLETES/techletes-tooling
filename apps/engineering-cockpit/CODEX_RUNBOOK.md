# Engineering Cockpit Codex Runbook

This is the operational guide for implementing the Engineering Cockpit with local Codex CLI sessions.

The implementation must remain portable across machines and Codex installations. Repository files and Git history are therefore the source of truth. Saved Codex sessions are a convenience only.

## Sources of truth

Read these in order at the beginning of every new implementation session:

1. [`AGENTS.md`](AGENTS.md) — mandatory rules and architecture constraints.
2. [`PROJECT_STATE.md`](PROJECT_STATE.md) — current subsystem, branch, verified checkpoint, blocker, and next action.
3. [`IMPLEMENTATION.md`](IMPLEMENTATION.md) — implementation entry point.
4. [`superpowers/INDEX.md`](superpowers/INDEX.md) — complete subsystem map and dependencies.
5. The current subsystem specification.
6. The current subsystem implementation plan.
7. [`SESSION_LOG.md`](SESSION_LOG.md) — recent implementation history and handoffs.

Detailed completion remains recorded in the checkboxes of each child implementation plan. `PROJECT_STATE.md` summarizes those plans but does not replace them.

## Recommended execution model

- Implement one subsystem at a time.
- Use one branch and worktree per subsystem.
- Keep sessions small: one coherent plan task, verification gate, or reviewable commit per session.
- Continue on the same subsystem branch across sessions until its exit criteria pass.
- Merge the subsystem before creating the next subsystem branch.
- Never ask one Codex session to implement the entire application in one run.

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

## First Codex session

Start Codex from `apps/engineering-cockpit/` so the directory-scoped `AGENTS.md` is in scope:

```bash
codex --sandbox workspace-write
```

Use this kickoff prompt:

```text
Implement the Techletes Engineering Cockpit in a controlled, resumable way.

Before changing anything:
1. Read AGENTS.md, CODEX_RUNBOOK.md, PROJECT_STATE.md, IMPLEMENTATION.md, superpowers/INDEX.md, the master specification, and the master roadmap.
2. Read the specification and implementation plan for the current subsystem recorded in PROJECT_STATE.md.
3. Inspect git status, the current branch, and recent commits.
4. Confirm that the current branch and worktree match PROJECT_STATE.md.
5. Summarize the exact next unchecked plan step, its dependencies, expected files, verification command, and stop condition.

Then execute only the smallest coherent unchecked task from that child plan. Follow test-first steps and the Techletes Superpowers workflow required by the plan.

You are authorized to create commits only when the child plan specifies a commit boundary or when committing the session handoff/progress state after a verified checkpoint. Do not push, merge, create a PR, force, rebuild, or clean up unless I explicitly request it.

Before ending the session:
- run the exact verification required for the completed step;
- update the child-plan checkboxes only for verified work;
- update PROJECT_STATE.md atomically;
- append a concise entry to SESSION_LOG.md;
- include the branch, HEAD SHA, tests run, remaining next action, and blockers;
- commit the verified implementation and state updates at the plan-defined boundary;
- leave the working tree clean, or explicitly record every uncommitted file and why it remains.

Do not continue into the next subsystem.
```

## Beginning every later session

A new Codex session must not depend on the previous chat. Start from the same worktree and run:

```bash
cd ~/worktrees/techletes-tooling/cockpit-01-bootstrap/apps/engineering-cockpit
git status --short --branch
git log -5 --oneline
codex --sandbox workspace-write
```

Use this resume-from-repository prompt:

```text
Resume the Engineering Cockpit implementation from repository state, not from assumed chat memory.

Read AGENTS.md, CODEX_RUNBOOK.md, PROJECT_STATE.md, IMPLEMENTATION.md, superpowers/INDEX.md, the current subsystem spec and plan, and the latest entries in SESSION_LOG.md. Inspect git status and recent commits. Verify that PROJECT_STATE.md agrees with the branch, HEAD, plan checkboxes, and working tree.

If they disagree, stop implementation and reconcile the state files from Git evidence first. Otherwise, identify the next smallest unchecked plan step and implement only that step. Run its required verification, update the progress files, and close out the session according to CODEX_RUNBOOK.md.
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

Use this only as a convenience. After resuming, still instruct Codex to read `PROJECT_STATE.md` and compare it with Git. Saved session context can be stale after rebases, commits from another machine, or branch changes.

## Ending a session deliberately

When a useful checkpoint has been reached, send:

```text
Close out this implementation session now. Do not start another plan task.

Run the required verification for the work completed in this session. Review the diff for scope and correctness. Update the relevant child-plan checkboxes only where verification passed. Update PROJECT_STATE.md and append SESSION_LOG.md with the exact branch, HEAD, completed work, verification results, decisions, blockers, uncommitted files, and next action. Create the plan-defined commit or a dedicated verified progress/handoff commit if appropriate. Report the clean/dirty working-tree state and stop.
```

Do this before the context becomes crowded, before switching machines, and before any long interruption.

## Moving to another machine or fresh clone

First make sure the current implementation branch and progress commits have been pushed explicitly:

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

Then use the resume-from-repository prompt above. No prior Codex session is required because the branch contains the implementation, plan checkboxes, project state, and session log.

## Completing a subsystem

A subsystem is complete only when:

1. every required implementation-plan checkbox is verified;
2. all subsystem exit criteria pass;
3. `PROJECT_STATE.md` marks the subsystem complete and identifies the next dependency-valid subsystem;
4. `SESSION_LOG.md` contains the final evidence summary;
5. the working tree is clean;
6. commits are reviewable and pushed only after explicit approval;
7. the subsystem branch is reviewed and merged according to repository policy.

After merge, create the next subsystem branch from the updated integration branch. Do not continue using the merged branch for the next subsystem.

## State-file rules

### `PROJECT_STATE.md`

- Current compact truth.
- Overwritten in place at each verified checkpoint.
- Must agree with Git and child-plan checkboxes.
- Must never contain secrets, access tokens, or copied terminal logs.

### Child implementation plans

- Detailed truth for completed tasks.
- Check a box only after its stated verification passes.
- Never bulk-check tasks based on intent or partial work.

### `SESSION_LOG.md`

- Append-only human-readable implementation history.
- One concise entry per meaningful session or recovery event.
- Do not paste full command output; record commands, result, and evidence location.

### Git commits

- Portable memory and recovery boundary.
- Prefer a verified commit before ending a session.
- Never claim portability for uncommitted work.

## Handling discoveries and plan changes

When implementation reveals that a specification is wrong or impossible:

1. stop the implementation step;
2. record the finding and evidence in `PROJECT_STATE.md` and `SESSION_LOG.md`;
3. update the affected child specification;
4. update the matching implementation plan;
5. review downstream subsystem contracts for impact;
6. resume implementation only after the planning documents are internally consistent.

Do not silently work around a failed architecture assumption.

## Recommended session size

A good session ends after one of these:

- one database model/migration slice plus tests;
- one adapter interface and contract-test slice;
- one API endpoint group plus generated client update;
- one frontend workflow plus Playwright coverage;
- one external-tool compatibility experiment and documented decision;
- one child-plan commit boundary.

End the session when a plan step is verified, even if Codex still has context available. This produces reliable checkpoints and makes fresh-clone continuation straightforward.
