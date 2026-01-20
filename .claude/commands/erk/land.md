---
description: Land PR with objective awareness - updates objective after landing
argument-hint: "[branch|PR#|URL] [--skip-objective]"
---

# /erk:land

Objective-aware wrapper for `erk land`. Lands the PR first, then offers to update the linked objective if one exists.

## Usage

```bash
# Land PR for current branch
/erk:pr-land

# Land PR for specific branch
/erk:pr-land feature-branch

# Land PR by number
/erk:pr-land 123

# Land PR by URL
/erk:pr-land https://github.com/owner/repo/pull/123

# Skip objective update prompt
/erk:pr-land --skip-objective
```

---

## Agent Instructions

### Step 1: Parse Arguments

Parse the command arguments:

- `$ARGUMENTS` may contain: branch name, PR number, PR URL, or be empty (use current branch)
- Check for `--skip-objective` flag

### Step 2: Determine Branch Name

If no branch argument provided, get current branch:

```bash
git branch --show-current
```

If argument is a PR number or URL, extract the branch name:

```bash
# For PR number
gh pr view <number> --json headRefName -q '.headRefName'

# For PR URL (extract number first, then use above)
```

### Step 3: Resolve to PR Number

**Critical:** Always resolve the branch to a PR number. The `erk land` command only accepts PR numbers or URLs, not branch names.

```bash
# Get PR number for branch
gh pr list --head <branch-name> --state open --json number -q '.[0].number'
```

If no open PR found, check all states:

```bash
gh pr list --head <branch-name> --state all --limit 1 --json number -q '.[0].number'
```

**If no PR found:** Report error and exit - cannot land without a PR.

### Step 4: Extract Plan Issue Number (P-prefix Detection)

Parse the plan issue number from the branch name pattern `P<number>-...`

Example: `P3699-objective-aware-pr-land` -> Plan Issue #3699

**If branch doesn't have P-prefix:** Record that there's no plan link. Continue to Step 6.

### Step 5: Check for Objective Link

If branch has P-prefix, use the `get-plan-metadata` exec command to extract the objective issue:

```bash
erk exec get-plan-metadata <plan-number> objective_issue
```

**Output format:**

```json
{
  "success": true,
  "value": 3400,
  "issue_number": 3509,
  "field": "objective_issue"
}
```

- If `success` is `true` and `value` is an integer, record that objective issue number
- If `success` is `true` and `value` is `null`, there's no objective link
- If `success` is `false`, warn and skip objective workflow (fail-open behavior)

### Step 6: Execute erk land

Land the PR using the resolved PR number. Use `--force` to skip interactive confirmation (required for non-TTY execution):

```bash
erk land <PR_NUMBER> --force
```

**If landing fails:** Report the error and exit.

### Step 7: Post-Land Objective Update

**Only runs if:** Landing succeeded AND plan has `objective_issue` AND `--skip-objective` not passed

1. Display: "PR #`<pr>` landed successfully."
2. Display: "This PR is part of Objective #`<objective>`."
3. Prompt user with AskUserQuestion:

```
Would you like to update the objective now?

Options:
1. Yes, update objective (Recommended)
2. Skip - I'll update it later
```

**If user selects "Yes":**

Run the `/erk:objective-update-with-landed-pr` workflow inline:

1. Post an action comment to the objective issue with:
   - What was done (infer from PR title/description)
   - Lessons learned (infer from implementation)
   - Roadmap updates (which steps are now done)

2. Update the objective body:
   - Mark relevant roadmap steps as `done`
   - Add PR number to the step
   - Update "Current Focus" section

3. Check if all steps are complete - if so, offer to close the objective.

**If user selects "Skip":** Just report success and remind them to update later.

### Step 8: Report Results

Display final status:

- PR landing result
- Objective update result (if applicable)
- Link to objective issue (if applicable)

---

## Fail-Open Behavior

The command lands normally (no blocking) when:

| Scenario                          | Action                          |
| --------------------------------- | ------------------------------- |
| Branch has no P-prefix            | Land normally, skip objective   |
| Plan issue not found              | Warn, land normally             |
| `objective_issue` is null/missing | Land normally, skip objective   |
| `--skip-objective` flag passed    | Land normally, skip objective   |
| Objective update fails            | Warn but report landing success |
| Any parsing/API error             | Warn, continue with landing     |

**Principle:** Landing always proceeds. Objective update is post-land and optional.

---

## Output Format

- **Start:** "Resolving PR for branch..."
- **No PR found:** "Error: No PR found for branch `<branch>`"
- **Landing:** "Landing PR #`<number>`..."
- **Success:** "PR #`<number>` landed successfully."
- **Objective prompt:** (as shown above)
- **Objective updated:** "Objective #`<number>` updated."
- **End:** Show final status and any relevant links

---

## Error Handling

- **No PR found:** Report error and exit (cannot land without PR)
- **Landing fails:** Report `erk land` error output and exit
- **Objective update fails:** Warn but report landing as successful
- **API errors during objective check:** Warn and skip objective workflow
