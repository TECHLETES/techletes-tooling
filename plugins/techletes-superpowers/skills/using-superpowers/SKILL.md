---
name: using-superpowers
description: Use when starting implementation work or deciding which development workflow fits a request with meaningful scope, risk, or uncertainty
---

<SUBAGENT-STOP>
If you were dispatched as a subagent to execute a specific task, ignore this skill.
</SUBAGENT-STOP>

## The Rule

Choose the smallest workflow that safely solves the request. Skills are tools, not ceremonies.

For a small, well-specified, low-risk change, inspect the relevant files, make the minimal edit, run the narrowest useful check, and report back. Do not invoke brainstorming, spec writing, plan writing, TDD, subagents, worktrees, or review skills merely because they exist.

Escalate only when a concrete signal warrants it:

| Signal | Add this workflow |
| --- | --- |
| Intent, UX, architecture, or requirements are materially unresolved | `brainstorming` |
| Multiple dependent implementation steps, cross-cutting changes, or high coordination cost | `writing-plans` |
| New behavior or a bug needs a durable regression check | `test-driven-development` or `systematic-debugging` |
| Independent tasks would benefit from separate context or parallel work | `subagent-driven-development` or `dispatching-parallel-agents` |
| Isolation, broad refactoring, or risky branch work is needed | `using-git-worktrees` |
| Review, security, or delivery is explicitly requested or warranted by risk | the matching review/security/finish skill |

When a user explicitly names a skill, use it unless it conflicts with a higher-priority instruction. When a skill is required, announce it briefly and follow only the applicable parts; do not manufacture extra gates.

## Skill Priority

When multiple skills apply, use the minimum compatible set. Process skills may shape implementation, but they do not automatically imply every other process skill.

- "Let's build X" → use brainstorming only if the request leaves important design decisions unresolved; otherwise implement directly or write a plan if it is genuinely multi-step.
- "Fix this bug" → techletes-superpowers:systematic-debugging first, then domain skills.

## Red Flags

These thoughts mean STOP—you're rationalizing:

| Thought | Reality |
|---------|---------|
| "This is just a simple question" | Answer it directly unless a named skill or external lookup is required. |
| "I need more context first" | Inspect only the context needed to make a safe decision. |
| "Let me explore the codebase first" | Explore the relevant area; do not map the whole repository by default. |
| "I can check git/files quickly" | Read-only inspection is part of solving the task, not a reason to start a workflow. |
| "Let me gather information first" | Gather only information that changes the implementation or risk decision. |
| "This doesn't need a formal skill" | Correct when the task is small, clear, and low-risk. |
| "I remember this skill" | Skills evolve. Read current version. |
| "This doesn't count as a task" | Action = task. Check for skills. |
| "The skill is overkill" | Check the escalation signals; skip it when none apply. |
| "I'll just do this one thing first" | For low-risk work, that may be the correct workflow. |
| "This feels productive" | Prefer the smallest useful change and a concrete check. |
| "I know what that means" | Knowing the concept ≠ using the skill. Invoke it. |

## Platform Adaptation

If your harness appears here, read its reference file for special instructions:

- Codex: `references/codex-tools.md`
- Pi: `references/pi-tools.md`
- Antigravity: `references/antigravity-tools.md`

## User Instructions

User instructions (CLAUDE.md, AGENTS.md, GEMINI.md, etc, direct requests) take precedence over skills, which in turn override default behavior. A skill's hard gate applies only when its escalation signal is present or the user explicitly requests it.
