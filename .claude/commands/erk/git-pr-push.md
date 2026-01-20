---
description: Create git commit and push branch as PR using git + GitHub CLI
argument-hint: <description>
---

# Push PR (Git Only)

Automatically create a git commit with a helpful summary message and push the current branch as a pull request using standard git + GitHub CLI (no Graphite required).

## Usage

```bash
# Invoke the command (description argument is optional but recommended)
/erk:git-pr-push "Add user authentication feature"

# Without argument (will analyze changes automatically)
/erk:git-pr-push
```

## What This Command Does

Handles the complete git-only push-pr workflow:

1. Check for uncommitted changes and stage/commit them if needed
2. Analyze git diff to generate meaningful commit message
3. Create commit with AI-generated message
4. Push to origin with upstream tracking
5. Create GitHub PR (or find existing one)
6. Report results with PR URL

## Key Differences from /gt:submit-branch

- Uses standard `git push` instead of `gt submit`
- Uses `gh pr create` instead of Graphite's PR submission
- No stack operations (no restack, no stack metadata updates)
- Simpler workflow: git -> push -> PR (no Graphite layer)
- Works in any git repository (not just Graphite-enabled repos)

## Prerequisites

- Git repository with remote configured
- GitHub CLI (`gh`) installed and authenticated
- Run `gh auth status` to verify authentication
- Run `gh auth login` if not authenticated

## Implementation

Execute the git-only push-pr workflow with the following steps:

### Step 1: Verify Prerequisites

Check GitHub CLI authentication and get current git state:

```bash
# Check GitHub CLI authentication (show status for verification)
gh auth status

# Get current branch name
current_branch=$(git branch --show-current)

# Check for uncommitted changes
has_changes=$(git status --porcelain)
```

If `gh auth status` fails, report error and tell user to run `gh auth login`.

### Step 2: Stage Changes (if needed)

If `has_changes` is non-empty, stage all changes:

```bash
git add .
```

### Step 3: Analyze Staged Diff

Get the staged diff and analyze it to generate a commit message:

```bash
# Get repository root for relative paths
repo_root=$(git rev-parse --show-toplevel)

# Get staged diff for analysis
git diff --staged
```

Load the `erk-diff-analysis` skill for commit message generation guidance.

### Step 4: Create Commit

Create the commit with your AI-generated message using heredoc:

```bash
git commit -m "$(cat <<'COMMIT_MSG'
[Your generated commit message here]
COMMIT_MSG
)"
```

### Step 5: Push to Remote

Push the branch to origin with upstream tracking:

```bash
git push -u origin "$(git branch --show-current)"
```

### Step 6: Get Closing Text

Get the issue closing text if this worktree was created from a GitHub issue:

```bash
closing_text=$(erk exec get-closing-text 2>/dev/null || echo "")
```

This reads `.impl/issue.json` and returns `Closes #N` if an issue reference exists.

### Step 6.5: Check for Existing PR

Before creating a new PR, check if one already exists for the current branch:

```bash
existing_pr=$(gh pr list --head "$(git branch --show-current)" --state open --json number,url,isDraft --jq '.[0]')
```

**Decision logic:**

- If `existing_pr` is empty or null: No existing PR, proceed to Step 7
- If `existing_pr` has data: PR exists, skip Step 7 and go directly to Step 8

If an existing PR was found, extract its details for reporting:

```bash
pr_url=$(echo "$existing_pr" | jq -r '.url')
pr_number=$(echo "$existing_pr" | jq -r '.number')
is_draft=$(echo "$existing_pr" | jq -r '.isDraft')
```

### Step 7: Create GitHub PR (if no existing PR)

**Skip this step if an existing PR was found in Step 6.5.** The push in Step 5 already updated the existing PR with new commits.

Extract PR title (first line) and body (remaining lines) from commit message, then create PR with closing text appended:

```bash
# Get the commit message
commit_msg=$(git log -1 --pretty=%B)

# Extract first line as title
pr_title=$(echo "$commit_msg" | head -n 1)

# Extract remaining lines as body (skip empty first line after title)
commit_body=$(echo "$commit_msg" | tail -n +2)

# Append closing text if present
if [ -n "$closing_text" ]; then
    pr_body="${commit_body}

${closing_text}"
else
    pr_body="${commit_body}"
fi

# Create PR using GitHub CLI
gh pr create --title "$pr_title" --body "$pr_body"
```

### Step 8: Validate PR Rules

Run the PR check command to validate the PR was created correctly:

```bash
erk pr check
```

This validates:

- Issue closing reference (Closes #N) is present when `.impl/issue.json` exists
- PR body contains the standard checkout footer

If any checks fail, display the output and warn the user, but continue to Step 9.

### Step 9: Report Results

Display a clear summary based on whether a PR was created or found:

**If a NEW PR was created (Step 7 was executed):**

```
## Branch Submission Complete

### What Was Done

✓ Staged all uncommitted changes
✓ Created commit with AI-generated message
✓ Pushed branch to origin with upstream tracking
✓ Created GitHub PR
✓ Linked to issue #N (will auto-close on merge)  [only if closing_text was present]

### View PR

[PR URL from gh pr create output]
```

**If an EXISTING PR was found (Step 7 was skipped):**

```
## Branch Submission Complete

### What Was Done

✓ Staged all uncommitted changes
✓ Created commit with AI-generated message
✓ Pushed branch to origin with upstream tracking
✓ Found existing PR #N for this branch (skipped PR creation)
✓ Linked to issue #M (will auto-close on merge)  [only if closing_text was present]

### Note

[If is_draft is true]: This is a draft PR. When ready for review, run: `gh pr ready`

### View PR

[PR URL extracted from existing_pr]
```

**Conditional lines:**

- The "Linked to issue" line should only appear if `closing_text` was non-empty
- The "Note" section with draft guidance should only appear if `is_draft` is true

**CRITICAL**: The PR URL MUST be the absolute last line of your output. Do not add any text after it.

## Error Handling

When errors occur, provide clear guidance:

**GitHub CLI not authenticated:**

```
❌ GitHub CLI is not authenticated

To use this command, authenticate with GitHub:
    gh auth login
```

**Nothing to commit:**

```
❌ No changes to commit

Your working directory is clean. Make some changes first.
```

**Push failed (diverged branches):**

```
❌ Push failed: branch has diverged

Option 1: Pull and merge
    git pull origin [branch]

Option 2: Force push (⚠️ overwrites remote)
    git push -f origin [branch]
```

Note: The "PR already exists" case is now handled automatically in Step 6.5. If a PR exists for the current branch, the command will skip PR creation and report the existing PR URL instead.

## Best Practices

### Never Change Directory

**NEVER use `cd` during execution.** Always use absolute paths or git's `-C` flag.

```bash
# ❌ WRONG
cd /path/to/repo && git status

# ✅ CORRECT
git -C /path/to/repo status
```

**Rationale:** Changing directories pollutes the execution context and makes it harder to reason about state. The working directory should remain stable throughout the entire workflow.

### Never Write to Temporary Files

**NEVER write commit messages or other content to temporary files.** Always use in-context manipulation and shell built-ins.

```bash
# ❌ WRONG - Triggers permission prompts
echo "$message" > "${TMPDIR:-/tmp}/commit_msg.txt"
git commit -F "${TMPDIR:-/tmp}/commit_msg.txt"

# ✅ CORRECT - In-memory heredoc
git commit -m "$(cat <<'EOF'
$message
EOF
)"
```

**Rationale:** Temporary files require filesystem permissions and create unnecessary I/O. Since agents operate in isolated contexts, there's no risk of context pollution from in-memory manipulation.

## Quality Standards

### Always

- Be concise and strategic in analysis
- Use component-level descriptions
- Highlight breaking changes prominently
- Note test coverage patterns
- Use relative paths from repository root
- Provide clear error guidance
- Use standard git + GitHub CLI commands (no Graphite dependencies)

### Never

- Add Claude attribution or footer to commit messages
- Speculate about intentions without code evidence
- Provide exhaustive lists of every function touched
- Include implementation details (specific variable names, line numbers)
- Provide time estimates
- Use vague language like "various changes"
- Retry failed operations automatically
- Write to temporary files (use in-context quoting and shell built-ins instead)
- Use Graphite-specific commands (`gt submit`, `gt restack`, etc.)

## Self-Verification

Before completing, verify:

- [ ] GitHub CLI authentication checked
- [ ] Git status verified
- [ ] Uncommitted changes staged (if any existed)
- [ ] Staged diff analyzed
- [ ] Diff analysis is concise and strategic (3-5 key changes max)
- [ ] Commit message has no Claude footer
- [ ] File paths are relative to repository root
- [ ] Commit created successfully
- [ ] Branch pushed to origin with upstream tracking
- [ ] Closing text obtained (if issue reference exists)
- [ ] GitHub PR created successfully (or existing PR found)
- [ ] PR URL extracted from output
- [ ] Results displayed with "What Was Done" section listing actions
- [ ] PR URL placed at end under "View PR" section
- [ ] Any errors handled with helpful guidance
