---
name: subagent-driven-development
description: Execute approved multi-step plans or resume phased implementation in the current session using bounded workers, risk-based model routing, evidence-based reviews, and durable progress tracking.
---

# Subagent-Driven Development

Keep the main session responsible for scope, decisions, integration, and
acceptance. Delegate bounded implementation, not unresolved product decisions.
Use one implementation writer at a time by default. Do small, clear, low-risk
changes inline; do not manufacture tasks merely to use subagents.

## Authorization and scope

An explicit request to use subagents, execute this plan with this workflow, or
continue an approved run is authorization. A project instruction selecting this
workflow is also sufficient for an implementation request. Do not ask again for
permission already given. A plan-only request is not permission to implement.
Ask once only when the execution/delegation scope is genuinely unspecified.

Record the execution mode: `plan-only`, `one-phase`, or `through-end`.
- "Implement/execute this plan" authorizes its remaining approved scope.
- "Phase by phase" or "only phase N" stops after the current/named phase unless
  automatic continuation was explicitly authorized.
- On resume, inspect progress and start the next incomplete authorized phase;
  do not stop merely to announce that an earlier phase is already complete.
- A later user stop or scope change takes effect before the next dispatch.

Continue through authorized phases without repeated approval prompts. Pause for
an unresolved material requirement conflict, a blocker you cannot safely
resolve, a requested checkpoint, or completion. Report brief meaningful progress
between phases; do not dump raw logs or ask "should I continue?" mid-approved run.

## Pre-flight

Read applicable AGENTS.md, the approved plan/spec, relevant issue/PR context,
current branch, and working-tree status. Use the existing checkout for sequential
work. Create a feature branch from the explicitly requested base; otherwise use
the documented integration branch (Techletes default: staging). For a stacked
PR, use its direct parent feature branch. Do not implement on a protected
integration branch without explicit authorization.

Review the plan once for conflicting requirements, missing interfaces, and
unsafe assumptions. Resolve from existing evidence first; batch only genuinely
blocking decisions for the user. Do not ask a planner to repeat a sound plan.

Load [model-routing.md](references/model-routing.md) before the first dispatch.
Use its explicit role/model/effort settings and evidence-based escalation rules.
Preserve the user's main-session model choice; the ordinary recommendation is
Terra medium, not an instruction to switch models silently.

## Durable progress and recovery

Use `scripts/sdd-workspace` to locate the existing `.superpowers/sdd/` workspace.
Inspect its `progress.md` before creating new state. Keep a compact ledger with:
- repository/branch, PR base, plan path and content hash;
- authorized mode, phase boundary, current task and accepted commit ranges;
- role/model/effort, correction count, review mode/verdicts, tested revision;
- unresolved findings/decisions and the next authorized action.

On resume or compaction, reconcile the ledger with git history and the current
plan. Reuse completed tasks only when the plan identity, branch, accepted
commits, and relevant requirements still match. A stale ledger is not proof of
completion; investigate mismatches without blindly replaying completed work.
Never run destructive cleanup to reset workflow state.

## Execute a testable task

1. **Prepare.** Record `TASK_BASE` before any task changes. Extract the task with
   `scripts/task-brief PLAN_FILE N`; it prints only the brief path on stdout and
   includes the plan's Global Constraints. Keep `### Task N: ...` headings in
   plans. Ensure the brief has objective, non-goals, owned paths, exact interface
   constraints, acceptance criteria, validation commands, and assigned checkout.
   Add binding constraints from other sources and only relevant prior decisions.
2. **Route.** Choose routine/high/deep worker from the shared policy. Set the
   actual configuration, not just words in its prompt. Use the
   [implementer template](implementer-prompt.md). No nested delegation.
3. **Implement.** The worker runs targeted checks, self-reviews, and commits
   within its assigned scope. Keep it alive for focused corrections. A fresh
   task gets a fresh worker; a context answer need not create a new one.
4. **Gate.** Inspect the actual diff and test evidence, not only the summary.
   For substantive tasks use a fresh independent reviewer with the
   [task-reviewer template](task-reviewer-prompt.md). A routine low-risk task
   may use a parent review with both verdicts recorded as `review_mode=parent`;
   do not label it independent. Require independent review at consequential
   milestones and before substantial whole-branch delivery.
5. **Correct.** Address Critical/Important findings before moving on. Send one
   consolidated correction request to the same worker where suitable. Re-run
   covering checks on the changed revision and re-review the affected scope.
   After one focused correction fails without new evidence, apply the routing
   policy rather than looping. Track Minor findings for final disposition.
6. **Accept.** Record spec compliance, quality verdict, validated revision,
   commit range, unresolved limitations, and next action. Close finished child
   threads. Do not carry an unfinished task into the next dependent task.

Dependent tasks work well sequentially: complete and verify the producer's
contract before dispatching its consumer. File separation alone does not imply
independence. Parallel read-only questions are optional when they avoid real
waiting or repeated exploration. Parallel writers require separately assigned
Git worktrees, independent contracts/resources, an explicit integration order,
and verification of the combined result. Never share a checkout among writers.

## Evidence and review packages

Generate `scripts/review-package TASK_BASE HEAD` and pass the returned path.
Never replace TASK_BASE with HEAD~1: a task or correction can span many commits.
Ensure all task changes are committed first; the package excludes uncommitted
and untracked files. Do not let unrelated dirty work disappear from acceptance.

Give the reviewer requirements, global constraints, the diff/package, report
path, and relevant integration boundaries. Require requirements/diff first and
the implementation narrative second. Read surrounding code and call sites when
needed to resolve a concrete risk; a diff is not a hard evidence boundary.
Do not tell reviewers what not to flag or pre-rate findings for them.

A test report must name its command, outcome, relevant output, environment, and
tested revision. Reuse evidence only for unchanged code and compatible scope/
environment. Missing, stale, ambiguous, or contradicted evidence needs focused
verification. Reviewers may request targeted reproductions; they must not
modify the shared checkout or widen permissions to run them. Run broader suites
at integration/final gates when impact warrants them, not once per trivial edit.
Passing tests do not prove that requirements or architecture are correct.

Resolve every unverified requirement before acceptance, or state it as a blocker/
limitation without a clean verdict. A finding that contradicts an explicit
requirement is a decision to resolve, not permission to ignore the finding or
silently change the contract.

## Phase completion and commit scope

Before advancing, finish phase checks/review, commit remaining authorized
changes, and record the accepted phase range. Worker commits can be the phase
checkpoint; do not create empty bookkeeping commits.

Default to scoped commits preserving unrelated user work. When the user
explicitly requests committing ALL changes, include their modified/untracked
files and deletions too, after inspecting the full diff for secrets and
unintended generated content and validating the complete snapshot. Never treat
"all" as permission to commit credentials, ignored files, or discard changes.
Never reset, stash, or revert user edits merely to produce a clean status.

If the user requested one phase, report that checkpoint and stop. Otherwise
continue to the next incomplete authorized phase without asking again.

## Final integration and delivery

Determine the real PR base from GitHub/planned delivery, not a hard-coded main.
For stacks, review only the child delta against its direct parent; recompute the
base after a restack. Use the merge-base with the actual PR base for the final
package. Run the justified integration checks on the final candidate revision.

Use [requesting-code-review](../requesting-code-review/SKILL.md) for one fresh
whole-branch review, including unresolved Minor findings. Skip an identical
second review only when the same independent reviewer already covered the exact
final revision, full requirements, and whole-branch scope. Consolidate final
fixes into one worker request; re-test and re-review their effects.

Use [finishing-a-development-branch](../finishing-a-development-branch/SKILL.md)
with the user's existing delivery choice. A request to open a PR is already that
choice, not an invitation to present a merge/discard menu. Never merge, enable
auto-merge, or delete branches without authorization.

Report changes, actual validation, limitations, branch/PR, and remaining work.
Do not claim model configuration, independent review, tests, or performance
improvements that were not actually observed.
