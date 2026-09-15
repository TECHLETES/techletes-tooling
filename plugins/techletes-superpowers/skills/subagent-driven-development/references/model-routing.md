# Model routing

This is the shared routing policy for Techletes workflows, not a benchmark claim
or a promise that one configuration is optimal. Explicit user choices, account
availability, budget caps, and repository constraints take precedence.

## Starting policy

| Work | Native Codex role | Model | Effort |
| --- | --- | --- | --- |
| Main-session coordination and ordinary planning | Main session, not a child | `gpt-5.6-terra` | `medium` |
| Narrow, read-only evidence gathering | `techletes-explorer` | `gpt-5.6-luna` | `medium` |
| Routine implementation using established patterns | `techletes-worker-routine` | `gpt-5.6-luna` | `medium` |
| Substantive, well-specified implementation | `techletes-worker` | `gpt-5.6-luna` | `high` |
| Difficult but bounded logic or debugging | `techletes-worker-deep` | `gpt-5.6-luna` | `xhigh` |
| Independent task, milestone, or final review | `techletes-reviewer` | `gpt-5.6-terra` | `high` |
| Ambiguous or consequential architecture decisions | `techletes-planner` | `gpt-5.6-sol` | `high` |
| Security-sensitive, destructive, or cross-cutting review | `techletes-reviewer-critical` | `gpt-5.6-sol` | `high` |

Do not use a planning agent merely to repeat an approved plan. Do not default all
workers to xhigh, or all reviewers to the worker's model. A small, clear change
can be implemented and checked inline without a child agent.

## Apply actual settings

Use the [native role sources](../../../codex/agents/) and
[installation instructions](../../../codex/README.md).
Select the installed role and inspect its effective model and effort when the
client exposes them. Role names in prose are not runtime configuration.

With a generic child, set both model and effort through fields actually exposed
by the dispatch tool. Do not invent a `reasoning_effort` argument when the tool
only accepts a role. Native TOML uses `model_reasoning_effort`. A custom agent
file's model/effort can take precedence over spawn settings: choose another
role or intentionally update its configuration rather than claiming an override
that did not happen. Writing "think harder" does not change configured effort.

Do not silently inherit a costly parent model, substitute an unavailable model,
or claim a configured setting was verified when it was not observable. State
what is unavailable. Use an explicitly configured supported role, or execute
inline when safe and consistent with the user's constraints. For unresolved
high-risk work, surface the missing capability or decision instead of presenting
an unverified result as reviewed. Never widen permissions to enable delegation.

## Escalate from evidence

- Missing requirements, files, credentials, or a broken test environment: repair
  the information/environment first. More reasoning does not supply evidence.
- Clear contract, difficult logic: move Luna medium -> high -> xhigh as needed;
  skip levels when the difficulty is already evident.
- Conflicting requirements, widening scope, cross-component failures, or a bad
  architecture assumption: return to the coordinator; use the planner for the
  unresolved decision instead of making a worker invent a new contract.
- After one focused correction still fails on the same issue without new
  evidence, change the approach, role, scope, or evidence. Do not repeat the same
  dispatch indefinitely. A failed high/xhigh attempt can justify a stronger
  implementation model through a supported explicit dispatch; do not misuse a
  read-only reviewer/planner as a writer.

Resume the existing worker for context answers and focused corrections when its
configuration remains suitable. Changing the role/model requires a new child;
pass only its brief, current diff, evidence, and unresolved issue. Use a fresh
context for independent review. Do not make routing depend on confidence alone.

## Measure before retuning

Record the role/model/effort, retries, substantive review findings, validation
result, and tested revision in the existing progress ledger/report. Record
usage, elapsed time, and human correction time only when available; never invent
them or substitute API list prices for subscription allowance consumption.

Compare total cost/time to an accepted change, including failed attempts and
review, on representative tasks from the same starting revision. Change one
routing choice at a time. Keep medium for work where high adds no observed value.

## Configuration references

Verified against official documentation on 2026-09-15; recheck when updating the
client or model identifiers:

- [Codex subagents](https://developers.openai.com/codex/subagents)
- [Codex configuration](https://developers.openai.com/codex/config-reference)
- [Luna](https://developers.openai.com/api/docs/models/gpt-5.6-luna)
- [Terra](https://developers.openai.com/api/docs/models/gpt-5.6-terra)
- [Sol](https://developers.openai.com/api/docs/models/gpt-5.6-sol)
