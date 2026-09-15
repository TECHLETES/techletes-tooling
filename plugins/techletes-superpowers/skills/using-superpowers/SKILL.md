---
name: using-superpowers
description: Choose the smallest development workflow for implementation requests with meaningful scope, risk, or uncertainty, without unnecessary planning or delegation ceremonies.
---

# Using Superpowers

A child assigned a bounded task should follow its brief and applicable technical
skills, not restart top-level workflow selection or delegate recursively.

For a small, clear, low-risk change, inspect the relevant code, edit locally, run
the narrowest useful check, and report. Do not invoke brainstorming, plan writing,
worktrees, TDD, subagents, or independent review simply because they exist.

| Concrete signal | Workflow to add |
| --- | --- |
| Materially unresolved intent, UX, architecture, or requirements | brainstorming |
| Dependent steps, shared interfaces, or cross-cutting scope | writing-plans |
| Unclear failures | systematic-debugging |
| New behavior or regression risk | meaningful check / test-driven-development |
| Approved multi-step work benefits from bounded contexts | subagent-driven-development |
| Genuinely independent investigations or isolated work | dispatching-parallel-agents |
| Workspace isolation is necessary | using-git-worktrees |
| Substantive/risky milestone or final delivery | requesting-code-review / finishing-a-development-branch |

Use the minimum compatible skills. Read the current version before relying on
its instructions. A skill does not automatically require every other process
skill. Read only context that can change the implementation or risk decision.

Use [shared routing](../subagent-driven-development/references/model-routing.md)
for delegated work, not a universal worker model. Existing explicit approval to
execute or continue an approved plan is sufficient. Preserve plan-only and
one-phase boundaries; do not invent unlimited authorization or redundant gates.

When the user names a skill, use it within higher-priority and explicit user
constraints. State unavailable tools or review capabilities rather than claiming
an unperformed step. For Codex, read [tool adaptation](references/codex-tools.md).
Other harness references remain available in `references/` when applicable.
