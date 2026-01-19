---
name: erk-diff-analysis
description: Internal skill for commit message generation. Only load when explicitly requested by name or invoked by commands.
---

# Diff Analysis

This skill provides the commit message generation prompt used by PR submission commands.

## When to Use

Only load this skill when:

- Explicitly requested by name (`erk-diff-analysis`)
- Invoked by commands like `/erk:git-pr-push`

## Usage

Load `references/commit-message-prompt.md` when analyzing a diff, then apply its principles to generate output.

## Key Principles

- Be concise and strategic - focus on significant changes
- Use component-level descriptions - reference modules/components, not individual functions
- Highlight breaking changes prominently
- Note test coverage patterns
- Use relative paths from repository root
