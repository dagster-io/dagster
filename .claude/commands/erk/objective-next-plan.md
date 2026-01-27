---
description: Create an implementation plan from an objective step
argument-hint: <issue-number-or-url>
---

# /erk:objective-create-plan

Create an implementation plan for a specific step in an objective's roadmap.

## Usage

```bash
/erk:objective-create-plan 3679
/erk:objective-create-plan https://github.com/owner/repo/issues/3679
/erk:objective-create-plan  # prompts for issue reference
```

---

## Agent Instructions

### Step 1: Parse Issue Reference

Parse `$ARGUMENTS` to extract the issue reference:

- If argument is a URL: extract issue number from path
- If argument is a number: use directly
- If no argument provided: try to get the default from pool.json (see below), then prompt if no default

**Getting default objective from pool.json:**

If no argument is provided, check if we're in a pool slot worktree with a last objective:

```bash
erk exec slot-objective
```

This returns JSON like:

```json
{ "objective_issue": 123, "slot_name": "erk-slot-01" }
```

Or if not in a slot or no objective:

```json
{ "objective_issue": null, "slot_name": null }
```

If `objective_issue` is not null, use it as the default and inform the user: "Using objective #<number> from slot's last objective. Run with explicit argument to override."

If no default found or not in a pool slot, prompt user using AskUserQuestion with "What objective issue should I work from?"

### Step 2: Fetch and Validate Issue

```bash
erk exec get-issue-body <issue-number>
```

This returns JSON with `{success, issue_number, title, body, labels, url}`.

**Validate this is an objective:**

1. Check for `erk-objective` label in the `labels` array
2. If label is `erk-plan` instead: report error "This is an erk-plan issue, not an objective. Use `/erk:plan-implement` instead."
3. If neither label: warn but proceed

### Step 2.5: Create Objective Context Marker

Create a marker to persist the objective issue number for the exit-plan-mode hook.

```bash
erk exec marker create --session-id "${CLAUDE_SESSION_ID}" \
  --associated-objective <objective-number> objective-context
```

Replace `<objective-number>` with the issue number from Step 2.

This enables the exit-plan-mode-hook to suggest the correct save command with `--objective-issue` automatically.

### Step 3: Load Objective Skill

Load the `objective` skill for format templates and guidance.

### Step 4: Parse Roadmap and Display Steps

Parse the objective body to extract roadmap steps. Look for markdown tables with columns like:

| Step | Description | Status | PR |

Extract all steps **in roadmap order** (Phase 1A before 1B before 2A, etc. - alphanumeric sort by step ID). Present steps in this natural order with the first pending step as the recommended option.

**Detect step status from PR column:**

- Empty PR column → `(pending)` - available to plan
- `#<number>` (just a number) → `(done, PR #XXX)` - already completed with a merged PR
- `plan #<number>` → `(plan in progress, #XXX)` - has a pending plan issue, skip recommending
- `blocked` in Status column → `(blocked)` - cannot be worked yet
- `skipped` in Status column → `(skipped)` - explicitly skipped

Display steps to the user:

```
Objective #<number>: <title>

Roadmap Steps:
  [1] Step 1A.1: <description> (pending) ← recommended
  [2] Step 1A.2: <description> (pending)
  [3] Step 1B.1: <description> (done, PR #123)
  [4] Step 2A.1: <description> (plan in progress, #456)
  ...
```

**Ordering rule:** Present steps in natural roadmap order (by step ID). The first pending step that does NOT have a plan in progress is the recommended option.

### Step 5: Prompt User to Select Step

Use AskUserQuestion to ask which step to plan:

```
Which step should I create a plan for?
- Step 1A.1: <description> (Recommended) ← first pending step without plan in progress
- Step 1A.2: <description>
- Step 2B.1: <description> (plan in progress, #456) ← shown but not recommended
- (Other - specify step number or description)
```

**Filtering rules:**

- **Show as options:** Steps that are `pending` (available to plan)
- **Show but deprioritize:** Steps with `plan in progress` - still selectable via "Other" but not recommended
- **Hide from options:** Steps that are `done`, `blocked`, or `skipped`

**Recommendation rule:** The first pending step (in roadmap order) that does NOT have a plan in progress is marked "(Recommended)".

If all steps are complete or have plans in progress, report appropriately:

- All complete: "All roadmap steps are complete! Consider closing the objective."
- All have plans: "All pending steps have plans in progress. You can still select one via 'Other' to create a parallel plan."

### Step 5.5: Create Roadmap Step Marker

After the user selects a step, create a marker to store the selected step ID for later use by `plan-save`:

```bash
erk exec marker create --session-id "${CLAUDE_SESSION_ID}" \
  --content "<step-id>" roadmap-step
```

Replace `<step-id>` with the step ID selected by the user (e.g., "2A.1"). This marker enables `plan-save` to automatically update the objective's roadmap table with the plan issue number.

### Step 6: Gather Context for Planning

Before entering plan mode, gather relevant context:

1. **Objective context:** Goal, design decisions, current focus
2. **Step context:** What the specific step requires
3. **Prior work:** Look at completed steps and their PRs for patterns

Use this context to inform the plan.

### Step 7: Enter Plan Mode

Enter plan mode to create the implementation plan:

1. Use the EnterPlanMode tool
2. Focus the plan on the specific step selected
3. Reference the parent objective in the plan

**Plan should include:**

- Reference to objective: `Part of Objective #<number>, Step <step-id>`
- Clear goal for this specific step
- Implementation phases (typically 1-3 for a single step)
- Files to modify
- Test requirements

### Step 8: Save Plan with Objective Link

After the plan is approved in plan mode, the `exit-plan-mode-hook` will prompt to save or implement.

**If the objective-context marker was created in Step 2.5:**
The hook will automatically suggest the correct command with `--objective-issue=<objective-number>`. Simply follow the hook's suggestion.

**If the marker was not created (fallback):**
Use the objective-aware save command manually:

```bash
/erk:plan-save --objective-issue=<objective-number>
```

Replace `<objective-number>` with the objective issue number from Step 2.

This will:

- Create a GitHub issue with the erk-plan label
- Link it to the parent objective (stored in metadata)
- Enable objective-aware landing via `/erk:land`

### Step 9: Verify Objective Link

After the plan is approved in plan mode, the `exit-plan-mode-hook` will prompt to save or implement.

**If the objective-context marker was created in Step 2.5:**
The hook will automatically suggest `/erk:plan-save --objective-issue=<objective-number>`.

When you run this command, it will:

- Save the plan to GitHub with objective metadata
- Automatically verify the objective link was saved correctly
- Display "Verified objective link: #<number>" on success
- Fail with remediation steps if verification fails

**Note:** If using `erk exec plan-save-to-issue` directly (not recommended), you must verify manually:

```bash
erk exec get-issue-body <new-issue-number>
```

Check the `body` field in the JSON response contains `objective_issue`.

---

## Output Format

- **Start:** "Loading objective #<number>..."
- **After parsing:** Display roadmap steps with status
- **After selection:** "Creating plan for step <step-id>: <description>"
- **In plan mode:** Show plan content
- **End:** Guide to `/erk:plan-save`

---

## Error Cases

| Scenario                                | Action                                                           |
| --------------------------------------- | ---------------------------------------------------------------- |
| Issue not found                         | Report error and exit                                            |
| Issue is erk-plan                       | Redirect to `/erk:plan-implement`                                |
| No pending steps                        | Report all steps complete, suggest closing                       |
| Invalid argument format                 | Prompt for valid issue number                                    |
| Roadmap not parseable                   | Ask user to specify which step to plan                           |
| Verification fails (no objective_issue) | `/erk:plan-save` handles automatically; follow remediation steps |

---

## Important Notes

- **Objective context matters:** Read the full objective for design decisions and lessons learned
- **One step at a time:** Each plan should focus on a single roadmap step
- **Link back:** Always reference the parent objective in the plan
- **Steelthread pattern:** If planning a Phase A step, focus on minimal vertical slice
