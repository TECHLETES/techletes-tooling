# Implementer handoff

Select the configured role using [model-routing.md](references/model-routing.md).
This is a prompt template, not a dispatch API schema. Use only fields supported
by the current client and do not leave placeholders in a real dispatch.

```text
Implement Task [N]: [objective].
Role: [configured worker role]; model/effort: [actual selected settings].
Work only in [absolute checkout path]. Do not spawn children.

Read [BRIEF_FILE] first: it is the source of requirements, non-goals, owned
paths, global constraints, interfaces, acceptance criteria, and validation.
Relevant prior decisions/interfaces not already in the brief: [only essentials].
Starting revision: [TASK_BASE]. Report file: [REPORT_FILE].
Commit scope: [owned changes, or explicit user-authorized all-changes policy].

Implement the smallest change following existing patterns. Inspect additional
code when needed, but do not expand scope or invent unresolved contracts.
Preserve user changes. Do not push, merge, switch branches, or widen permissions.
Return NEEDS_CONTEXT for missing evidence; return BLOCKED for a concrete blocker
or an architectural decision outside this brief. Explain what you tried and
what evidence/decision is needed. Do not keep retrying the same failed approach.

Run focused tests while iterating and the agreed checks before handoff. Add a
regression check for changed behavior; use TDD when required. Self-review the
actual diff, fix issues, and commit within the authorized scope. Avoid full-suite
repetition unless the scope or changed evidence warrants it.

Write [REPORT_FILE] with implemented acceptance criteria, files changed, commands,
outcomes and relevant output, environment, tested revision, self-review findings,
and remaining risks/requirements. Include red/green evidence when TDD is required.
After fixes, append updated evidence and the new tested revision; do not reuse
results from a pre-fix snapshot as proof of the amended code.

Return at most 15 lines: DONE / DONE_WITH_CONCERNS / NEEDS_CONTEXT / BLOCKED,
commit range, one-line test summary, unresolved concerns, and report path.
DONE_WITH_CONCERNS requires the requested implementation to be complete; use
BLOCKED for incomplete work. Include actionable blocker details in the response.
```
