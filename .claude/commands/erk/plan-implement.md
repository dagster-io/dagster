---
description: Implement a plan from GitHub issue, file path, or current .impl folder
argument-hint: "[<issue-number-or-url-or-path>]"
---

# /erk:plan-implement

Implement a plan - either from a GitHub issue, a markdown file, an existing `.impl/` folder, or by saving the current plan first.

This is the primary implementation workflow - it orchestrates:

1. Setting up the `.impl/` folder (from issue, file, existing folder, or fresh plan)
2. Executing the implementation
3. Running CI and submitting the PR

## Prerequisites

- Must be in a git repository managed by erk
- GitHub CLI (`gh`) must be authenticated
- One of:
  - An issue number, URL, or file path argument
  - An existing `.impl/` folder
  - A plan in `~/.claude/plans/` (from plan mode)

## Usage

```bash
/erk:plan-implement                    # Use .impl/ or save current plan
/erk:plan-implement 2521               # Fetch and implement issue #2521
/erk:plan-implement https://github.com/owner/repo/issues/2521  # URL form
/erk:plan-implement ./my-plan.md       # Implement from local markdown file
```

---

## Agent Instructions

### Step 0: Parse Arguments

Extract optional argument from `$ARGUMENTS`:

- **If numeric** (e.g., `2521`): Store as `ISSUE_ARG`
- **If GitHub URL** (e.g., `https://github.com/owner/repo/issues/2521`): Extract number from path, store as `ISSUE_ARG`
- **If path to file** (anything else non-empty): Store as `FILE_ARG`
- **If empty**: Proceed to check `.impl/` folder

Store either `ISSUE_ARG` (issue number) or `FILE_ARG` (file path), or neither if empty.

### Step 1: Determine Implementation Source

Follow this priority order:

#### 1a. If ISSUE_ARG is provided

Set up from the specified issue:

```bash
erk exec setup-impl-from-issue <ISSUE_ARG>
```

This command:

- Creates a feature branch from current branch (stacked) or trunk
- Checks out the new branch in the current worktree
- Creates `.impl/` folder with the plan content
- Saves issue reference for PR linking

If this fails, display the error and stop.

Then run impl-init:

```bash
erk exec impl-init --json
```

#### 1a-file. If FILE_ARG is provided

Set up from the specified markdown file:

1. **Verify the file exists** using the Read tool
2. **Extract the title** from the first `# ` heading in the file
3. **Generate branch name** from the title (slugify: lowercase, replace spaces with hyphens, remove special chars)
4. **Create a feature branch** (use devrun agent for gt commands):
   ```bash
   gt create <branch-name>
   ```
5. **Create `.impl/` folder** and copy the plan:
   ```bash
   mkdir -p .impl && cp <FILE_ARG> .impl/plan.md
   ```

This is a local-only plan (no GitHub issue tracking).

Then run impl-init:

```bash
erk exec impl-init --json
```

Note: `has_issue_tracking` will be `false` for file-based plans.

#### 1b. If .impl/ already exists

Check if implementation is already set up:

```bash
erk exec impl-init --json
```

If this succeeds with `"valid": true`, the `.impl/` folder is already configured. **Skip directly to Step 3** (Read Plan and Load Context).

Note: `has_issue_tracking` may be `true` (issue-based) or `false` (file-based).

If it fails or returns `"valid": false`, continue to Step 2.

#### 1c. Fall back to saving current plan

If neither argument nor valid `.impl/` exists, save the current plan from plan mode (Step 2).

### Step 2: Save Plan to GitHub

Save the current plan to GitHub and capture the issue number:

```bash
erk exec plan-save-to-issue --format json --session-id="${CLAUDE_SESSION_ID}"
```

Parse the JSON output to get:

- `issue_number`: The created issue number
- `title`: The issue title (for branch naming)

If this fails, display the error and stop.

### Step 2b: Create Branch and Setup .impl/

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

### Step 2c: Re-run Implementation Initialization

Run impl-init again now that .impl/ is set up:

```bash
erk exec impl-init --json
```

Use the returned `phases` for TodoWrite entries. If validation fails, display error and stop.

### Step 3: Read Plan and Load Context

Read `.impl/plan.md` to understand:

- Overall goal and context
- Context & Understanding sections (API quirks, architectural insights, pitfalls)
- Implementation phases and dependencies
- Success criteria

**Context Consumption**: Plans contain expensive discoveries. Ignoring `[CRITICAL:]` tags, "Related Context:" subsections, or "DO NOT" items causes repeated mistakes.

### Step 4: Load Related Documentation

If plan contains "Related Documentation" section, load listed skills via Skill tool and read listed docs.

### Step 5: Create TodoWrite Entries

Create todo entries for each phase from impl-init output.

### Step 6: Signal GitHub Started

```bash
erk exec impl-signal started --session-id="${CLAUDE_SESSION_ID}" 2>/dev/null || true
```

This also deletes the Claude plan file (from `~/.claude/plans/`) since:

- The content has been saved to GitHub issue
- The content has been snapshotted to `.erk/scratch/`
- Keeping it could cause confusion if the user tries to re-save

### Step 7: Execute Each Phase Sequentially

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

### Step 8: Report Progress

After each phase: report changes made and what's next.

### Step 9: Final Verification

Confirm all tasks executed, success criteria met, note deviations, summarize changes.

### Step 10: Signal GitHub Ended

```bash
erk exec impl-signal ended --session-id="${CLAUDE_SESSION_ID}" 2>/dev/null || true
```

### Step 11: Verify .impl/ Preserved

**CRITICAL GUARDRAIL**: Verify the .impl/ folder was NOT deleted.

```bash
erk exec impl-verify
```

If this fails, you have violated instructions. The .impl/ folder must be preserved for user review.

### Step 12: Run CI Iteratively

1. If `.erk/prompt-hooks/post-plan-implement-ci.md` exists: follow its instructions
2. Otherwise: check CLAUDE.md/AGENTS.md for CI commands

After CI passes, clean up `.worker-impl/` if present:

```bash
if [ -d .worker-impl/ ]; then
  git rm -rf .worker-impl/
  git commit -m "Remove .worker-impl/ after implementation"
  git push
fi
```

**CRITICAL**: Never delete `.impl/` - leave for user review (no auto-commit).

### Step 13: Create/Update PR (if .worker-impl/ present)

**Only if .worker-impl/ was present:**

```bash
gh pr create --fill --label "ai-generated" || gh pr edit --add-label "ai-generated"
```

Then validate PR rules:

```bash
erk pr check
```

If checks fail, display output and warn user.

### Step 14: Output Format

- **Start**: "Setting up implementation..." or "Fetching plan from issue #X..."
- **After setup**: "Implementation environment ready, reading plan..."
- **Each phase**: "Phase X: [brief description]" with code changes
- **End**: "Plan execution complete. [Summary]"

### Step 15: Submit PR

After all phases complete and CI passes, submit the PR:

```
/erk:pr-submit
```

This delegates to `erk pr submit` which handles commit message generation, Graphite submission, and PR metadata.

---

## Related Commands

- `/erk:plan-save` - Save plan only, don't implement (for defer-to-later workflow)
- `/erk:replan` - Re-plan an existing issue with current codebase state
