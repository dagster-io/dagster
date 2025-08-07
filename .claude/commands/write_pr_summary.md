# Write PR summary

Use `gt ls -s` to determine the last git ref in the stack. View all changes since that ref with `git diff`. Also view the commit messages with `git log`. Use this context, alongside any session context from what you know about the changes to write a PR summary in Markdown, of the format

```md
## Summary & Motivation

[Brief summary of changes here, including code sample, if a new API was added, etc.]

## How I Tested These Changes

[Very brief summary of test plan here, e.g. "New unit tests.", "New integration tests.", "Existing test suite." This can be a single sentence.]

## Changelog

[End user facing changelog entry, remove this section if no public-facing API was changed and no bug was fixed. Public-facing APIs are identified by the @public decorator. Ignore minor changes. If there are no user-facing changes, remove this section.]
```

Use bullet points sparingly, and do not overuse italics/bold text. Use short sentences. Output the new markdown to the user so they can copy and paste it into the PR.
