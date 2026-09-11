---
name: requesting-code-review
description: Use when completing tasks, implementing major features, or before merging to verify work meets requirements
---

# Requesting Code Review

Dispatch a code reviewer subagent to catch issues before they cascade. The reviewer gets precisely crafted context for evaluation — never your session's history. This keeps the reviewer focused on the work product, not your thought process, and preserves your own context for continued work.

**Core principle:** Review early, review often.

## When to Request Review

**Mandatory:**
- After each task in subagent-driven development
- After completing major feature
- Before merge to the integration branch

**Optional but valuable:**
- When stuck (fresh perspective)
- Before refactoring (baseline check)
- After fixing complex bug

## How to Request

**1. Determine the actual review base and get git SHAs:**

If the branch already has a PR, derive the review base from GitHub instead of assuming `main` or `HEAD~1`:

```bash
BASE_BRANCH=$(gh pr view --json baseRefName --jq .baseRefName)
git fetch origin "$BASE_BRANCH"
BASE_SHA=$(git merge-base HEAD "origin/$BASE_BRANCH")
HEAD_SHA=$(git rev-parse HEAD)
```

This is required for stacked PRs. For example:

```text
#190: staging...feature/90-export-approval
#191: feature/90-export-approval...feature/71-export-workflow
```

Review #191 against `feature/90-export-approval`, not against `staging`, so #190 changes are not reviewed twice.

If the PR does not exist yet, use the PR base recorded in the implementation plan's `Delivery` section. If no planned base exists, use `staging` as the Techletes default unless the repository explicitly documents another integration branch.

For a task-level review that intentionally covers only the most recent task rather than the complete PR, use the task's starting commit as `BASE_SHA`. Do not substitute `HEAD~1` when the task spans multiple commits.

**2. Dispatch code reviewer subagent:**

Dispatch a `general-purpose` subagent, filling the template at [code-reviewer.md](code-reviewer.md)

**Placeholders:**
- `{DESCRIPTION}` - Brief summary of what you built
- `{PLAN_OR_REQUIREMENTS}` - What it should do
- `{BASE_SHA}` - Starting commit
- `{HEAD_SHA}` - Ending commit

**3. Act on feedback:**
- Fix Critical issues immediately
- Fix Important issues before proceeding
- Note Minor issues for later
- Push back if reviewer is wrong (with reasoning)

## Example

```
[Just completed Task 2: Add verification function]

You: Let me request code review before proceeding.

BASE_SHA=$(git log --oneline | grep "Task 1" | head -1 | awk '{print $1}')
HEAD_SHA=$(git rev-parse HEAD)

[Dispatch code reviewer subagent]
  DESCRIPTION: Added verifyIndex() and repairIndex() with 4 issue types
  PLAN_OR_REQUIREMENTS: Task 2 from docs/superpowers/plans/deployment-plan.md
  BASE_SHA: a7981ec
  HEAD_SHA: 3df7661

[Subagent returns]:
  Strengths: Clean architecture, real tests
  Issues:
    Important: Missing progress indicators
    Minor: Magic number (100) for reporting interval
  Assessment: Ready to proceed

You: [Fix progress indicators]
[Continue to Task 3]
```

## Integration with Workflows

**Subagent-Driven Development:**
- Review after EACH task
- Catch issues before they compound
- Fix before moving to next task

**Executing Plans:**
- Review after each task or at natural checkpoints
- Get feedback, apply, continue

**Ad-Hoc Development:**
- Review before merge
- Review when stuck

**Stacked PRs:**
- Read the actual `baseRefName` from the PR
- Review only the child-specific diff against its direct parent branch
- Do not report findings on unchanged parent code as child-PR findings
- After the parent is merged and the child is restacked/retargeted, recompute the base before re-reviewing

## Red Flags

**Never:**
- Skip review because "it's simple"
- Assume `origin/main` is the PR review base
- Review a stacked child against `staging` while its parent PR is still open
- Ignore Critical issues
- Proceed with unfixed Important issues
- Argue with valid technical feedback

**If reviewer wrong:**
- Push back with technical reasoning
- Show code/tests that prove it works
- Request clarification

See template at: [code-reviewer.md](code-reviewer.md)
