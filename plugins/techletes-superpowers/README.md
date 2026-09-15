# Techletes Superpowers

Lean development workflows for Techletes coding agents. Start with the smallest
workflow that resolves the task; use planning, delegation, and independent review
where their cost is justified by uncertainty or impact.

## Version 0.3.0

The shared [model-routing policy](skills/subagent-driven-development/references/model-routing.md)
replaces the fixed Luna-medium-for-everything rule. It keeps ordinary coordination
on Terra medium, uses Luna medium/high/xhigh for increasingly difficult bounded
work, and reserves Terra/Sol review and Sol planning for appropriate risks.
These are tunable starting choices, not measured optimal settings.

Plans specify outcomes, contracts, and acceptance criteria rather than a second
copy of implementation code. Execution respects explicit one-phase/through-end
approval, resumes from reconciled progress, reuses workers for corrections, and
uses sequential writers by default. Reviews start from requirements and actual
changes, with revision-matched validation evidence and proportionate gates.

## Native Codex roles

See [Codex setup](codex/README.md). The included installer copies seven namespaced
TOML roles without changing config.toml, AGENTS.md, credentials, or permissions.
Existing customized roles are preserved unless explicitly replaced with backups.
Plugin installation alone does not register these native roles. Legacy
`agents/*.agent.md` files remain host-specific instructions, not Codex settings.

## Verification

```bash
uv run --no-project --python 3.11 -m unittest discover -s plugins/techletes-superpowers/tests -v
```

Run from the tooling repository root. Tests cover configuration, installer safety,
workflow contracts, and handoff scripts. They do not exercise paid model calls or
prove the effective settings/account access of an installed Codex CLI.
