# Codex tool adaptation

Use the tools exposed by the installed client; do not invent dispatch arguments
or assume a tool name from another harness. Current Codex supports standalone
custom-agent TOML files. See [native role setup](../../../codex/README.md) and
[shared routing](../../subagent-driven-development/references/model-routing.md).

The plugin's legacy `agents/*.agent.md` files are not native Codex configuration.
Installing skills alone does not install the TOML roles or global AGENTS.md.
Set both `model` and `model_reasoning_effort` in each native role; choose the
matching installed role at dispatch instead of relying on inherited defaults.
Confirm effective settings when session metadata exposes them.

Current configuration uses `[agents] enabled = true` (default). Older clients
may use `[features] multi_agent = true`; verify the installed version and tool
availability rather than claiming an unsupported toggle enabled delegation.
Keep workers alive for focused corrections, then close completed child threads.
Do not let delegation change the existing sandbox or approval policy.

## Environment and delivery

Inspect Git state before creating or cleaning up a workspace:

```bash
GIT_DIR=$(cd "$(git rev-parse --git-dir)" && pwd -P)
GIT_COMMON=$(cd "$(git rev-parse --git-common-dir)" && pwd -P)
BRANCH=$(git branch --show-current)
```

Different Git/common directories identify a linked worktree. A blank branch
means detached HEAD, not proof that every branch/push operation is forbidden.
Use actual errors and host constraints to determine permitted delivery.

Reuse an existing workspace for sequential work. Never remove a host-managed
worktree or infer ownership solely from its directory name. If the host blocks
branch/push/PR operations, preserve verified commits and provide the supported
native handoff action. Do not claim the PR was created when it was not.

Reference: [official Codex subagent documentation](https://developers.openai.com/codex/subagents),
checked 2026-09-15. Runtime model access and permissions still need a local smoke test.
