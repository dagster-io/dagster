# Write PR summary

Use `gt ls -s` to determine the last git ref in the stack. View all changes since that ref with `git diff`. Also view the commit messages with `git log`. Use this context, alongside any session context from what you know about the changes to write a PR summary in Markdown, of the format

```md
## Summary

[brief summary of changes here, including code sample, if a new API was added, etc.]

## Test Plan

[very brief summary of test plan here, e.g. "New unit tests.", "New integration tests.", "Existing test suite." This can be a single sentence.]

## Changelog

[end user facing changelog entry, remove this section if no public-facing API was changed and no bug was fixed. Ignore minor changes.]
```

Use bullet points sparingly, and do not overuse italics/bold text. Use short sentences.

Copy the md contents to the clipboard, using `pbcopy` on macos.
