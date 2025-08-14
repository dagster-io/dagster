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

After generating the PR summary markdown, check if there is a current PR for this branch using `gh pr view` or similar command. If there is no PR, error and tell the user to create a PR first. If there is a PR, update it with the generated summary using `gh pr edit --body "generated_summary"` and also generate a concise, descriptive title based on the summary content and update it using `gh pr edit --title "generated_title"` or similar GitHub CLI command.

Additionally, update the latest commit message in the branch with the contents of the PR summary using `git commit --amend -m "new_commit_message"` where the new commit message is derived from the PR summary title and content.

**CRITICAL - SERIAL EXECUTION REQUIRED**: All git and gh commands in Step 3 must be executed one at a time in this order:

1. `gh pr view` - Check for existing PR
2. `gh pr edit --title "..."` - Update PR title
3. `gh pr edit --body "..."` - Update PR body
4. `git commit --amend -m "..."` - Update commit message

**NEVER execute these commands in parallel** as they can cause git index locking conflicts. Wait for each command to complete before executing the next one. If git lock errors occur, use: `rm -f .git/index.lock && sleep 1` before retrying.

## Step 4: Display Graphite URL

After successfully updating the PR, always display the Graphite URL for easy access:

```bash
echo "🔗 Graphite PR View: https://app.graphite.dev/github/pr/dagster-io/dagster/[PR_NUMBER]/"
```

Replace `[PR_NUMBER]` with the actual PR number from the `gh pr view` output.
