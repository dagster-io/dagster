---
description: Save plan to GitHub and execute implementation in current worktree
---

# /erk:plan-implement

User-facing command to save a plan to GitHub and immediately implement it.

This is the primary implementation workflow - it orchestrates:

1. Saving the plan to GitHub as an issue
2. Setting up the `.impl/` folder
3. Executing the implementation

## Prerequisites

- Must be in a git repository managed by erk
- Must have a plan in `~/.claude/plans/` (from plan mode)
- GitHub CLI (`gh`) must be authenticated

## When NOT to Use This Command

❌ **After `/erk:plan-save`** - The plan is already saved to GitHub. Use:

- `erk implement <issue-number>` - CLI command to fetch and implement
- `/erk:plan-implement-here <issue-number>` - Slash command alternative

❌ **When implementing an existing GitHub issue** - Use the commands above instead.

✅ **Use this command when**: You just finished planning in plan mode and want to immediately implement (save + implement in one step).

---

## Agent Instructions

### Step 1: Check if .impl/ Already Set Up

First, check if implementation is already set up (e.g., from `erk implement <issue>`):

```bash
erk exec impl-init --json
```

If this succeeds with `"valid": true` and `"has_issue_tracking": true`, the `.impl/` folder is already configured. **Skip directly to Step 4** (Read Plan and Load Context).

If it fails or returns `"valid": false`, continue to Step 2 to save the plan.

### Step 2: Extract Session ID

Get the session ID from the `SESSION_CONTEXT` reminder in your conversation context.

### Step 3: Save Plan to GitHub

Save the current plan to GitHub and capture the issue number:

```bash
erk exec plan-save-to-issue --format json --session-id="<session-id>"
```

Parse the JSON output to get:

- `issue_number`: The created issue number
- `title`: The issue title (for branch naming)

If this fails, display the error and stop.

### Step 3b: Create Branch and Setup .impl/

Now set up the implementation environment using the saved issue:

```bash
erk exec setup-impl-from-issue <issue-number>
```

This command:

- Creates a feature branch from current branch (stacked) or trunk
- Checks out the new branch in the current worktree
- Creates `.impl/` folder with the plan content
- Saves issue reference for PR linking

If this fails, display the error and stop.

### Step 3c: Re-run Implementation Initialization

Run impl-init again now that .impl/ is set up:

```bash
erk exec impl-init --json
```

Use the returned `phases` for TodoWrite entries. If validation fails, display error and stop.

### Step 4: Read Plan and Load Context

Read `.impl/plan.md` to understand:

- Overall goal and context
- Context & Understanding sections (API quirks, architectural insights, pitfalls)
- Implementation phases and dependencies
- Success criteria

**Context Consumption**: Plans contain expensive discoveries. Ignoring `[CRITICAL:]` tags, "Related Context:" subsections, or "DO NOT" items causes repeated mistakes.

### Step 5: Load Related Documentation

If plan contains "Related Documentation" section, load listed skills via Skill tool and read listed docs.

### Step 6: Create TodoWrite Entries

Create todo entries for each phase from impl-init output.

### Step 7: Signal GitHub Started

```bash
erk exec impl-signal started --session-id="<session-id>" 2>/dev/null || true
```

This also deletes the Claude plan file (from `~/.claude/plans/`) since:

- The content has been saved to GitHub issue
- The content has been snapshotted to `.erk/scratch/`
- Keeping it could cause confusion if the user tries to re-save

### Step 8: Execute Each Phase Sequentially

For each phase:

1. **Mark phase as in_progress** (in TodoWrite)
2. **Read task requirements** carefully
3. **Implement code AND tests together**:
   - Load `dignified-python-313` skill for coding standards
   - Load `fake-driven-testing` skill for test patterns
   - Follow project AGENTS.md standards
4. **Mark phase as completed** (in TodoWrite)
5. **Report progress**: changes made, what's next

**Important:** `.impl/plan.md` is immutable - NEVER edit during implementation

### Step 9: Report Progress

After each phase: report changes made and what's next.

### Step 10: Final Verification

Confirm all tasks executed, success criteria met, note deviations, summarize changes.

### Step 11: Signal GitHub Ended

```bash
erk exec impl-signal ended 2>/dev/null || true
```

### Step 12: Verify .impl/ Preserved

**CRITICAL GUARDRAIL**: Verify the .impl/ folder was NOT deleted.

```bash
erk exec impl-verify
```

If this fails, you have violated instructions. The .impl/ folder must be preserved for user review.

### Step 13: Run CI Iteratively

1. If `.erk/prompt-hooks/post-plan-implement-ci.md` exists: follow its instructions
2. Otherwise: check CLAUDE.md/AGENTS.md for CI commands

After CI passes:

- `.worker-impl/`: delete folder, commit cleanup, push
- `.impl/`: **NEVER DELETE** - leave for user review (no auto-commit)

### Step 14: Create/Update PR (if .worker-impl/ present)

**Only if .worker-impl/ was present:**

```bash
gh pr create --fill --label "ai-generated" || gh pr edit --add-label "ai-generated"
```

Then validate PR rules:

```bash
erk pr check
```

If checks fail, display output and warn user.

### Step 15: Output Format

- **Start**: "Saving plan and setting up implementation..."
- **After save**: "Plan saved as issue #X, setting up .impl/ folder..."
- **Each phase**: "Phase X: [brief description]" with code changes
- **End**: "Plan execution complete. [Summary]"

---

## Related Commands

- `/erk:plan-save` - Save plan only, don't implement (for defer-to-later workflow)
- `/erk:plan-implement-here` - Implement from existing GitHub issue (skips save step)
