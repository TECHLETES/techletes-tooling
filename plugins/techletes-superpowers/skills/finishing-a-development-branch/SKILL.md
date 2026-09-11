---
name: finishing-a-development-branch
description: Use when implementation is complete, all tests pass, and you need to decide how to integrate the work - guides completion of development work by presenting structured options for merge, PR, or cleanup
---

# Finishing a Development Branch

## Overview

Guide completion of development work by presenting clear options and handling chosen workflow.

**Core principle:** Verify tests → Detect environment → Determine actual delivery base → Present options → Execute choice → Clean up.

**Announce at start:** "I'm using the finishing-a-development-branch skill to complete this work."

## The Process

### Step 1: Verify Tests

**Before presenting options, verify tests pass:**

```bash
# Run project's test suite
npm test / cargo test / pytest / go test ./...
```

**If tests fail:**
```
Tests failing (<N> failures). Must fix before completing:

[Show failures]

Cannot proceed with merge/PR until tests pass.
```

Stop. Don't proceed to Step 2.

**If tests pass:** Continue to Step 2.

### Step 2: Detect Environment

**Determine workspace state before presenting options:**

```bash
GIT_DIR=$(cd "$(git rev-parse --git-dir)" 2>/dev/null && pwd -P)
GIT_COMMON=$(cd "$(git rev-parse --git-common-dir)" 2>/dev/null && pwd -P)
```

This determines which menu to show and how cleanup works:

| State | Menu | Cleanup |
|-------|------|---------|
| `GIT_DIR == GIT_COMMON` (normal repo) | Standard 4 options | No worktree to clean up |
| `GIT_DIR != GIT_COMMON`, named branch | Standard 4 options | Provenance-based (see Step 6) |
| `GIT_DIR != GIT_COMMON`, detached HEAD | Reduced 3 options (no merge) | No cleanup (externally managed) |

### Step 3: Determine PR Base

Do not assume `main` or infer the base only from branch ancestry. Determine the intended delivery base from the plan and GitHub state.

1. If the implementation plan has a `Delivery` section, use its planned PR base.
2. If the branch already has an open PR, use the PR's actual base:

```bash
BASE_BRANCH=$(gh pr view --json baseRefName --jq .baseRefName)
```

3. If the current issue depends on an open PR whose branch contains required code, use that direct parent feature branch as the base for a stacked PR.
4. Otherwise use `staging` as the Techletes default, unless the repository explicitly documents another integration branch.

Validate the chosen base exists:

```bash
git fetch origin

git rev-parse --verify "origin/$BASE_BRANCH"
```

For a stacked PR, confirm the relationship with GitHub instead of guessing from branch names:

```bash
gh pr view <parent-pr> --json number,headRefName,baseRefName,state
```

### Step 4: Present Options

**Normal repo and named-branch worktree — present exactly these 4 options:**

```
Implementation complete. What would you like to do?

1. Merge back to <base-branch> locally
2. Push and create a Pull Request
3. Keep the branch as-is (I'll handle it later)
4. Discard this work

Which option?
```

**Detached HEAD — present exactly these 3 options:**

```
Implementation complete. You're on a detached HEAD (externally managed workspace).

1. Push as new branch and create a Pull Request
2. Keep as-is (I'll handle it later)
3. Discard this work

Which option?
```

**Don't add explanation** - keep options concise.

### Step 5: Execute Choice

#### Option 1: Merge Locally

```bash
# Get main repo root for CWD safety
MAIN_ROOT=$(git -C "$(git rev-parse --git-common-dir)/.." rev-parse --show-toplevel)
cd "$MAIN_ROOT"

# Merge first — verify success before removing anything
git checkout <base-branch>
git pull
git merge <feature-branch>

# Verify tests on merged result
<test command>

# Only after merge succeeds: cleanup worktree (Step 6), then delete branch
```

Then: Cleanup worktree (Step 6), then delete branch:

```bash
git branch -d <feature-branch>
```

#### Option 2: Push and Create PR

```bash
# Push branch
git push -u origin <feature-branch>
```

Create the PR against the base determined in Step 3:

```bash
gh pr create --base "$BASE_BRANCH" --head <feature-branch> ...
```

For a stacked PR, include concise dependency metadata in the PR body:

```text
Stacked on #<parent-pr>.

Review this PR against `<parent-feature-branch>`.
Merge #<parent-pr> first, then retarget/restack this PR to `staging`.
```

Do not target `staging` directly while the child still depends on an unmerged parent PR; doing so makes the child diff include the parent work.

While both parent and child PRs are open and actively reviewed, prefer merging parent branch updates into the child branch:

```bash
git checkout <child-branch>
git merge origin/<parent-feature-branch>
git push
```

Avoid repeatedly rebasing an already-reviewed child just to pick up parent changes, because that rewrites commit SHAs and makes GitHub review history noisy.

After the parent PR merges, move the child onto the integration branch. If the parent was merged without rewriting commits, retargeting may be sufficient. If the parent was squash-merged, replay only child-specific commits:

```bash
git fetch origin
git checkout <child-branch>
git rebase --onto origin/staging <parent-feature-branch> <child-branch>
git push --force-with-lease
```

Then retarget the PR to `staging`:

```bash
gh pr edit --base staging
```

Use `--force-with-lease`, never plain `--force`, and only for this deliberate post-parent restack or when the user explicitly requests a history rewrite.

**Do NOT clean up worktree** — user needs it alive to iterate on PR feedback.

#### Option 3: Keep As-Is

Report: "Keeping branch <name>. Worktree preserved at <path>."

**Don't cleanup worktree.**

#### Option 4: Discard

**Confirm first:**
```
This will permanently delete:
- Branch <name>
- All commits: <commit-list>
- Worktree at <path>

Type 'discard' to confirm.
```

Wait for exact confirmation.

If confirmed:
```bash
MAIN_ROOT=$(git -C "$(git rev-parse --git-common-dir)/.." rev-parse --show-toplevel)
cd "$MAIN_ROOT"
```

Then: Cleanup worktree (Step 6), then force-delete branch:
```bash
git branch -D <feature-branch>
```

### Step 6: Cleanup Workspace

**Only runs for Options 1 and 4.** Options 2 and 3 always preserve the worktree.

```bash
GIT_DIR=$(cd "$(git rev-parse --git-dir)" 2>/dev/null && pwd -P)
GIT_COMMON=$(cd "$(git rev-parse --git-common-dir)" 2>/dev/null && pwd -P)
WORKTREE_PATH=$(git rev-parse --show-toplevel)
```

**If `GIT_DIR == GIT_COMMON`:** Normal repo, no worktree to clean up. Done.

**If worktree path is under `.worktrees/` or `worktrees/`:** Superpowers created this worktree — we own cleanup.

```bash
MAIN_ROOT=$(git -C "$(git rev-parse --git-common-dir)/.." rev-parse --show-toplevel)
cd "$MAIN_ROOT"
git worktree remove "$WORKTREE_PATH"
git worktree prune  # Self-healing: clean up any stale registrations
```

**Otherwise:** The host environment (harness) owns this workspace. Do NOT remove it. If your platform provides a workspace-exit tool, use it. Otherwise, leave the workspace in place.

## Quick Reference

| Option | Merge | Push | Keep Worktree | Cleanup Branch |
|--------|-------|------|---------------|----------------|
| 1. Merge locally | yes | - | - | yes |
| 2. Create PR | - | yes | yes | - |
| 3. Keep as-is | - | - | yes | - |
| 4. Discard | - | - | - | yes (force) |

## Common Mistakes

**Assuming main/master is the base**
- **Problem:** Techletes feature work normally targets `staging`, and stacked PRs target their direct parent feature branch
- **Fix:** Read the plan/GitHub PR state and determine the actual base before merging, reviewing, or opening a PR

**Targeting staging for a dependent child PR**
- **Problem:** The child PR includes the still-unmerged parent diff
- **Fix:** Target the direct parent feature branch until the parent PR is merged

**Rebasing an active reviewed stack for every parent update**
- **Problem:** Rewrites child commit SHAs and creates noisy review history
- **Fix:** Merge parent updates into the child while both PRs remain open; restack only after the parent merges or when otherwise necessary

**Skipping test verification**
- **Problem:** Merge broken code, create failing PR
- **Fix:** Always verify tests before offering options

**Open-ended questions**
- **Problem:** "What should I do next?" is ambiguous
- **Fix:** Present exactly 4 structured options (or 3 for detached HEAD)

**Cleaning up worktree for Option 2**
- **Problem:** Remove worktree user needs for PR iteration
- **Fix:** Only cleanup for Options 1 and 4

**Deleting branch before removing worktree**
- **Problem:** `git branch -d` fails because worktree still references the branch
- **Fix:** Merge first, remove worktree, then delete branch

**Running git worktree remove from inside the worktree**
- **Problem:** Command fails silently when CWD is inside the worktree being removed
- **Fix:** Always `cd` to main repo root before `git worktree remove`

**Cleaning up harness-owned worktrees**
- **Problem:** Removing a worktree the harness created causes phantom state
- **Fix:** Only clean up worktrees under `.worktrees/` or `worktrees/`

**No confirmation for discard**
- **Problem:** Accidentally delete work
- **Fix:** Require typed "discard" confirmation

## Red Flags

**Never:**
- Proceed with failing tests
- Merge without verifying tests on result
- Delete work without confirmation
- Force-push except a deliberate post-parent stacked-PR restack using `--force-with-lease`, or when explicitly requested
- Remove a worktree before confirming merge success
- Clean up worktrees you didn't create (provenance check)
- Run `git worktree remove` from inside the worktree

**Always:**
- Verify tests before offering options
- Detect environment before presenting menu
- Determine the real PR base from plan/GitHub state; default to `staging`, not `main`
- Target the direct parent branch for dependent stacked PRs
- Merge stacked PRs bottom-up
- Present exactly 4 options (or 3 for detached HEAD)
- Get typed confirmation for Option 4
- Clean up worktree for Options 1 & 4 only
- `cd` to main repo root before worktree removal
- Run `git worktree prune` after removal
