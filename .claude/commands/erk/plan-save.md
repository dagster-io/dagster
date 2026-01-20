---
description: Save the current session's plan to GitHub as an issue
argument-hint: "[--objective-issue=<number>]"
---

# /erk:plan-save

Save the current session's plan to GitHub as an issue with session context.

## Usage

```bash
/erk:plan-save                           # Standalone plan
/erk:plan-save --objective-issue=3679    # Plan linked to objective
```

When creating a plan from an objective (via `/erk:objective-next-plan`), the exit-plan-mode hook will automatically suggest the command with the correct `--objective-issue` flag.

## Issue Structure

The created issue has a specific structure:

- **Issue body**: Contains only the metadata header (schema version, timestamps, etc.)
- **First comment**: Contains the actual plan content

This separation keeps machine-readable metadata in the body while the human-readable plan is in the first comment.

## Agent Instructions

### Step 1: Parse Arguments

Check `$ARGUMENTS` for the `--objective-issue` flag:

```
If $ARGUMENTS contains "--objective-issue=<number>":
  - Extract the number
  - Store as OBJECTIVE_ISSUE variable
  - Set OBJECTIVE_FLAG to "--objective-issue=<number>"
Else:
  - Set OBJECTIVE_FLAG to empty string
```

### Step 2: Run Save Command

Run this command with the session ID and optional objective flag:

```bash
erk exec plan-save-to-issue --format json --session-id="${CLAUDE_SESSION_ID}" ${OBJECTIVE_FLAG}
```

Parse the JSON output to extract `issue_number` for verification in Step 3.

If the command fails, display the error and stop.

### Step 3: Verify Objective Link (if applicable)

**Only run this step if `--objective-issue` was provided in arguments.**

Verify the objective link was saved correctly:

```bash
erk exec get-plan-metadata <issue_number> objective_issue
```

Parse the JSON response:

- If `success: true` and `value` matches the expected objective number: verification passed
- If `success: false` or value doesn't match: verification failed

**On verification success:**

Display: `Verified objective link: #<objective-number>`

**On verification failure:**

Display error and remediation steps:

```
ERROR: Objective link verification failed
Expected objective: #<expected>
Actual: <actual-or-null>

The plan was saved but without the correct objective link.
Fix: Close issue #<issue_number> and re-run:
  /erk:plan-save --objective-issue=<expected>
```

Exit without creating the plan-saved marker. The session continues so the user can retry.

### Step 3.5: Update Objective Roadmap (if objective linked)

**Only run this step if `--objective-issue` was provided and verification passed.**

Update the objective's roadmap table to show that a plan has been created for this step:

1. **Read the roadmap step marker** to get the step ID:

```bash
step_id=$(erk exec marker read --session-id "${CLAUDE_SESSION_ID}" roadmap-step)
```

If the marker doesn't exist (command fails), skip this step - the plan wasn't created via `objective-next-plan`.

2. **Fetch the objective issue body:**

```bash
erk exec get-issue-body <objective-issue>
```

Parse the JSON response to extract the `body` field. 3. **Parse and update the roadmap table:**

Find the row in the roadmap table where the Step column matches `step_id`. Update the PR column to show `plan #<issue_number>`.

Example transformation:

```markdown
# Before

| Step | Description   | Status  | PR  |
| ---- | ------------- | ------- | --- |
| 2A.1 | Add feature X | pending |     |

# After

| Step | Description   | Status  | PR         |
| ---- | ------------- | ------- | ---------- |
| 2A.1 | Add feature X | pending | plan #4567 |
```

4. **Update the objective issue:**

```bash
erk exec update-issue-body <objective-issue> --body "<updated_body>"
```

**Note:** If the PR column already has content, preserve it or append (e.g., if there's already a plan, append the new plan number).

5. **Report the update:**

Display: `Updated objective #<objective-issue> roadmap: step <step_id> → plan #<issue_number>`

**Error handling:** If the roadmap update fails, warn but continue - the plan was saved successfully, just the roadmap tracking didn't update. The user can manually update the objective.

### Step 4: Display Results

On success, display:

```
Plan "<title>" saved as issue #<issue_number>
URL: <issue_url>

Next steps:

View Issue: gh issue view <issue_number> --web

In Claude Code:
  Prepare worktree: /erk:prepare
  Submit to queue: /erk:plan-submit

OR exit Claude Code first, then run one of:
  Local: erk prepare <issue_number>
  Local (dangerously): erk prepare -d <issue_number>
  Submit to Queue: erk plan submit <issue_number>

The -d/--dangerous flag skips permission prompts during implementation,
allowing the agent to execute without approval gates.
```

If objective was verified, also display: `Verified objective link: #<objective-number>`

If the JSON output contains `slot_name` and `slot_objective_updated: true`, also display: `Slot objective updated: <slot_name> → #<objective-number>`

**Note:** Slot objective updates are handled automatically by `plan-save-to-issue` when `--objective-issue` is provided - no separate command call needed.

On failure, display the error message and suggest:

- Checking that a plan exists (enter Plan mode and exit it first)
- Verifying GitHub CLI authentication (`gh auth status`)
- Checking network connectivity

## Session Tracking

After successfully saving a plan, the issue number is stored in a marker file that enables automatic plan updates in the same session.

**To read the saved issue number:**

```bash
erk exec marker read --session-id "${CLAUDE_SESSION_ID}" plan-saved-issue
```

This returns the issue number (exit code 0) or exits with code 1 if no plan was saved in this session.
