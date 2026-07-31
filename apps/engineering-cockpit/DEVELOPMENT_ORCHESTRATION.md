# Engineering Cockpit Development Orchestration

## Scope

This document defines how Codex is used to **implement this repository**.

It is not a product requirement for the Engineering Cockpit itself. Do not add cockpit runtime features merely to reproduce this Sol/Terra/Luna development workflow. The cockpit product continues to follow the subsystem specifications under `superpowers/`.

## Roles

### Controller session

Every human-started implementation session uses either **GPT-5.6 Sol** or **GPT-5.6 Terra** as the main controller.

The controller owns:

- reading and reconciling repository state;
- understanding the active specification and implementation plan;
- performing the plan pre-flight review;
- deciding the next task and constructing precise task briefs;
- dispatching subagents;
- answering subagent context questions;
- adjudicating reviewer findings against the specification;
- integrating reviewed work;
- updating the durable progress files;
- deciding whether the subsystem exit criteria have passed.

The controller is the thinker, planner, coordinator, and final verifier. It should not perform normal feature implementation itself when the subagent workflow is available. Small coordination-only edits, conflict resolution, planning corrections, progress updates, and integration work remain controller responsibilities.

### Implementation and review subagents

Every subagent must be dispatched explicitly with:

```yaml
model: gpt-5.6-luna
reasoning_effort: medium
```

This applies to:

- exploration subagents;
- implementer subagents;
- task-reviewer subagents;
- fix subagents;
- final whole-branch reviewer subagents.

Do not inherit the controller model, omit the reasoning setting, or substitute Sol/Terra for implementation tasks.

Each subagent is fresh and receives only the context needed for its role. It must not depend on the controller conversation history.

## Required skill

The controller must use:

```text
techletes-superpowers:subagent-driven-development
```

for every child implementation plan unless the user explicitly overrides the workflow for that plan.

The kickoff prompt contains explicit user consent for the active child plan. This satisfies the skill's per-plan confirmation requirement. A later child plan requires a new kickoff or an equally explicit user confirmation.

## Execution unit

The default unit is one child subsystem implementation plan on one subsystem branch/worktree.

Once Subagent-Driven Development is confirmed for that child plan, the controller proceeds continuously through its tasks without asking the user whether to continue between tasks. It stops only when:

- the user interrupts or requests closeout;
- a blocker cannot be resolved from available context;
- the specification or plan is materially contradictory;
- the execution environment prevents safe continuation;
- the child plan and its final review are complete.

The controller must not continue into the next subsystem without a new branch/worktree, updated `PROJECT_STATE.md`, and fresh explicit confirmation for that subsystem's plan.

### Evidence-based resequencing

Implementation order is a means to satisfy requirements, not an invariant. If
verified evidence exposes a dependency cycle, an impossible exit gate, or a
missing prerequisite, the controller may move the smallest safe prerequisite
earlier or split it from its later subsystem. It must preserve all security,
ownership, and acceptance requirements; update the affected specification and
plan before implementation; record the rationale and verification in durable
state; and keep the remaining later subsystem scope intact. Do not retain a
known-broken sequence merely because it appears in the original roadmap.

## Per-task loop

For every task in the active child implementation plan:

1. Reconcile the plan, Git state, `PROJECT_STATE.md`, and `.superpowers/sdd/progress.md`.
2. Record the task base commit before dispatch.
3. Generate or write a task brief containing the exact task requirements and binding constraints.
4. Dispatch a fresh Luna Medium implementer.
5. The implementer writes code, tests, runs focused verification, self-reviews, commits at the authorized boundary, and writes its report file.
6. Generate a review package from the recorded base commit through the implementer HEAD.
7. Dispatch a fresh Luna Medium task reviewer with the task brief, implementer report, review package, and binding global constraints.
8. For Critical or Important findings, dispatch a fresh Luna Medium fix subagent and then re-review.
9. Resolve every reviewer item that could not be verified from the diff.
10. Mark the task complete only after specification compliance and code-quality review pass.
11. Update the child-plan checkboxes and durable progress ledger.
12. Continue directly to the next incomplete task unless a stop condition applies.

At the end of the child plan, dispatch one fresh Luna Medium final reviewer over the complete branch diff. If it reports findings, dispatch one Luna Medium fix subagent with the complete actionable findings list, verify the fixes, and repeat the final review.

## Concurrency and worktrees

Sequential subagents work in the current subsystem checkout.

Never run two implementers concurrently in the same checkout. Parallel implementation is allowed only when tasks are genuinely independent and each implementer has a dedicated Git worktree assigned before dispatch. The Sol/Terra controller owns integration of parallel work.

Reviewers do not modify the checkout. Fix subagents may modify only after the controller has selected the findings to address.

## Durable progress

The implementation remains recoverable without previous Codex sessions through these files:

- `apps/engineering-cockpit/PROJECT_STATE.md` — current project/subsystem checkpoint;
- `.superpowers/sdd/progress.md` — task-level subagent execution and review ledger;
- the active child implementation plan — detailed verified checkboxes;
- `apps/engineering-cockpit/SESSION_LOG.md` — append-only session handoffs and findings;
- Git commits and test artifacts — objective implementation evidence.

The controller owns updates to these progress files. Implementer and reviewer subagents report through task-specific report files rather than independently rewriting global state.

## Session interruption and resume

When a Sol/Terra controller session ends before the child plan is complete, it must:

1. stop dispatching new tasks;
2. let any active subagent reach a safe conclusion or record it as interrupted;
3. record completed and reviewed tasks in `.superpowers/sdd/progress.md`;
4. update only verified child-plan checkboxes;
5. update `PROJECT_STATE.md` with the exact next task and repository state;
6. append `SESSION_LOG.md`;
7. commit and push only as explicitly authorized;
8. leave the working tree clean or document every uncommitted file.

A fresh Sol/Terra session resumes from the repository files and must not redispatch tasks marked complete in the SDD ledger.

## Product-boundary rule

The following are development-process facts, not cockpit functionality:

- the human starts Codex with Sol or Terra;
- the main session dispatches Luna Medium subagents;
- implementer/reviewer/fixer roles are coordinated through the Superpowers skill;
- `.superpowers/sdd/progress.md` tracks implementation work on this repository.

Do not add model selectors, Sol/Terra controller logic, Luna-specific dispatch rules, or this repository's SDD ledger to the Engineering Cockpit product unless a separate approved product specification explicitly requires them.
