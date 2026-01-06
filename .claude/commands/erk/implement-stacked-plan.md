---
description: Create a stacked branch and implement a saved plan
---

# /erk:implement-stacked-plan

Create a graphite-stacked branch from a saved plan issue and implement it in the current worktree.

## Usage

```
/erk:implement-stacked-plan <issue-number>
```

## When to Use This Command

✅ **Use when**: You have a saved plan (GitHub issue) and want to implement it as a stacked branch on top of your current branch.

❌ **Don't use when**:

- You just finished planning and want to save + implement → Use `/erk:plan-implement`
- You want to implement in a new worktree → Use `erk implement <issue-number>`

## Prerequisites

- Must be in a git repository managed by erk
- Must have a saved plan issue on GitHub (with `erk-plan` label)
- GitHub CLI (`gh`) must be authenticated
- Graphite CLI (`gt`) must be available

---

## Agent Instructions

### Step 1: Validate Argument

Extract the issue number from the argument (handles `#123` or `123` format).

If no issue number provided, display usage and stop:

```
Usage: /erk:implement-stacked-plan <issue-number>

Example: /erk:implement-stacked-plan 4128
```

### Step 2: Record Current Branch

Get the current branch name (this will be the parent for stacking):

```bash
git branch --show-current
```

Save this as `parent_branch`.

### Step 3: Setup Implementation

Run the setup command to fetch the plan, create the branch, and set up `.impl/`:

```bash
erk exec setup-impl-from-issue <issue-number>
```

Parse the output to get the `branch` name from the JSON.

If this fails, display the error and stop.

### Step 4: Track with Graphite

Register the new branch with graphite, stacked on the parent:

```bash
gt track --branch <branch-name> --parent <parent_branch>
```

This makes the branch part of the graphite stack for proper PR management.

### Step 5: Execute Implementation

Invoke the standard implementation workflow:

```
/erk:plan-implement
```

This handles all remaining steps: reading the plan, loading context, executing phases, running CI, and creating the PR.

---

## Notes

- The issue must have the `erk-plan` label
- The branch will be stacked on whatever branch you were on when you started
- Use this when you want to add a stacked change in the current worktree
- Differs from `erk implement` which creates a new worktree
