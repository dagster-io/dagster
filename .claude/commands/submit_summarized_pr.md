# Submit Summarized PR

Submit a PR with an AI-generated summary by squashing the current branch, generating a summary, and creating/updating a draft PR.

## Quick Usage

Use the optimized Python CLI for best performance:

```bash
# Main functionality - submit the PR
dagster-claude-commands submit-summarized-pr submit

# Test/preview - generate summary without creating PR
dagster-claude-commands submit-summarized-pr print-pr-summary

# Test title generation only
dagster-claude-commands submit-summarized-pr print-pr-title
```

### Submit Subcommand Options

- `--dry-run`: Preview what would be done without executing
- `--no-squash`: Skip squashing commits (useful if already squashed)

### Available Subcommands

- **`submit`**: Execute the full PR submission workflow (main functionality)
- **`print-pr-summary`**: Generate and display PR summary without creating a PR (for testing)
- **`print-pr-title`**: Generate and display PR title only (for testing title generation)

## What it does:

### `submit` subcommand workflow:

1. **Validates prerequisites**: Checks git repo, CLI tools, and branch status
2. **Squashes commits**: Combines all commits in current branch (unless `--no-squash`)
3. **Generates PR summary**: Creates summary from commit messages and diff using template
4. **Updates commit message**: Amends commit with generated summary
5. **Creates/updates draft PR**: Uses Graphite to submit draft PR
6. **Updates PR metadata**: Sets title and body via GitHub CLI

### `print-pr-summary` subcommand workflow:

1. **Validates prerequisites**: Checks git repo, CLI tools, and branch status
2. **Generates PR summary**: Creates summary from commit messages and diff using template
3. **Displays summary**: Outputs the generated summary to stdout for review

## Requirements

- Must be run from within a git repository
- Requires Graphite CLI (`gt`) to be installed
- Requires GitHub CLI (`gh`) to be installed
- Cannot be run on master/main branches
- Current branch must be part of a Graphite stack

## Error Handling

The CLI provides comprehensive validation and error handling:

- Pre-flight validation of all requirements
- Clear error messages with specific recovery guidance
- Handles edge cases (single commits, missing tools, etc.)
- Atomic operations to avoid inconsistent repository state

## Performance

The Python CLI is **5-10x faster** than shell-based implementations and provides better error handling and user feedback.
