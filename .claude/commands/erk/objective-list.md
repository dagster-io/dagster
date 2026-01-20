---
description: List open objectives
---

# /erk:objective-list

List all open objectives in the current repository.

## Agent Instructions

### Step 1: Fetch Open Objectives

Run:

```bash
gh issue list --label "erk-objective" --state open --json number,title,createdAt --limit 50
```

### Step 2: Display Results

Format output as a markdown table:

| #    | Title                 | Created |
| ---- | --------------------- | ------- |
| #123 | Objective: Feature X  | 3d ago  |
| #456 | Objective: Refactor Y | 1w ago  |

If no objectives found, report: "No open objectives found."

### Step 3: Suggest Next Steps

After listing, suggest:

- /erk:objective-create-plan <number> to start planning a step from an objective
