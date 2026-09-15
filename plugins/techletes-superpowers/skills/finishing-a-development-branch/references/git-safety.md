# Git safety procedures

Use this reference only when finishing work involves a local merge, discard,
worktree cleanup, force-with-lease restack, or branch deletion. These operations
are intentionally more prescriptive than the normal workflow.

## Before destructive or history-changing operations

Record and inspect:

```bash
git status --short
git branch --show-current
git rev-parse HEAD
git rev-parse --show-toplevel
git worktree list --porcelain
```

Confirm the exact branch, candidate revision, target base, dirty/untracked files,
and whether this run demonstrably created the worktree being considered for
cleanup. A directory name alone is not proof of ownership. Do not stash, reset,
clean, or revert user changes to make the state convenient.

## Local merge

Only execute after explicit local-merge authorization and successful candidate
validation.

1. Determine the actual target base from the PR/plan/repository policy.
2. Move to the main repository checkout; never remove or switch away from a
   worktree while the shell is inside a worktree that may later be deleted.
3. Fetch the target branch and update it safely. Avoid overwriting local changes.
4. Merge the feature branch without deleting either branch first.
5. Run the required integration checks on the merged result.
6. Only after the merge and checks succeed may owned-worktree cleanup or branch
   deletion occur.

If the target checkout is dirty or cannot be updated without risking user work,
stop and report the conflict rather than resetting it.

## Discard

Discard is destructive and always requires an explicit confirmation after the
exact impact is shown. Present the branch/worktree and commit range plus any
uncommitted/untracked files that would be lost, then require the user to confirm
with the word `discard` (or an equally explicit confirmation already required by
the host environment). A prior request to "finish", "clean up", or open a PR is
not discard authorization.

After confirmation, remove only the specifically authorized work. Never use
`git clean -fdx` as workflow cleanup. Never delete a branch before handling an
owned linked worktree that references it.

## Worktree cleanup

Cleanup is allowed only when the workflow no longer needs the worktree and its
ownership is known from this run. Before removal, verify the worktree has no
unpreserved changes. Then:

1. `cd` outside the worktree into the main repository checkout.
2. `git worktree remove <owned-worktree-path>` without `--force`.
3. `git worktree prune` if appropriate.
4. Delete the feature branch only after the worktree no longer references it.

Do not remove host-managed, pre-existing, or ownership-ambiguous worktrees.

## Stacked-PR restack after parent merge

First fetch the actual integration branch and verify the parent PR's merge method
and the parent tip/boundary used to create the child. Do not guess a branch point.
If the parent merge preserved the relevant commits, simple PR retargeting may be
enough. If the parent was squash-merged and child commits must be replayed:

```bash
git rebase --onto origin/<integration-branch> <verified-parent-tip> <child-branch>
git push --force-with-lease
gh pr edit --base <integration-branch>
```

Never use plain `--force`. Recompute the child diff against the new base and rerun
checks affected by the restack before claiming the PR is ready.
