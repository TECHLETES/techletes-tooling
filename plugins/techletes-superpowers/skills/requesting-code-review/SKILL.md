---
name: requesting-code-review
description: Review substantive changes, consequential milestones, or final branches independently against requirements, surrounding code, integration risks, and revision-matched validation evidence.
---

# Requesting Code Review

Use [model-routing.md](../subagent-driven-development/references/model-routing.md):
Terra high for normal independent review, Sol high for consequential security,
data-loss, migrations, or cross-cutting changes. Do not inherit a Luna worker's
configuration. Use a fresh context rather than the implementation thread.

Review coherent deliverables, not every mechanical edit. A parent can review a
routine low-risk task; record that honestly. Require independent review for
substantive/risky milestones and before substantial final delivery. Do not run
an identical second review when the exact revision, requirements, and whole-branch
scope were already independently covered. Small ad-hoc changes need proportionate
verification, not an obligatory agent hierarchy.

## Determine the actual range

For an existing PR, inspect its actual base instead of assuming main or staging:

```bash
BASE_BRANCH=$(gh pr view --json baseRefName --jq .baseRefName)
git fetch origin "$BASE_BRANCH"
BASE_SHA=$(git merge-base HEAD "origin/$BASE_BRANCH")
HEAD_SHA=$(git rev-parse HEAD)
```

Without a PR, use the explicitly requested/planned base, then repository policy
(Techletes default: staging). For a stacked child, review against its direct
parent feature branch so parent changes are not reviewed twice. Recompute the
base after a restack/retarget. If a requested base conflicts with an existing PR,
resolve that discrepancy explicitly; do not silently retarget it.

For task review, use the commit recorded before that task, not HEAD~1 or a guessed
log entry. Generate a package with the subagent-driven-development skill's
`scripts/review-package BASE_SHA HEAD_SHA`. Check for dirty/untracked changes:
a committed-range package does not include them.

## Dispatch and act

Use [code-reviewer.md](code-reviewer.md) for whole-branch review, or the
[subagent task reviewer](../subagent-driven-development/task-reviewer-prompt.md)
for a bounded task. Supply requirements, constraints, package, exact revisions,
relevant interfaces, test-report path, and unresolved earlier findings. Keep the
implementation narrative separate from requirements and ask for requirements/
diff-first assessment. Do not repeat full repository exploration.

Reviewers can inspect complete functions, callers, and unchanged code to resolve
concrete risks. Reuse validation only when its revision, environment, and scope
match; missing/stale evidence needs a focused check, not automatic trust. Do not
modify shared state or widen permissions to reproduce a finding.

Resolve Critical/Important issues before acceptance. Send consolidated findings
to the existing worker when suitable; run covering tests and re-review fixes.
Track Minor findings through final disposition, rather than silently dropping
them. Evaluate disputed findings against source and tests, not the author's
confidence. Surface plan-mandated defects as decisions to resolve.

Report spec and quality verdicts, evidence-backed findings, checks actually
performed, and limitations. No model, test, or independent-review claims without
observable evidence. A clean verdict is not approval to merge.
