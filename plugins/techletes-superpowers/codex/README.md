# Codex CLI setup

The plugin supplies skills; native custom agents are a separate Codex
configuration surface. Do not assume installing the plugin loads the legacy
`agents/*.agent.md` descriptions, these TOML files, or the plugin's `AGENTS.md`
as global instructions. Invoke the plugin skill explicitly, or add the relevant
workflow entry point to your project's AGENTS.md using your normal setup.

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

Current Codex documents `[agents] enabled = true` (the default) and
`max_concurrent_threads_per_session` for the thread cap. An older client may use
`[features] multi_agent = true`. Check your installed version and exposed tools;
do not claim an unsupported configuration enabled delegation. No permission
relaxation is required or supplied by this bundle.

Exploration, planning, and review roles request a read-only sandbox and also
carry explicit no-mutation instructions. Codex can reapply the parent turn's
live permission overrides, so do not treat the role file as an unchangeable
security boundary. Worker roles inherit the existing sandbox; none relax it.

Before relying on the workflow, confirm that the named roles appear in Codex and
run a narrow read-only exploration/review smoke test. Confirm the child model
and effort in session metadata when available. Static tests cannot verify your
account's model access or a particular CLI's runtime behavior.

## Validate this bundle

```bash
uv run --no-project --python 3.11 -m unittest discover -s plugins/techletes-superpowers/tests -v
```

This checks role settings, installer safety, workflow contracts, and the actual
handoff scripts in temporary Git repositories. It makes no paid model calls.

Sources: [custom agents](https://developers.openai.com/codex/subagents) and
[configuration reference](https://developers.openai.com/codex/config-reference),
checked 2026-09-15.
