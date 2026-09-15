# Techletes Tooling Agent Instructions

This repository contains the source for Techletes plugins and skills.

## Scope

- Make skill changes in `plugins/`, not in cached copies or generated output.
- When modifying a skill or plugin, bump the plugin version appropriately as
  part of the same change.
- This repository integrates through `main`; create a separate branch and PR.

## General Rules

- Follow the existing repository and plugin conventions.
- Keep edits minimal and localized.
- Prefer changing the source of truth over patching derived artifacts.
- For plugin changes, run `uv run --no-project --python 3.11 -m unittest discover
  -s plugins/techletes-superpowers/tests -v` and inspect the actual diff.
- Native Codex role sources live in the plugin's `codex/agents/` directory.
  Do not edit installed copies or treat legacy `.agent.md` files as native roles.
- Application-specific runbooks and historical progress ledgers are not shared
  plugin policy; do not rewrite them as part of a plugin-only change.
