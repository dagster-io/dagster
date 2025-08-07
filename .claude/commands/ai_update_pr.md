# AI Update PR summary

## Step 0: Always Inspect Repository State First

**CRITICAL**: It is essential to disregard any context about what branch you think you are on. ALWAYS start by inspecting the current state of the repository and GT stack to determine where you actually are.

**NEVER assume** you know the current branch or stack position based on previous context or conversation history. The repository state may have changed.

**Required commands to run first**:
- `git branch --show-current` - Get the actual current branch name
- `gt ls -s` - Get the actual current stack structure
- `git status` - Verify repository state

Only after confirming the actual repository state should you proceed with the remaining steps.

## Step 1: Identify the Previous Branch

First, use `gt ls -s` to view the stack structure. The output shows branches in order, with `◉` marking the current branch and `◯` marking other branches in the stack.

**CRITICAL**: The previous branch is the one that appears immediately AFTER the `◉` (current branch) in the `gt ls -s` output.

Example:

```
◉  feature/current-branch     <- Current branch (HEAD)
◯  feature/previous-branch    <- This is the previous branch to use
◯  feature/older-branch       <- NOT this one
◯  master
```

In this example, you would use `feature/previous-branch` as the `<previous_branch>`.

## Step 2: Get Changes for Current Branch Only

View changes for ONLY the current branch with `git diff <previous_branch>..HEAD` where `<previous_branch>` is the branch identified in Step 1. Also view the commit messages for the current branch only with `git log --oneline <previous_branch>..HEAD`.

**Verification**: The `git log --oneline <previous_branch>..HEAD` command should typically show only 1-2 commits for the current branch. If it shows many commits, double-check that you identified the correct previous branch.

## Step 3: Write PR Summary

Focus only on changes in the current branch, not the entire stack history. Use this context, alongside any session context from what you know about the changes to write a PR summary in Markdown, of the format

```md
## Summary & Motivation

[Brief summary of changes here, including code sample, if a new API was added, etc.]

## How I Tested These Changes

[Very brief summary of test plan here, e.g. "New unit tests.", "New integration tests.", "Existing test suite." This can be a single sentence.]

## Changelog

[End user facing changelog entry, remove this section if no public-facing API was changed and no bug was fixed. Public-facing APIs are identified by the @public decorator. Ignore minor changes. If there are no user-facing changes, remove this section.]
```

Use bullet points sparingly, and do not overuse italics/bold text. Use short sentences.

After generating the PR summary markdown, check if there is a current PR for this branch using `gh pr view` or similar command. If there is no PR, error and tell the user to create a PR first. If there is a PR, update it with the generated summary using `gh pr edit --body "generated_summary"` and also generate a concise, descriptive title based on the summary content and update it using `gh pr edit --title "generated_title"` or similar GitHub CLI command.

Additionally, update the latest commit message in the branch with the contents of the PR summary using `git commit --amend -m "new_commit_message"` where the new commit message is derived from the PR summary title and content.
