---
description: Create diagnostic report for git index.lock errors from current context
---

# Diagnostic Report: Git Lock Error

When a git operation fails with `fatal: Unable to create '.../.git/index.lock': File exists`, this command collects diagnostic information and uploads it as a GitHub gist for analysis.

## Usage

Run this command when you encounter a git index.lock error:

```bash
/erk:diag-lock-error
```

## Implementation

### Step 1: Identify the Lock Error in Context

Search the current conversation context for the git index.lock error. Look for:

- Tool results containing `fatal: Unable to create` and `index.lock`
- The specific repository path where the error occurred (extract the full lock file path)
- The command that triggered the error

**Extract the lock file path** from the error message. Examples:

- Regular repo: `.git/index.lock`
- Worktree: `/path/to/.git/worktrees/<name>/index.lock`

Save this path for Step 2c.

If no lock error is found in the recent context, ask the user: "No git index.lock error found. Run diagnostic anyway to capture system state?" If yes, proceed with data collection (error context will note "proactive collection - no current error").

### Step 2: Collect Diagnostic Data

Create a temporary directory and collect all diagnostic files:

```bash
DIAG_DIR=$(mktemp -d)
echo "Collecting diagnostics in $DIAG_DIR"
```

#### 2a. Error Context

Write the error details from the conversation to a file. Include:

- The exact command that failed (e.g., `erk exec quick-submit`, `git add -A`)
- The full error message including the lock file path
- Timestamp if visible
- Whether the lock was removed and how (manual rm, or still present)

```bash
cat > "$DIAG_DIR/01-error-context.txt" << 'EOF'
# Error Context

Command: <command that triggered the error>
Time: <timestamp if known>
Repository: <working directory path>
Lock file path: <full path from error message>

Error output:
<full error message>

Resolution: <how it was resolved, or "still investigating">
EOF
```

#### 2b. Git Status

```bash
git status > "$DIAG_DIR/02-git-status.txt" 2>&1
```

#### 2c. Lock File State

Check if the lock file exists using the **exact path from the error message** (Step 1):

```bash
# Use the lock file path extracted from the error message
LOCK_FILE="<path from error message>"
if [ -f "$LOCK_FILE" ]; then
    echo "Lock file EXISTS" > "$DIAG_DIR/03-lock-state.txt"
    ls -la "$LOCK_FILE" >> "$DIAG_DIR/03-lock-state.txt"
    # File details (macOS)
    stat "$LOCK_FILE" >> "$DIAG_DIR/03-lock-state.txt" 2>&1
    # Check if empty (stale lock indicator)
    echo "" >> "$DIAG_DIR/03-lock-state.txt"
    echo "File size: $(wc -c < "$LOCK_FILE") bytes" >> "$DIAG_DIR/03-lock-state.txt"
else
    echo "Lock file does NOT exist (may have been removed)" > "$DIAG_DIR/03-lock-state.txt"
fi
```

#### 2d. Git Processes

```bash
ps aux | grep -E '[g]it|[c]laude' | head -20 > "$DIAG_DIR/04-processes.txt" 2>&1
```

#### 2e. Recent Erk Commands

```bash
if [ -f ~/.erk/command_history.jsonl ]; then
    tail -200 ~/.erk/command_history.jsonl > "$DIAG_DIR/05-erk-history.jsonl"
else
    echo "No erk command history found" > "$DIAG_DIR/05-erk-history.jsonl"
fi
```

#### 2f. Git Config

```bash
git config --list --show-origin > "$DIAG_DIR/06-git-config.txt" 2>&1
```

#### 2g. Worktree Info

```bash
git worktree list > "$DIAG_DIR/07-worktree-list.txt" 2>&1
pwd >> "$DIAG_DIR/07-worktree-list.txt"
```

#### 2h. Git Reflog

Capture recent git operations to understand what was happening around the time of the error:

```bash
git reflog --date=iso -n 50 > "$DIAG_DIR/08-git-reflog.txt" 2>&1
```

#### 2i. Session ID

The session ID is provided by the skill loader via string substitution. Write it to a file:

```bash
echo "${CLAUDE_SESSION_ID}" > "$DIAG_DIR/09-session-id.txt"
```

#### 2j. Session XML Content

Preprocess the current session to compressed XML format for analysis. The session ID `${CLAUDE_SESSION_ID}` is substituted by the skill loader:

```bash
SESSION_FILE=$(find ~/.claude/projects -name "${CLAUDE_SESSION_ID}.jsonl" 2>/dev/null | head -1)
if [ -n "$SESSION_FILE" ] && [ -f "$SESSION_FILE" ]; then
    erk exec preprocess-session "$SESSION_FILE" --max-tokens 100000 --stdout > "$DIAG_DIR/10-session.xml"
else
    echo "Session file not found for ID: ${CLAUDE_SESSION_ID}" > "$DIAG_DIR/10-session.xml"
fi
```

This captures the conversation leading up to the error, including tool calls and results (typically ~45-100KB after compression).

### Step 3: Create Gist

Upload all files as a gist:

```bash
gh gist create --desc "Git index.lock diagnostic report - $(date +%Y-%m-%d-%H%M%S)" "$DIAG_DIR"/*
```

Capture the gist URL from the output.

### Step 4: Cleanup

```bash
rm -rf "$DIAG_DIR"
```

### Step 5: Report

Display the result:

```markdown
## Diagnostic Report Created

**Gist URL**: <gist_url>

The diagnostic report has been uploaded. Share this URL when reporting the issue.

### Files Included

1. `01-error-context.txt` - The error message and context
2. `02-git-status.txt` - Current git status
3. `03-lock-state.txt` - Lock file existence and details
4. `04-processes.txt` - Running git/claude processes
5. `05-erk-history.jsonl` - Recent erk command history
6. `06-git-config.txt` - Git configuration
7. `07-worktree-list.txt` - Git worktree information
8. `08-git-reflog.txt` - Recent git operations (reflog with timestamps)
9. `09-session-id.txt` - Claude Code session ID
10. `10-session.xml` - Preprocessed session XML (conversation leading to error)
```

## Notes

- This command requires `gh` CLI to be authenticated
- The gist is created as a secret (not public) by default
- Run this command immediately after encountering the error for best results
- The error context must be visible in the current conversation

## Common Causes

- **Stale lock (0 bytes)**: A git process crashed or was killed, leaving an empty lock file
- **Parallel operations**: Multiple Claude sessions or erk commands running git operations simultaneously
- **Worktree conflicts**: Operations across worktrees can sometimes conflict
- **Interrupted operations**: Ctrl+C during git operations can leave stale locks

## Quick Fix

If the lock file is 0 bytes (stale), it's safe to remove:

```bash
rm <lock-file-path>
```
