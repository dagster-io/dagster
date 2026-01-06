---
description: Save the current session's plan to GitHub as an issue
---

# /erk:plan-save

Save the current session's plan to GitHub as an issue with session context.

## Issue Structure

The created issue has a specific structure:

- **Issue body**: Contains only the metadata header (schema version, timestamps, etc.)
- **First comment**: Contains the actual plan content

This separation keeps machine-readable metadata in the body while the human-readable plan is in the first comment.

## Agent Instructions

### Step 1: Extract Session ID

Get the session ID from the `SESSION_CONTEXT` reminder in your conversation context.

### Step 2: Run Save Command

Run this command with the extracted session ID:

```bash
erk exec plan-save-to-issue --format display --session-id="<session-id-from-step-1>"
```

### Step 3: Display Results

On success, **copy the command output exactly as printed**. This is critical:

- Do NOT paraphrase or summarize
- Do NOT add bullet points or change formatting
- Do NOT omit any lines (especially the `--dangerous` option)
- Show the output in a code block to preserve formatting

On failure, display the error message and suggest:

- Checking that a plan exists (enter Plan mode and exit it first)
- Verifying GitHub CLI authentication (`gh auth status`)
- Checking network connectivity
