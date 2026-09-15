---
name: finishing-a-development-branch
description: Verify and deliver completed branch work through the user's chosen PR, merge, or handoff action while respecting actual PR bases, stacked dependencies, and workspace ownership.
---

# Finishing a Development Branch

Verify the candidate, determine the actual delivery base, execute the authorized
action, and report evidence. Do not add a delivery menu when the user already
requested a PR, a local merge, or keeping the branch. Ask only when that choice
is genuinely missing. A request to open a PR does not authorize merging it.

## Verify the final candidate

Inspect status and the actual diff, including untracked/deleted files and any
user edits authorized for inclusion. Preserve unrelated work. Run the smallest
checks covering the final change plus broader integration checks when impact
warrants them. Use repository commands and existing package managers.

Reuse earlier evidence only when the code, environment, and required scope
match. Re-run affected checks after fixes. Complete the independent review
required by the implementation workflow; do not duplicate an identical review
of the same final revision and scope. State unavailable review capabilities.

Unresolved correctness/security issues block a clean completion claim. Do not
claim ready-to-merge with failing or unavailable required checks. If delivery was
requested, a draft PR may preserve work with those limitations prominently
reported; never misrepresent it as verified. Do not merge failing changes.

## Detect workspace and base

Inspect branch, working tree, and actual environment restrictions:

```bash
git status --short
git branch --show-current
git rev-parse --git-dir
git rev-parse --git-common-dir
```

A detached HEAD does not by itself prove that branch creation is prohibited.
Honor host restrictions; if they prevent delivery, preserve commits and provide
the supported handoff instead of claiming a successful push or PR.

For an existing PR, inspect its current base:

```bash
gh pr view --json number,headRefName,baseRefName,state
```

For a new PR, use the explicitly requested base, then the plan's Delivery section,
then the repository's integration policy (Techletes default: staging). A dependent
stacked child targets its direct parent feature branch. Confirm parent state and
branch through GitHub, not a name guess. Resolve conflicts between explicit
instructions and an existing PR before retargeting it.

Fetch and validate the intended base. Review the branch against its merge-base
with that actual target, not automatically against main or HEAD~1.

## Execute the chosen action

**Create/update a PR:** commit authorized changes, push the feature branch, and
create the PR against the determined base (or update the existing PR). Include
scope, validation/results, limitations, and issue/dependency references. Preserve
the branch/worktree for feedback. Do not enable auto-merge or merge the PR.

```bash
git push -u origin <feature-branch>
gh pr create --base <actual-base> --head <feature-branch>
```

**Merge locally:** only when explicitly selected, update the base without
clobbering work, merge the feature branch, and verify the integrated result.
Cleanup is allowed only after successful merge and verification.

**Keep:** report branch, revision, and workspace; leave them intact.

**Discard:** show the exact branch, commits, and files/worktree that would be
lost, and require explicit confirmation for that deletion. Never infer discard
permission from a request to finish, clean up, or create a PR.

Use an authorized GitHub connector if gh is unavailable; describe actual
capability limitations instead of inventing CLI execution.

## Stacked PR lifecycle

Record the parent PR and explain that review is child-specific against its direct
parent branch. Merge bottom-up; never combine unrelated issues just to avoid a
stack. While both PRs are reviewed, merge parent updates into the child instead
of repeatedly rebasing reviewed history.

After the parent merges, fetch the actual integration branch and recompute the
child range. A merge preserving parent commits may need only retargeting. After
a squash merge, replay only child-specific commits:

```bash
git rebase --onto origin/<integration-branch> <verified-parent-tip> <child-branch>
git push --force-with-lease
gh pr edit --base <integration-branch>
```

Record/verify the parent's tip before its branch disappears; do not guess the
boundary or use an unrelated newer parent tip. Validate the new diff and rerun
checks affected by restacking. Never use plain --force. Limit history rewriting
to a deliberate post-parent restack or explicit authorization.

## Cleanup and report

A directory named `.worktrees/` does not prove ownership. Remove only a worktree
this run demonstrably created, when cleanup was authorized and needed after a
successful local merge or explicitly confirmed discard. Never remove a
host-managed or pre-existing workspace. Check for user/dirty work first. Leave
PR and keep-as-is worktrees intact.

Move outside an owned worktree before removal, remove it before deleting its
branch, and never use forced removal to bypass uncommitted changes. Report what
changed, validation actually performed, limitations, and the resulting PR or
handoff. Do not claim a remote action succeeded without its returned result.
