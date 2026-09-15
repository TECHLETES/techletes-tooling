---
name: writing-plans
description: Plan multi-step, dependent, or cross-cutting changes whose interfaces, acceptance criteria, sequencing, validation, and delivery boundaries need coordination.
---

# Writing Plans

Write a plan only when it reduces implementation or review risk. A clear one-file
change does not require a design document. Read the relevant code, issue/spec,
and applicable instructions; reuse approved decisions rather than restarting
design. Resolve material ambiguity with brainstorming or the stronger planning
role in [model-routing.md](../subagent-driven-development/references/model-routing.md).
Do not spend a stronger model on routine plan transcription.

Save justified plans to `docs/superpowers/plans/YYYY-MM-DD-<feature>.md` unless the
user specifies another location. Specify outcomes and constraints without writing
the implementation twice. Include code only for a necessary interface, invariant,
subtle algorithm, or exact regression case; do not require full code for every step.

## Delivery boundaries

Prefer one PR per issue or independently reviewable change. Record branch and
actual PR base in a Delivery section; honor an explicitly requested base first.
Otherwise use the documented integration branch (Techletes default: `staging`).
For issue B depending on an open PR A, target B at A's feature branch. Do not
combine unrelated issues merely because implementation overlaps.

While both PRs are under review, merge parent updates into the child instead of
repeatedly rewriting reviewed history. Merge bottom-up. After the parent merges,
retarget/restack the child onto the actual integration branch. A squash-merged
parent requires replaying only child-specific commits with `rebase --onto` or
an equivalent operation, not replaying the parent's commits.

## Right-size tasks and phases

A task is a coherent deliverable with meaningful acceptance criteria and a
validation cycle. Fold setup, configuration, tests, and docs into the task that
needs them. Do not create a separate agent/review gate for each mechanical step.
Group tasks into explicit phase boundaries only when those checkpoints help the
user or integration. Keep `### Task N: ...` headings for the task-brief extractor.

Specify dependencies and interfaces, not just filenames. Different files can
still share contracts or mutable resources. Default to sequential writers;
justify any parallel implementation and its isolated worktrees/resources.

## Plan template

```markdown
# [Feature] Implementation Plan

**Goal:** [observable outcome]
**Architecture:** [smallest viable approach and relevant decisions]
**Execution:** [plan-only / one-phase / through-end, from user authorization]

## Global Constraints
[Exact binding requirements: security/data boundaries, interfaces, versions,
formats, dependency limits. Separate known facts from unresolved decisions.]

## Delivery
[Issue/logical change -> branch -> PR base; dependencies and merge order.]

## Phases
[Task grouping, acceptance gate, requested stop boundary; no invented approval.]

### Task N: [testable deliverable]
**Outcome / non-goals:** [scope]
**Depends on:** [verified task/interface, or none]
**Files:** [exact paths to inspect/change/test]
**Interfaces:** [consumes/produces; exact names/types where binding]
**Acceptance:** [observable behavior, edge cases, failure handling]
**Worker:** [role from routing policy and brief reason]
**Review:** [parent for routine low-risk work, independent for substantive/risky work]
**Validation:** [actual repository commands, expected outcomes and environment]
- [ ] Implement the bounded change and meaningful regression checks.
- [ ] Run validation, self-review, commit authorized scope, and report evidence.
- [ ] Resolve review findings and record the accepted revision before advancing.
```

Do not leave these template placeholders in the real plan. Replace vague phrases
such as "handle errors" with concrete failure behavior and observable checks.
Do not invent commands, symbols, APIs, or exact line numbers without inspecting
the source. An outcome-based task is valid without a full implementation listing.

## Self-review and handoff

Check spec coverage, interface consistency, validation feasibility, task size,
risk-based routing, phase authorization, and PR/stack boundaries once. Correct
the plan rather than spawning a reviewer for its formatting.

For plan-only requests, return the plan and stop. When the user already requested
implementation, continue into the authorized workflow without another execution
menu or subagent confirmation. Use
[subagent-driven-development](../subagent-driven-development/SKILL.md) for
approved delegation, otherwise [executing-plans](../executing-plans/SKILL.md).
Preserve an explicit one-phase stop; do not interpret a plan as unlimited consent.
