---
name: dispatching-parallel-agents
description: Coordinate genuinely independent investigations or implementation tasks when separate contexts or parallel work outweigh handoff and integration costs.
---

# Dispatching Parallel Agents

Use [shared routing](../subagent-driven-development/references/model-routing.md)
and the authorization/evidence rules in
[subagent-driven-development](../subagent-driven-development/SKILL.md).
Parallelism is optional, not an objective. Keep dependent implementation
sequential and do small tasks inline.

## Establish independence

Different files, components, or test failures do not prove independence. Check
shared interfaces, dependencies, lockfiles, migrations, databases, ports, and
other mutable resources. Related failures may have one root cause: investigate
together before splitting them.

Parallel read-only questions may share a checkout only while the inspected
revision is stable; pin a commit or isolated snapshot if a writer is active.
Parallel writers MUST have separately assigned Git worktrees and isolated mutable
resources, agreed contracts, and a clear integration order. Never run concurrent
writers in the same checkout, even with different file assignments.

## Dispatch and integrate

Give each child a bounded goal, non-goals, relevant evidence, owned paths,
absolute checkout, acceptance criteria, validation commands, and report path.
Select an actual configured model/effort from the shared policy. Do not pass the
full session history, spawn children recursively, or widen permissions.

Use the client's actual concurrency controls; several textual instructions do
not prove concurrent execution. Do not exceed its thread/resource limits. The
main session retains integration and branch ownership.

Read reports and actual diffs, check contracts/conflicts, integrate in dependency
order, then run the checks justified by the combined impact. Independent passing
tasks do not prove the integrated result works. Request risk-appropriate review
on the combined candidate and resolve findings before acceptance.

Reuse suitable workers for focused corrections and close finished threads.
Report observed checks and limitations; do not invent speedup or cost savings.
