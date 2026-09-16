# Codex CLI setup

The plugin supplies skills; native custom agents are a separate Codex
configuration surface. Do not assume installing the plugin loads the legacy
`agents/*.agent.md` descriptions, these TOML files, or the plugin's `AGENTS.md`
as global instructions. Invoke the plugin skill explicitly, or add the relevant
workflow entry point to your project's AGENTS.md using your normal setup.

## Enable the V2 subagent system

The Techletes workflows target Codex's V2 subagent interface. Enable both
multi-agent flags in `$CODEX_HOME/config.toml` (normally `~/.codex/config.toml`):

```toml
[features]
multi_agent = true
multi_agent_v2 = true
```

`multi_agent = true` on its own can leave the session on the legacy V1 tool
interface even when the selected model's catalog entry advertises V2. Restart
Codex and start a new session after changing the feature flags. Verify the live
session exposes V2 before relying on delegation.

The role installer below intentionally does not edit `config.toml`; user-level
Codex feature flags remain an explicit one-time setup step.

## Install the native roles

Requires Python 3.11+ and a Codex CLI supporting standalone custom-agent TOML
files. Run from a checkout of techletes-tooling (or use the installed plugin's
absolute path). The installer does not change your model default, config.toml,
AGENTS.md, authentication, tools, or permissions.

```bash
uv run --no-project --python 3.11 plugins/techletes-superpowers/codex/install-agents.py --dry-run
uv run --no-project --python 3.11 plugins/techletes-superpowers/codex/install-agents.py
```

The default destination is `$CODEX_HOME/agents`, or `~/.codex/agents` when
CODEX_HOME is unset. For repository-scoped roles, pass the target project's
`.codex/agents` directory explicitly with `--destination`. Do not overwrite a
whole Codex configuration to install roles.

Rerunning is a no-op for identical files. Conflicting files are not overwritten
unless `--overwrite` is supplied; replacements get uniquely named `.bak` backups.
Review changes before replacing customized roles. After a plugin update, rerun
the installer and restart Codex so installed copies do not stay stale.

## Start the main session

```bash
codex --model gpt-5.6-terra -c 'model_reasoning_effort="medium"'
```

This chooses the coordinator, not the child agents. Your explicit model choice
still wins over the workflow's recommendation. The routing policy and role
purposes are in
[model-routing.md](../skills/subagent-driven-development/references/model-routing.md).

Codex also exposes `[agents]` configuration such as the session thread cap. The
V2 feature flags above control which subagent tool interface this workflow
expects; do not infer V2 merely from a model catalog entry. Check the installed
version and live tool availability. No permission relaxation is required or
supplied by this bundle.

Exploration, planning, and review roles request a read-only sandbox and also
carry explicit no-mutation instructions. Codex can reapply the parent turn's
live permission overrides, so do not treat the role file as an unchangeable
security boundary. Worker roles inherit the existing sandbox; none relax it.

Before relying on the workflow, confirm that the named roles appear in Codex and
run a narrow read-only exploration/review smoke test. Confirm the child model,
effort, and V2 tool interface in session metadata when available. Static tests
cannot verify your account's model access or a particular CLI's runtime behavior.

## Validate this bundle

```bash
uv run --no-project --python 3.11 -m unittest discover -s plugins/techletes-superpowers/tests -v
```

This checks role settings, installer safety, workflow contracts, and the actual
handoff scripts in temporary Git repositories. It makes no paid model calls.

Sources: [custom agents](https://developers.openai.com/codex/subagents) and
[configuration reference](https://developers.openai.com/codex/config-reference),
checked 2026-09-16.
