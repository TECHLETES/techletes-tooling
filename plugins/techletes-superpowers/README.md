# Techletes Superpowers

Lean software delivery workflows for Codex and other coding-agent hosts.

## Version 0.3.1

- Codex workflows now explicitly require the V2 subagent interface with both
  `multi_agent = true` and `multi_agent_v2 = true`; restart Codex and start a
  new session after changing the feature flags.
- Shared role-based model/effort routing instead of forcing every child to Luna
  medium. Routine workers stay medium; substantive work uses high; bounded hard
  problems can use xhigh. Independent review uses Terra high, with Sol high for
  consequential planning/review. These are starting policies, not measured optima.
- Sequential writers by default, compact file handoffs, focused correction reuse,
  explicit escalation, revision-matched evidence, and risk-based review gates.
- Resume-aware phase execution with explicit plan-only/one-phase/through-end
  boundaries, scoped commits, and no repeated approval or delivery menus.
- Native Codex roles and a non-destructive installer; legacy host definitions no
  longer impose conflicting model, parallelism, or full-rewrite instructions.

## Setup and entry points

Install the plugin using the existing marketplace configuration. For executable
Codex role settings, follow [Codex setup](codex/README.md): installing skills alone
does not install those role files or turn this plugin's AGENTS.md into global
instructions. Existing custom roles are never silently overwritten.

Use [workflow selection](skills/using-superpowers/SKILL.md) for a new request,
[planning](skills/writing-plans/SKILL.md) for coordinated changes, and
[phased execution](skills/subagent-driven-development/SKILL.md) for approved work.
The [routing policy](skills/subagent-driven-development/references/model-routing.md)
is the shared source for role selection and escalation.

Explicit user choices and project-specific constraints override the defaults.
This release does not rewrite application-specific plans/runbooks or historical
progress ledgers, change authentication/permissions, or merge any PR.

## Validation

```bash
uv run --no-project --python 3.11 -m unittest discover -s plugins/techletes-superpowers/tests -v
```

The offline tests exercise installer safety, role settings, documentation links,
workflow entrypoints, and handoff scripts in temporary Git repositories. CI runs
on Python 3.11 and 3.13. These checks do not measure model quality or prove that
your local Codex version/account can load and run every role; perform the setup
smoke test before relying on the runtime configuration.
