# AI Update PR (Subagent-Optimized)

Use the specialized PR Update Expert agent to handle the complete AI-assisted PR workflow with optimized context management.

Use the Task tool to invoke the `pr-update-expert` subagent:

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
