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

## Plan completeness guardrails

A plan should remove implementation ambiguity without becoming a second copy of
the code. These are plan failures unless they are explicitly listed as unresolved
blocking decisions:

- `TBD`, `TODO`, `implement later`, `similar to Task N`, or placeholders left in
  executable tasks;
- vague requirements such as "handle edge cases", "add validation", "proper error
  handling", or "write tests" without naming observable behavior/failure cases;
- commands, file paths, symbols, APIs, schemas, or exact line ranges invented
  without inspecting the repository/documentation that defines them;
- an interface consumed by a later task without identifying where it already
  exists or which earlier task produces it;
- acceptance criteria that cannot be observed or validated from the stated checks;
- migrations/public API/config/deployment changes without compatibility, rollout,
  failure, and rollback considerations where those risks apply;
- security/authorization/data-boundary changes without explicit trust-boundary
  requirements and validation where relevant;
- a task depending on an unresolved product/architecture decision while pretending
  the implementation path is settled.

Tests in a plan should describe the behavior and important edge/failure cases the
implementation must prove. Include exact test code only when the test itself is a
critical contract or subtle regression; do not force verbose code snippets for
routine cases.

Validation commands must come from the repository or verified tooling. If a check
cannot currently be run, state the limitation and what evidence would satisfy it
instead of inventing expected output.

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

Do not leave template placeholders in the real plan. An outcome-based task is
valid without a full implementation listing.

## Self-review and handoff

Before finalizing, check once:

1. **Spec coverage:** every requirement/non-goal maps to a task or is explicitly
   excluded/unresolved.
2. **Placeholder/vagueness scan:** no executable task relies on the failure
   patterns above.
3. **Interface consistency:** producers/consumers use the same names, types,
   schemas, files, and ordering assumptions.
4. **Validation feasibility:** commands exist and acceptance criteria are actually
   testable; unavailable checks are called out.
5. **Risk coverage:** security/data/migration/compatibility/rollback concerns are
   represented when applicable.
6. **Delivery boundaries:** issue/PR bases, stacks, phase stops, and merge order
   reflect the requested workflow.

Correct plan defects inline rather than spawning a reviewer for formatting.

For plan-only requests, return the plan and stop. When the user already requested
implementation, continue into the authorized workflow without another execution
menu or subagent confirmation. Use
[subagent-driven-development](../subagent-driven-development/SKILL.md) for
approved delegation, otherwise [executing-plans](../executing-plans/SKILL.md).
Preserve an explicit one-phase stop; do not interpret a plan as unlimited consent.
