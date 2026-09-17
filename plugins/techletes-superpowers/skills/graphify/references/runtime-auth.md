# Graphify runtime and authentication

Graphify does **not** require an external model API key when it is used through the Techletes `/graphify` skill inside Codex.

## Codex / skill mode

When Codex invokes `/graphify`:

- Code structure is extracted locally with Graphify/tree-sitter AST tooling.
- Semantic extraction for docs, PDFs, images, and mixed corpora is performed by the active Codex session and its subagents.
- The user's existing Codex authentication/model access is the model runtime. Do not require `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`, or another provider key before using the skill.
- A missing provider API key is **not** a reason to declare Graphify unavailable, skip it, or fall back to broad grep/codebase reads.

A code-only corpus can be graphed fully locally without any model API key. Existing `graphify-out/` graphs can also be queried locally without a provider key.

## When provider credentials are actually needed

Provider credentials apply to the separate **headless CLI extraction** workflow, for example `graphify extract --backend openai`, where Graphify itself calls a model provider outside the assistant session. CI/headless use may therefore require the selected backend's credentials or another supported local/provider runtime.

This is different from the Techletes Codex skill workflow and must not be used as a prerequisite for normal `/graphify` usage.

## Failure handling

If Graphify cannot run in Codex:

1. Check whether the `graphify` CLI/package is installed; install/refresh `graphifyy` if needed.
2. Check whether Codex multi-agent support is available when semantic extraction is needed.
3. For a code-only repository, continue with local AST extraction even if semantic subagents are unavailable.
4. Only ask for a provider API key when the user explicitly requested headless `graphify extract` with a backend that needs one.

Source behavior was verified against the current Graphify documentation: normal assistant-skill usage needs no extra API key; keys are documented for headless/CI extraction only.
