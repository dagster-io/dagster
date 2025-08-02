# Submit Summarized PR

Submit a PR with an AI-generated summary by squashing the current branch, generating a summary, and creating/updating a draft PR.

This command integrates the logic from `write_pr_summary.md` into an automated workflow.

## Steps performed:

1. **Squash current branch**: Uses `gt squash --no-edit` to combine commits
2. **Generate PR summary**: Uses the same logic as `write_pr_summary.md`
3. **Update commit message**: Amends the commit with the generated summary
4. **Create/update draft PR**: Uses `gt submit -n -d` to create a draft PR
5. **Update PR title/body**: Uses `gh pr edit` to set the title and body

## PR Summary Generation

Follows the PR summary template in `_pr_summary_template.md`.

After generating the summary:

- Extract the first sentence from the "Summary & Motivation" section as the PR title
- Use the full summary as the PR body
- Create/update the draft PR with this title and body

## Requirements

- Must be run from within a git repository
- Requires Graphite CLI (`gt`) to be installed
- Requires GitHub CLI (`gh`) to be installed
- Cannot be run on master/main branches
- Current branch must be part of a Graphite stack

## Error Handling

- Validates git repository context
- Checks for required CLI tools
- Prevents execution on protected branches
- Handles cases where branch has only one commit (nothing to squash)
- Gracefully handles PR URL retrieval failures
