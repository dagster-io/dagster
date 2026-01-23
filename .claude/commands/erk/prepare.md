---
description: Prepare a worktree from a saved plan issue
---

# /erk:prepare

## Goal

Find the most recent GitHub plan issue created in this conversation and prepare a worktree for implementation via `erk prepare`.

## What This Command Does

1. Search conversation for the last GitHub issue reference
2. Extract the issue number
3. Run `erk prepare <issue_number>` to create a worktree

## Finding the Issue

Search the conversation from bottom to top for these patterns (in priority order):

1. **plan-save/save-raw-plan output**: Look for `**Issue:** https://github.com/.../issues/<number>`
2. **Issue URL**: `https://github.com/<owner>/<repo>/issues/<number>`

Extract the issue number from the most recent match.

## Execution

Once you have the issue number, run:

```bash
erk prepare <issue_number>
```

Display the command output to the user. The `erk prepare` command handles worktree creation and slot allocation.

The output will include activation instructions like:

```
To activate the worktree environment:
  source /path/to/worktree/.erk/bin/activate.sh
```

Share these activation instructions with the user so they can switch to the new worktree.

## Error Cases

- **No issue found in conversation**: Report "No GitHub plan issue found in conversation. Run /erk:plan-save first to create an issue."
- **erk prepare fails**: Display the error output from the command
