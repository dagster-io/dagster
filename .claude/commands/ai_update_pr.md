# AI Update PR summary

## Step 0: Always Inspect Repository State First

**CRITICAL**: It is essential to disregard any context about what branch you think you are on. ALWAYS start by inspecting the current state of the repository and GT stack to determine where you actually are.

**NEVER assume** you know the current branch or stack position based on previous context or conversation history. The repository state may have changed.

**Required commands to run first (EXECUTE SERIALLY, NOT IN PARALLEL)**:

1. `git branch --show-current` - Get the actual current branch name
2. `gt ls -s` - Get the actual current stack structure
3. `git status` - Verify repository state
4. `gh pr view` - Verify that a PR on gh exists. If it does not, tell user to submit using gt submit.
5. `gt ls -s` - Verify that branch is being tracked by graphite.
6. `gt squash --no-interactive` - Squash commits. If there is a merge conflict, tell the user to do it manually and exit
7. `gt submit --no-interactive` - Submit only this branch.

**CRITICAL**: Execute these commands one at a time, waiting for each to complete before running the next. Do NOT use parallel bash execution as this can cause git index locking issues.

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

**CRITICAL**: Execute these git commands serially (one at a time) to avoid git index locking issues.

**Verification**: The `git log --oneline <previous_branch>..HEAD` command should typically show only 1-2 commits for the current branch. If it shows many commits, double-check that you identified the correct previous branch.

## Step 3: Write PR Summary

Focus only on changes in the current branch, not the entire stack history. Use this context, alongside any session context from what you know about the changes to write a PR summary in Markdown, of the format

```md
## Summary & Motivation

[Brief summary of changes here, including code sample, if a new API was added, etc.]

## How I Tested These Changes

[Very brief summary of test plan here, e.g. "New unit tests.", "New integration tests.", "Existing test suite." This can be a single sentence.]

## Changelog

[End user facing changelog entry, remove this section if no public-facing API was changed and no bug was fixed. Public-facing APIs are identified by the @public decorator. Internal tools like CLIs meant for developer use should not have changelog entries. If there are no user-facing changes, remove this section.]
```

Use bullet points sparingly, and do not overuse italics/bold text. Use short sentences.

After generating the PR summary markdown, use the `dagster-dev update-pr-and-commit` command to atomically update both the GitHub PR and local commit message:

```bash
dagster-dev update-pr-and-commit --title "generated_title" --body "generated_summary"
```

This command safely handles all PR and commit updates in the correct serial order to prevent git index locking issues. It will:

1. Verify the PR exists (exit with error if not)
2. Update the PR title
3. Update the PR body
4. Update the local commit message (title + body)
5. Display the Graphite URL

The command automatically handles error checking and provides clear feedback at each step.

## Step 4: Complete

The `dagster-dev update-pr-and-commit` command automatically displays the Graphite URL upon successful completion, so no additional steps are required.
