# Escalation and retry policy

Use this when a worker reports uncertainty, a correction fails, or implementation
starts widening beyond its brief. Escalation is a change in evidence, scope,
approach, or capability — not simply another identical attempt.

## First classify the problem

- **Missing evidence or access:** required file, credential, service, fixture,
documentation, or reproducible environment is unavailable. Repair the evidence or
environment first; more reasoning does not create missing facts.
- **Contract ambiguity:** requirements, tests, interfaces, or acceptance criteria
conflict or leave a material behavior unspecified. Return the decision to the
coordinator; do not let a worker silently choose a product or architecture policy.
- **Bounded reasoning difficulty:** the contract is clear but the implementation
logic is genuinely difficult. Increase worker reasoning using the routing policy.
- **Scope/architecture drift:** the task now requires a public API/schema change,
migration, deployment behavior, broad restructuring, or a new cross-component
contract that was not approved. Stop implementation and re-plan that decision.
- **Execution failure:** the chosen approach is wrong, a test still fails, or a
fix introduced another defect. Use the failure as new evidence before retrying.

## Concrete worker stop signals

A worker should stop and report `NEEDS_CONTEXT` or `BLOCKED` when any of these is
true:

- multiple materially different architecture choices remain and the brief does
  not decide between them;
- expected behavior in requirements and tests conflicts;
- a required interface, migration, environment variable, dependency, or external
  service behavior is unspecified or unavailable;
- completing the task requires changes outside the owned scope that are not a
  small, obvious integration edit;
- the planned file/interface structure no longer fits the codebase and meaningful
  restructuring would be required;
- the worker is reading progressively broader parts of the repository without
  converging on a bounded implementation;
- a focused correction reproduces the same failure without new evidence;
- user changes overlap the task in a way that cannot be preserved safely.

Uncertainty alone is not a blocker. The worker should name the exact unresolved
fact or decision and the evidence already inspected.

## Retry policy

For a focused review finding, prefer one correction in the existing worker
context when its model/effort remains appropriate. Require fresh validation on
the amended revision.

If that correction fails on the same issue without materially new evidence, do
not loop. Choose one of:

1. obtain missing evidence or repair the environment;
2. narrow or split the task at a real contract boundary;
3. change the implementation approach;
4. escalate Luna medium -> high -> xhigh for a clear bounded problem;
5. return an ambiguous/cross-cutting decision to the coordinator and, when
   warranted, the stronger planning role;
6. use a stronger implementation-capable model only through an explicitly
   supported role/configuration.

Do not use a read-only planner or reviewer as a hidden writer. Do not widen
permissions merely to make delegation succeed. Record the reason for escalation
and the evidence that triggered it in the task report/progress ledger.
