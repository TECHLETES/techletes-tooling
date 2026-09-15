# Whole-branch reviewer handoff

Select `techletes-reviewer` or `techletes-reviewer-critical` using
[model-routing.md](../subagent-driven-development/references/model-routing.md).
Use [validation evidence](../subagent-driven-development/references/evidence.md)
when judging prior checks. Fill the prompt below; do not treat it as an API schema.

```text
Independently review [BRANCH/PR] against [ACTUAL_BASE_BRANCH].
Base revision: [BASE_SHA]. Candidate revision: [HEAD_SHA].
Requirements/spec: [PATHS]. Binding constraints: [CONSTRAINTS/PATH].
Diff package: [DIFF_FILE]. Validation reports: [REPORT_PATHS].
Unresolved earlier findings: [LIST/PATH, or none].

Read requirements and actual changes before the implementation narrative.
Verify the package covers the final candidate and actual PR base. For a stacked
PR, judge only child-specific changes against its direct parent and do not report
unchanged parent code as a child defect.

Review the complete deliverable, not only syntax or changed lines:

Requirements and scope
- Is every required behavior, failure case, migration/config/documentation change,
  and explicit non-functional constraint present?
- Were unrequested features, abstractions, dependencies, or public contracts added?
- Are deviations from the plan/requirements actually justified, or do they change
  the requested outcome?

Correctness and maintainability
- Are control flow, edge cases, state transitions, concurrency/order, and error
  paths correct?
- Are responsibilities clear, names/types/contracts accurate, and error handling
  explicit rather than swallowed?
- Is the code DRY without premature abstraction or needless indirection?
- Did the change create an oversized/tangled unit or duplicate behavior that will
  predictably diverge?

Architecture and integration
- Does the design fit surrounding project patterns and cross-task interfaces?
- Are callers/consumers, performance/scalability characteristics, shared state,
  retries/idempotency, and resource lifecycle correct where relevant?
- Do schema/API/configuration changes have safe migration and rollout behavior?

Security and data safety
- Check authorization and tenant/client boundaries, secrets, input validation,
  data integrity, irreversible operations, injection/path traversal or similar
  trust-boundary risks when relevant.
- Check migration/rollback and data-loss behavior for stateful changes.

Compatibility and production readiness
- Are backward compatibility, deployment/config defaults, environment variables,
  feature flags, observability/logging, operational failure modes, and docs/help
  handled where the change affects them?
- Are cleanup/recovery paths safe and are destructive operations sufficiently
  guarded?

Testing and evidence
- Do tests assert observable behavior rather than merely mocks or implementation
  details?
- Are important edge/failure/integration cases covered at the right level?
- Would the regression test actually fail for the defect it claims to prevent?
- Are reported checks from the same revision, scope, and compatible environment?
- Passing tests do not establish requirement completeness, architecture, or
  security correctness.

Use the diff as the starting point, not a hard evidence boundary. Inspect complete
functions, callers, tests, migrations, configuration, and unchanged integrations
when needed to resolve a concrete risk. Do not crawl unrelated code without a
named reason.

Reuse validation only for a matching revision/scope/environment. State gaps and
request focused reproduction where evidence is missing or doubtful. Do not edit
the shared checkout/index, move HEAD, commit, push, merge, spawn children, or
widen permissions. If safe execution would require mutation, report the exact
isolated check instead. Do not rerun unrelated full suites by habit.

Severity:
- Critical: realistic security/data-loss/corruption risk, broken core behavior,
  or unsafe integration.
- Important: missed requirement, incorrect/fragile behavior, broken compatibility
  or interface, serious maintainability damage, or a test gap that blocks trust.
- Minor: low-risk polish, localized maintainability, optional documentation, or
  extra coverage that does not block integration.

For each finding provide file:line, what is wrong, why it matters, and a fix or
required decision when not obvious. Explicitly call out defects mandated by the
plan instead of assuming the plan makes them acceptable. Resolve or disposition
previous findings; do not silently drop them. Evidence-backed strengths may be
included briefly, but never fabricate praise.

Return:

### Spec Compliance
[Compliant | Issues found | Not fully verified]
[Missing/extra/misunderstood/unverified requirements]

### Issues
#### Critical
#### Important
#### Minor
[Evidence-backed findings; "None" where empty]

### Validation / Integration Checks
[Checks inspected/run, stale or missing evidence, unresolved integration risks]

### Assessment
**Ready to merge:** [Yes | No | With fixes | Insufficient evidence]
**Reasoning:** [concise technical assessment]

Review approval does not authorize a merge.
```
