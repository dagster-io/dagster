---
description:
  Create git commit and submit current branch with Graphite (squashes commits
  and rebases stack)
argument-hint: <description>
---

# Submit PR

Automatically create a git commit with a helpful summary message and submit the current branch as a pull request.

**Note:** This command squashes commits and rebases the stack. If you prefer a simpler workflow that preserves your commit history, use `/erk:git-pr-push` instead.

## Usage

```bash
# Invoke the command (description argument is optional but recommended)
/erk:pr-submit "Add user authentication feature"

# Without argument (will analyze changes automatically)
/erk:pr-submit
```

## Implementation

This command delegates to `erk pr submit` which handles everything:

- Preflight checks (auth, squash commits, submit to Graphite)
- AI-powered commit message generation
- PR metadata update with title and body
- PR validation

### Execute

Run the full submit workflow:

```bash
erk pr submit
```

### Report Results

The command outputs:

- PR URL
- Graphite URL
- Success message

## Error Handling

If `erk pr submit` fails, display the error and stop. The Python implementation handles all error cases including:

- Authentication issues (Graphite/GitHub)
- Merge conflicts
- No commits to submit
- Submission failures

Do NOT attempt to auto-resolve errors. Let the user fix issues and re-run.
