# Validation and handoff evidence

Use this for task acceptance, corrections, milestone reviews, and final review.
The purpose is to make evidence reusable without treating stale or partial test
claims as proof of a different revision.

## Minimum implementation evidence

A worker report must identify:

- exact candidate revision or commit range;
- files changed and any relevant user changes preserved;
- each validation command actually run;
- command outcome plus the relevant failure/pass output;
- environment details that materially affect the result;
- acceptance criteria covered by those checks;
- untested, partially tested, or externally blocked requirements;
- warnings/noise introduced by the change or otherwise relevant to correctness.

When TDD is required, record RED and GREEN evidence for the behavior under test.
Do not manufacture RED evidence after the implementation already exists.

## Reusing evidence

Reuse a prior result only when all material inputs still match:

- tested code/revision has not changed in the affected area;
- dependency/configuration/environment assumptions remain compatible;
- command scope covers the acceptance criterion now being evaluated;
- no later change invalidated the result.

After a correction, rerun the focused checks that cover the amended behavior.
Broader unchanged suites do not need ritual repetition unless the correction can
affect them. At phase/final integration gates, run the broader checks justified
by the combined impact.

## Review evidence

A reviewer receives requirements/constraints, the exact base/head, the diff or
review package, relevant integration boundaries, and the implementation report.
The reviewer should inspect requirements and code before relying on the report's
claims. A committed-range diff excludes uncommitted and untracked work; the
controller must account for those separately before acceptance.

A reviewer may inspect unchanged callers, complete functions, migrations,
configuration, or tests when needed to resolve a concrete risk. Do not restrict a
reviewer to context lines when correctness depends on surrounding behavior.

If a requirement cannot be verified, report it explicitly as unverified and name
the focused check or evidence needed. Do not convert missing evidence into a clean
verdict. Passing tests do not prove spec compliance, architecture correctness, or
security boundaries.

## Acceptance record

For every accepted substantive task or phase, record in the progress ledger:

- base/head or accepted commit range;
- worker role/model/effort used;
- validation commands and tested revision;
- review mode: parent or independent;
- spec-compliance and quality verdicts;
- Critical/Important findings resolved;
- Minor findings intentionally deferred;
- remaining limitations and next authorized action.

Claims such as "independently reviewed", "all tests pass", or a specific model
configuration must be backed by observable session/tool evidence. If the client
does not expose a setting, state that limitation instead of claiming it was
verified.
