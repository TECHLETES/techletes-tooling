---
name: executing-plans
description: Execute or resume a written plan inline when delegation is unavailable, declined, or unnecessary, with explicit phase boundaries and verification checkpoints.
---

# Executing Plans

Read the plan, applicable instructions, working-tree state, and progress ledger.
Reconcile completed tasks with the current branch, plan identity, and actual
commits before resuming. Start the next incomplete authorized task, not the first
task or an unnecessary approval prompt for an already completed phase.

Respect `plan-only`, `one-phase`, and `through-end` scope as described in
[subagent-driven-development](../subagent-driven-development/SKILL.md).
A plan-only request stops at the plan. Existing explicit execution approval is
sufficient; preserve any requested phase stop. Do not advertise delegation as a
guaranteed quality improvement or insist on it for a small inline change.

Inspect relevant code and resolve concrete gaps before implementation. For each
coherent task, implement its acceptance criteria, run focused checks, self-review
the actual diff, resolve findings, and commit within the authorized scope.
Record tested revisions and accepted task/phase ranges in durable progress.
Use the same preservation/all-changes rules as the delegated workflow.

Use independent review for substantive/risky gates when available. If unavailable,
perform a parent review and state that limitation; never label it independent or
claim an unperformed review. Unresolved correctness/security gaps still block a
clean completion claim. Broader integration checks belong at justified phase/
final gates, not every mechanical step.

Attempt bounded diagnosis of blockers; ask only for decisions or access the
available evidence cannot resolve. Do not ignore failures, repeatedly retry the
same approach, or silently change requirements to make a test pass.

At an authorized stop, report the checkpoint. At final completion use
[finishing-a-development-branch](../finishing-a-development-branch/SKILL.md)
with the user's existing delivery choice. Do not introduce an extra menu when
the user already requested a PR. Never implement directly on an integration
branch without explicit authorization.
