# AI Update PR (Subagent-Optimized)

Use the specialized PR Update Expert agent to handle the complete AI-assisted PR workflow with optimized context management.

Use the Task tool to invoke the `pr-update-expert` subagent:

```
I'll update your PR using the optimized AI workflow that handles repository analysis, thesis collection, and PR body generation with improved context management.
```

The agent will:

1. **Repository Analysis**: Execute `dagster-dev ai-review-analyze --json --minimal --smart-summary` for optimized state checking
2. **Thesis Management**: Handle existing thesis detection and interactive collection
3. **AI Analysis**: Generate structured PR summaries with human-AI content separation
4. **Atomic Updates**: Execute `dagster-dev ai-review-update --auto-prepare` with proper escaping

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
