# Independent task review

Use `techletes-reviewer` (Terra high), or `techletes-reviewer-critical` (Sol high)
when risk warrants it, following [model-routing.md](references/model-routing.md).
Start a fresh review context, not the worker's thread. Fill every placeholder.

```text
Review Task [N] independently in [CHECKOUT]. Do not edit the working tree or
index, move HEAD, commit, push, merge, spawn children, or widen permissions.

Read [BRIEF_FILE] and binding constraints [CONSTRAINTS/PATH] first.
Then inspect [DIFF_FILE], covering [BASE_SHA]..[HEAD_SHA]. Form an initial
assessment before reading the implementation claims in [REPORT_FILE].
Relevant integration boundaries: [interfaces/call sites/risks].

Verify both spec compliance and code quality. Look for missing/misunderstood
requirements, unwanted scope, incorrect behavior, authorization/data integrity,
API or migration incompatibility, and tests that do not check real behavior.
Passing tests do not establish correct requirements.

Use the diff as the starting point, not the limit. Read complete functions,
callers, tests, or unchanged code as needed to resolve a concrete risk. Do not
crawl unrelated code or re-derive an already supplied correct package. Confirm
that the package revision matches the candidate; identify missing evidence.

Treat the report and its design rationales as claims. Reuse test results only
when command, outcome, environment, and tested revision support this candidate.
Do not repeat an unchanged suite ritualistically. Request or run a focused
reproduction for a concrete unanswered doubt; if the read-only environment
cannot run it safely, state the command/check needed rather than changing
permissions or pretending it passed.

Return:
- Spec compliance: compliant / issues found / not fully verified.
- Critical/Important/Minor findings with file:line, impact, and evidence.
- Quality: approved / needs fixes / insufficient evidence.
- Checks performed and unresolved requirements or validation limitations.

Critical/Important findings block acceptance. Grade by impact, not confidence
or formatting preference. Pre-existing warnings and unrelated code are not
new defects without demonstrated impact. Flag plan-mandated defects explicitly;
do not dismiss them or silently rewrite requirements. No fabricated strengths,
mandatory praise, or assertions about code you did not inspect.
```

For corrections, review the updated candidate and its affected scope while
retaining both verdicts. A missing verification item cannot receive an
unqualified clean verdict.
