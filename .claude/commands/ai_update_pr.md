# AI Update PR (Subagent-Optimized)

Use the specialized PR Update Expert agent to handle the complete AI-assisted PR workflow with optimized context management.

<<<<<<< HEAD
Use the Task tool to invoke the `pr-update-expert` subagent:
=======
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

**CRITICAL**: If `gt squash` or `gt submit` encounters merge conflicts, HALT the entire ai_update_pr process immediately. Do NOT attempt to resolve conflicts automatically. Instead:

1. Inform the user about the conflict and which files are affected
2. Tell them to resolve conflicts manually using `gt add -A` and `gt continue`
3. Advise them to re-run the ai_update_pr command after resolving conflicts
4. Do NOT proceed with any further steps until conflicts are resolved

Only after confirming the actual repository state AND successful operations should you proceed with the remaining steps.

## Step 1: Identify the Previous Branch

First, use `gt ls -s` to view the stack structure. The output shows branches in order, with `◉` marking the current branch and `◯` marking other branches in the stack.

**CRITICAL**: The previous branch is the one that appears immediately AFTER the `◉` (current branch) in the `gt ls -s` output.

Example:

> > > > > > > 2760d880dc (Implement dg plus api run events command with comprehensive run API design)

```
I'll update your PR using the optimized AI workflow that handles repository analysis, thesis collection, and PR body generation with improved context management.
```

The agent will:

1. **Repository Analysis**: Execute `dagster-dev ai-review-analyze --json --minimal --smart-summary` for optimized state checking
2. **Thesis Management**: Handle existing thesis detection and interactive collection
3. **AI Analysis**: Generate structured PR summaries with human-AI content separation, adapting detail level based on change complexity:

   **CRITICAL BREVITY REQUIREMENTS:**
   - **NEVER replicate diff content** - summaries should capture intent, not implementation details
   - **Maximum 2-3 sentences** for simple to medium changes
   - **Focus on WHY and WHAT, not HOW** - avoid line-by-line analysis
   - **Default to concise** - err on the side of too brief rather than too verbose

   **Complexity Guidelines:**
   - **Simple changes** (single-line fixes, typos, minor tweaks): 1 sentence maximum
   - **Technical fixes** (import reorganization, compatibility fixes, lazy loading): 1-2 sentences describing the high-level approach, NO file-by-file breakdowns
   - **Medium changes** (function additions, config updates, isolated features): 2-3 sentences with key impact points
   - **Complex changes** (architectural changes, multiple classes/functions, cross-cutting concerns): Brief paragraph focusing on architectural decisions, not implementation specifics
   - **Large but simple changes** (file splits, refactoring without logic changes): 1-2 sentences about structural intent, ignore line counts

4. **Atomic Updates**: Execute `dagster-dev ai-review-update --auto-prepare` with proper escaping

## Anti-Patterns to Avoid

**❌ NEVER DO THIS:**

- File-by-file change listings ("Updated file X to do Y, modified file Z to include W...")
- Line-by-line diff recreation ("Added import X, changed function Y from A to B...")
- Verbose implementation details that mirror the actual code changes
- Long bullet lists describing every small modification

**✅ INSTEAD DO THIS:**

- High-level purpose statements ("Improves error handling in authentication flow")
- Impact-focused descriptions ("Enables lazy loading to reduce startup time")
- Intent-based summaries ("Refactors validation logic for better maintainability")

## Key Benefits

- **Cost Optimization**: Smart diff summarization reduces token usage by 78%
- **Context Isolation**: PR workflow complexity handled in specialized agent context
- **Performance**: Single consolidated commands with intelligent analysis reduce overhead
- **User Experience**: Same interface, dramatically improved backend efficiency
- **Reliability**: Specialized error handling and validation logic
- **Scalability**: Caching system for repeat operations

## Commit Title Guidelines

**Maximum length**: 72 characters

**Suggested formats**:

- `Optimize /ai_update_pr with ai-review commands and user thesis input`
- `Add ai-review commands for optimized /ai_update_pr performance`
- `Improve /ai_update_pr efficiency with new ai-review- commands`

**Enforce with**: git commit --amend to shorten overly long titles before pushing.

The user experience remains identical while benefiting from optimized context management and specialized PR workflow expertise.
