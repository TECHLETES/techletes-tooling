---
name: finishing-a-development-branch
description: Verify and deliver completed branch work through the user's chosen PR, merge, or handoff action while respecting actual PR bases, stacked dependencies, and workspace ownership.
---

# Finishing a Development Branch

Verify the candidate, determine the actual delivery base, execute the authorized
action, and report evidence. Do not add a delivery menu when the user already
requested a PR, a local merge, or keeping the branch. Ask only when that choice
is genuinely missing. A request to open a PR does not authorize merging it.

Before any local merge, discard, worktree cleanup, branch deletion, or history
rewrite/restack, read and follow [git-safety.md](references/git-safety.md). Keep
those deterministic safeguards even when the higher-level delivery choice is
already authorized.

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

**Merge locally:** only when explicitly selected. Follow the exact local-merge
sequence in [git-safety.md](references/git-safety.md), verify the integrated
result, and clean up only after successful verification.

**Keep:** report branch, revision, and workspace; leave them intact.

**Discard:** follow the explicit-impact and confirmation procedure in
[git-safety.md](references/git-safety.md). Never infer discard permission from a
request to finish, clean up, or create a PR.

Use an authorized GitHub connector if gh is unavailable; describe actual
capability limitations instead of inventing CLI execution.

## Stacked PR lifecycle

Record the parent PR and explain that review is child-specific against its direct
parent branch. Merge bottom-up; never combine unrelated issues just to avoid a
stack. While both PRs are reviewed, merge parent updates into the child instead
of repeatedly rebasing reviewed history.

After the parent merges, fetch the actual integration branch and recompute the
child range. A merge preserving parent commits may need only retargeting. For a
squash-merged parent or any history rewrite, follow the verified-boundary and
`--force-with-lease` procedure in [git-safety.md](references/git-safety.md).

Validate the new diff and rerun checks affected by restacking before claiming the
child PR is ready.

## Cleanup and report

Only clean up a worktree this run demonstrably owns, and only when the chosen
action no longer needs it. Follow [git-safety.md](references/git-safety.md) for
status checks, moving outside the worktree, removal order, pruning, and branch
deletion. Never force cleanup through user changes or remove a host-managed,
pre-existing, or ownership-ambiguous workspace.

Report what changed, validation actually performed, limitations, and the resulting
PR or handoff. Do not claim a remote action succeeded without its returned result.
