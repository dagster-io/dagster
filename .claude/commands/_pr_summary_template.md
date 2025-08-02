# PR Summary Template

This template is shared by `write_pr_summary.md` and `submit_summarized_pr.md` to ensure consistency.

## Context Gathering

Use `gt ls -s` to determine the last git ref in the stack. View all changes since that ref with `git diff`. Also view the commit messages with `git log`. Use this context, alongside any session context from what you know about the changes to write a PR summary.

## Output Format

```md
## Summary & Motivation

[Brief summary of changes here, including code sample, if a new API was added, etc.]

## How I Tested These Changes

[Very brief summary of test plan here, e.g. "New unit tests.", "New integration tests.", "Existing test suite." This can be a single sentence.]

## Changelog

[End user facing changelog entry, remove this section if no public-facing API was changed and no bug was fixed. Public-facing APIs are identified by the @public decorator. Ignore minor changes. If there are no user-facing changes, remove this section.]
```

## Style Guidelines

Use bullet points sparingly, and do not overuse italics/bold text. Use short sentences.