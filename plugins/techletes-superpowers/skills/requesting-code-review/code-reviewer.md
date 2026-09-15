# Whole-branch reviewer handoff

Select `techletes-reviewer` or `techletes-reviewer-critical` using
[model-routing.md](../subagent-driven-development/references/model-routing.md).
Fill the prompt below; do not treat it as an API schema.

```text
Independently review [BRANCH/PR] against [ACTUAL_BASE_BRANCH].
Base revision: [BASE_SHA]. Candidate revision: [HEAD_SHA].
Requirements/spec: [PATHS]. Binding constraints: [CONSTRAINTS/PATH].
Diff package: [DIFF_FILE]. Validation reports: [REPORT_PATHS].
Unresolved earlier findings: [LIST/PATH, or none].

Read requirements and actual changes before the implementation narrative.
Inspect surrounding code, callers, and unchanged integrations when a concrete
risk requires it. Verify that the review package covers the final candidate and
actual PR base. Do not report unchanged parent-PR code as a new child-PR defect.

Check requirements, edge cases, security/tenant boundaries, data integrity,
compatibility, migrations/rollback, error handling, and test adequacy according
to impact. Trace cross-task interfaces. Passing tests do not establish correct
requirements, and isolated task checks do not prove final integration works.

Reuse reported validation only for a matching revision, scope, and environment.
State gaps and request focused reproduction where evidence is missing or doubtful.
Do not edit the shared checkout/index, move HEAD, commit, push, merge, spawn
children, or widen permissions. If execution would write to shared state, report
the needed isolated check instead. Do not run unrelated full suites by habit.

Return spec compliance, Critical/Important/Minor findings with file:line and
impact, checks actually performed, unverified requirements, and a quality verdict:
approved / needs fixes / insufficient evidence. Resolve or explicitly disposition
previous findings. Explain plan defects rather than grading them as correct merely
because the plan requested them. Do not fabricate strengths or assert knowledge
of code you did not inspect. Review approval does not authorize a merge.
```
