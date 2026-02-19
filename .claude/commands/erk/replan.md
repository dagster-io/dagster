---
description: Replan an existing erk-plan issue against current codebase state
argument-hint: <issue-number-or-url>
---

# /erk:replan

Recomputes an existing erk-plan issue against the current codebase state, creating a new plan and closing the original.

## Usage

```bash
/erk:replan 2521
/erk:replan https://github.com/owner/repo/issues/2521
```

---

## Agent Instructions

### Step 1: Parse Issue Reference

Extract the issue number from the argument:

- If numeric (e.g., `2521`), use directly
- If URL (e.g., `https://github.com/owner/repo/issues/2521`), extract the number from the path

If no argument provided, ask the user for the issue number.

### Step 2: Fetch Original Issue

```bash
erk exec get-issue-body <number>
```

This returns JSON with `{success, issue_number, title, body, state, labels, url}`. Store the issue title and check that:

1. Issue exists
2. Issue has `erk-plan` label

If not an erk-plan issue, display error:

```
Error: Issue #<number> is not an erk-plan issue (missing erk-plan label).
```

If issue is already closed, display warning but continue:

```
Warning: Issue #<number> is already closed. Proceeding with replan anyway.
```

### Step 3: Fetch Plan Content

The plan content is stored in the first comment's `plan-body` metadata block:

```bash
gh issue view <number> --comments --json comments
```

Parse the first comment to find `<!-- erk:metadata-block:plan-body -->` section.

Extract the plan content from within the `<details>` block.

If no plan-body found, display error:

```
Error: No plan content found in issue #<number>. Expected plan-body metadata block in first comment.
```

### Step 4: Deep Investigation

Use the Explore agent (Task tool with subagent_type=Explore) to perform deep investigation of the codebase. This is the most important step - surface-level analysis leads to poor plans.

#### 4a: Check Plan Items Against Codebase

For each implementation item in the plan:

- Search for relevant files, functions, or patterns
- Determine status: **implemented**, **partially implemented**, **not implemented**, or **obsolete**

Build a comparison table showing:

| Plan Item | Current Status | Notes |
| --------- | -------------- | ----- |
| ...       | ...            | ...   |

#### 4b: Deep Investigation (MANDATORY)

Go beyond the plan items to understand the actual implementation:

1. **Data Structures**: Find all relevant types, dataclasses, and their fields
2. **Helper Functions**: Identify utility functions and their purposes
3. **Lifecycle & State**: Understand how state flows through the system
4. **Naming Conventions**: Document actual names used (not guessed names)
5. **Entry Points**: Map all places that trigger the relevant functionality
6. **Configuration**: Find config options, defaults, and overrides

#### 4c: Document Corrections and Discoveries

Create two lists:

1. **Corrections to Original Plan**: Wrong assumptions, incorrect names, outdated information
2. **Additional Details**: Implementation specifics, architectural insights, edge cases

These lists will be posted to the original issue and included in the new plan.

### Step 5: Post Investigation to Original Issue

Before creating the new plan, post the investigation findings to the original issue as a comment. This preserves context if the new plan is also replanned later.

```bash
gh issue comment <original_number> --body "## Deep Investigation Notes (for implementing agent)

### Corrections to Original Plan
- [List corrections discovered]

### Additional Details Not in Original Plan
- [List new details discovered]

### Key Architectural Insights
- [List important discoveries]"
```

### Step 6: Create New Plan (Always)

**Always create a new plan issue**, regardless of implementation status. Even if the original plan is fully implemented or obsolete, a fresh plan with investigation context is valuable.

Use EnterPlanMode to create an updated plan.

The new plan should include:

#### Header Section

```markdown
# Plan: [Updated Title]

> **Replans:** #<original_issue_number>
```

#### What Changed Section

```markdown
## What Changed Since Original Plan

- [List major codebase changes that affect this plan]
- [Reference specific PRs or commits if relevant]
```

#### Investigation Findings Section

```markdown
## Investigation Findings

### Corrections to Original Plan

- [List any wrong assumptions or incorrect names from original plan]

### Additional Details Discovered

- [List implementation specifics not in original plan]
- [Include data structures, helper functions, naming conventions]
```

#### Remaining Gaps Section

```markdown
## Remaining Gaps

- [List items from original plan that still need implementation]
- [Note any items that are partially done]
- [Note if plan is fully implemented or obsolete - still document for context]
```

#### Implementation Steps Section

```markdown
## Implementation Steps

1. [Updated step 1]
2. [Updated step 2]
   ...
```

### Step 7: Save and Close

After the user approves the plan in Plan Mode:

1. Exit Plan Mode
2. Run `/erk:plan-save` to create the new GitHub issue
3. Close the original issue with a comment linking to the new one:

```bash
gh issue close <original_number> --comment "Superseded by #<new_number> - see updated plan that accounts for codebase changes."
```

Display final summary:

```
✓ Created new plan issue #<new_number>
✓ Closed original issue #<original_number>

Next steps:
- Review the new plan: gh issue view <new_number>
- Submit for implementation: erk plan submit <new_number>
```

---

## Error Cases

| Error                    | Message                                                                       |
| ------------------------ | ----------------------------------------------------------------------------- |
| Issue not found          | `Error: Issue #<number> not found.`                                           |
| Not an erk-plan          | `Error: Issue #<number> is not an erk-plan issue (missing erk-plan label).`   |
| No plan content          | `Error: No plan content found in issue #<number>.`                            |
| GitHub CLI not available | `Error: GitHub CLI (gh) not available. Run: brew install gh && gh auth login` |
| No network               | `Error: Unable to reach GitHub. Check network connectivity.`                  |

---

## Important Notes

- **DO NOT implement the plan** - This command only creates an updated plan
- **DO NOT skip codebase analysis** - Always verify current state before replanning
- **Use Explore agent** for comprehensive codebase searches (Task tool with subagent_type=Explore)
- The original issue is closed only after the new plan is successfully created
- The new plan references the original issue for traceability
