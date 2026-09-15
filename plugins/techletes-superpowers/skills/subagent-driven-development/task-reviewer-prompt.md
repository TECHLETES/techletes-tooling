# Independent task review

Use `techletes-reviewer` (Terra high), or `techletes-reviewer-critical` (Sol high)
when risk warrants it, following [model-routing.md](references/model-routing.md).
Use [evidence.md](references/evidence.md) for validation handling. Start a fresh
review context, not the worker's thread. Fill every placeholder.

```text
Review Task [N] independently in [CHECKOUT]. Do not edit the working tree or
index, move HEAD, commit, push, merge, spawn children, or widen permissions.

Read [BRIEF_FILE] and binding constraints [CONSTRAINTS/PATH] first.
Then inspect [DIFF_FILE], covering [BASE_SHA]..[HEAD_SHA]. Form an initial
assessment before reading implementation claims in [REPORT_FILE].
Relevant integration boundaries: [interfaces/call sites/risks].

Your job is to produce two separate verdicts: spec compliance and implementation
quality. Treat the report, test claims, and design rationale as unverified claims
until checked against the requirements and code.

Spec compliance:
- Missing: a requested behavior, constraint, failure case, migration, docs/update,
  or integration requirement is absent.
- Extra: unrequested behavior, dependency, abstraction, API, or scope was added.
- Misunderstood: the requested outcome exists but with materially wrong semantics.
- Unverified: a requirement cannot be established from the available evidence;
  name the focused check or context needed rather than assuming success.

Implementation quality:
- Correctness: edge cases, state transitions, concurrency/order, error paths, and
  data integrity are sound for the task's actual risk.
- Security/trust boundaries: authorization, tenant/client separation, secrets,
  input validation, and destructive operations are handled where relevant.
- Interfaces/compatibility: public APIs, types, schemas, migrations, config,
  callers, and backward compatibility stay coherent.
- Structure: responsibilities are understandable; no harmful duplication,
  speculative abstraction, deep indirection, or task-created oversized/tangled
  units without justification.
- Error handling/observability: failures are explicit and useful; errors are not
  swallowed; relevant logging/diagnostics remain adequate.
- Tests: changed observable behavior and important failure cases are asserted;
  tests do not merely validate mocks or implementation details; regression tests
  would fail for the bug/behavior they claim to protect.
- Scope/hygiene: no unrelated refactor, debug artifacts, secrets, accidental
  generated files, or unexplained warnings introduced by the change.

Use the diff as the starting point, not the limit. Read complete functions,
callers, tests, migrations, configuration, or unchanged code when needed to
resolve a concrete risk. Do not crawl unrelated code or re-derive an already
correct review package. Confirm that the package revision matches the candidate.

Reuse validation only when command, outcome, environment, scope, and tested
revision support this candidate. Do not rerun an unchanged suite by ritual. Run
or request a focused reproduction when code inspection raises a concrete doubt.
If the read-only environment cannot run it safely, state the exact check needed
rather than changing permissions or pretending it passed.

Severity calibration:
- Critical: realistic security/data-loss/corruption risk, broken core behavior,
  or a defect that makes the candidate unsafe to integrate.
- Important: missed requirement, incorrect/fragile behavior, broken interface,
  material maintainability problem, or meaningful test gap that blocks trust in
  this task.
- Minor: localized polish, low-risk maintainability improvement, or optional
  coverage/documentation improvement that does not block the task.

A plan-mandated defect is still a finding: label it as such so the coordinator
can resolve the requirement conflict. Do not downgrade an issue because the
worker intended it. Do not report pre-existing unrelated problems as new task
findings without demonstrating impact from this change.

For every finding give file:line, what is wrong, why it matters, and the fix or
required decision when not obvious. Evidence-backed strengths may be noted, but
do not fabricate praise or spend output on generic positives.

Return exactly these sections:

### Spec Compliance
[Compliant | Issues found | Not fully verified]
[Missing/extra/misunderstood/unverified items with file:line or required check]

### Issues
#### Critical
#### Important
#### Minor
[Findings with evidence; write "None" for an empty severity]

### Validation / Checks
[What you inspected or ran; stale/missing evidence and limitations]

### Assessment
**Task quality:** [Approved | Needs fixes | Insufficient evidence]
**Reasoning:** [concise technical reason]

Critical/Important findings block acceptance. A missing verification item cannot
receive an unqualified clean verdict.
```

For corrections, review the updated candidate and affected scope while retaining
both verdicts. Verify covering tests/evidence correspond to the amended revision;
do not treat the previous clean areas as permission to ignore regressions caused
by the fix.
