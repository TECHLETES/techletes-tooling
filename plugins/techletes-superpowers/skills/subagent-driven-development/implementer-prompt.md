# Implementer handoff

Select the configured role using [model-routing.md](references/model-routing.md).
Use [escalation.md](references/escalation.md) when scope or reasoning starts to
widen, and [evidence.md](references/evidence.md) for the handoff contract. This is
a prompt template, not a dispatch API schema. Use only fields supported by the
current client and do not leave placeholders in a real dispatch.

```text
Implement Task [N]: [objective].
Role: [configured worker role]; model/effort: [actual selected settings].
Work only in [absolute checkout path]. Do not spawn children.

Read [BRIEF_FILE] first: it is the source of requirements, non-goals, owned
paths, global constraints, interfaces, acceptance criteria, and validation.
Relevant prior decisions/interfaces not already in the brief: [only essentials].
Starting revision: [TASK_BASE]. Report file: [REPORT_FILE].
Commit scope: [owned changes, or explicit user-authorized all-changes policy].

Before editing, stop and ask the coordinator if a material requirement,
acceptance criterion, interface, or dependency is genuinely ambiguous or
conflicts with the repository/tests. Do not ask about choices the brief already
settles and do not invent policy to avoid a question.

Implement the smallest change following existing patterns. Inspect additional
code when needed, but do not expand scope or invent unresolved contracts.
Preserve user changes. Do not push, merge, switch branches, rewrite history, or
widen permissions.

Escalate with NEEDS_CONTEXT or BLOCKED when any of these occurs:
- multiple materially different architecture choices remain unresolved;
- requirements/tests disagree on expected behavior;
- completing the task requires an unplanned public API/schema/migration,
  deployment/configuration contract, or broad restructuring;
- required access, service behavior, fixture, dependency, or documentation is
  missing and cannot be established from the assigned environment;
- work is spreading through progressively broader files without converging on a
  bounded implementation;
- user changes overlap the task and cannot be preserved safely;
- a focused correction reproduces the same failure without new evidence.

When escalating, name the exact unresolved fact/decision, evidence inspected,
and what would unblock the work. Do not repeatedly retry the same approach.

Run focused tests while iterating and the agreed checks before handoff. Add a
meaningful regression check for changed behavior; use TDD when required. Prefer
observable behavior over mock-only assertions. Avoid repeating a full suite after
every edit unless the task's impact warrants it.

Before handoff, self-review the actual diff:
- Completeness: every acceptance criterion implemented or explicitly reported as
  blocked/unverified; no requirement silently omitted.
- Scope: no unrequested feature, abstraction, dependency, or unrelated cleanup;
  YAGNI and existing project patterns preserved.
- Correctness: edge cases, error paths, trust/authorization/data-integrity
  boundaries considered where relevant.
- Quality: names match behavior, control flow is understandable, errors are not
  swallowed, types/contracts stay consistent, and touched code remains
  maintainable without speculative abstraction.
- Tests: changed behavior and important failure cases are actually asserted;
  tests are not passing merely because everything is mocked.
- Hygiene: review the complete diff for accidental generated files, debug code,
  secrets, stale comments, unexplained warnings introduced by the change, and
  unintended user-file modifications.

Fix issues found during self-review before reporting when they remain within the
approved task. Escalate instead of silently widening the brief.

Write [REPORT_FILE] with:
- acceptance criteria implemented and any unmet/unverified items;
- files changed and relevant preserved user changes;
- exact validation commands, outcomes, relevant output, and environment;
- candidate/tested revision;
- TDD RED/GREEN evidence when TDD was required;
- self-review findings and fixes;
- remaining risks, warnings, assumptions, or follow-up decisions.

After review fixes, append fresh evidence for the amended revision. Do not reuse
results from a pre-fix snapshot as proof of the new code.

Return at most 15 lines:
- DONE / DONE_WITH_CONCERNS / NEEDS_CONTEXT / BLOCKED;
- commit range;
- one-line validation summary;
- unresolved concerns or blocker details;
- report path.

DONE_WITH_CONCERNS requires the requested implementation to be complete. Use
NEEDS_CONTEXT for missing information/evidence and BLOCKED for incomplete work or
a decision outside the brief. Never silently produce work you do not trust.
```
