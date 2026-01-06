# Prompt Hooks

Prompt hooks are markdown files that provide instructions to AI agents at specific points in your erk workflows.

## What Are Prompt Hooks?

Unlike Claude Code hooks (which execute shell commands at lifecycle events), prompt hooks are **AI-readable documentation** that:

- Execute at specific workflow points (e.g., after plan implementation)
- Provide project-specific instructions to AI agents
- Customize AI behavior without code changes
- Are version-controlled with your project

## Available Hooks

| Hook File                   | Fires When                                           | Purpose                                   |
| --------------------------- | ---------------------------------------------------- | ----------------------------------------- |
| `post-plan-implement-ci.md` | After `/erk:plan-implement` completes implementation | Define CI workflow and iteration strategy |

## Creating a Prompt Hook

1. Create a markdown file in `.erk/prompt-hooks/` with the appropriate name
2. Write instructions for the AI agent in imperative mood
3. Include specific commands, tools to load, and success criteria
4. Reference skills to load (e.g., `Load the \`ci-iteration\` skill`)

### Example: post-plan-implement-ci.md

\`\`\`markdown

# Post-Implementation CI

Run CI validation after plan implementation using \`make fast-ci\`.

Load the \`ci-iteration\` skill for the iterative fix workflow.

## Iteration Process

1. Run \`make fast-ci\` via devrun agent
2. If checks fail: apply targeted fixes
3. Re-run CI (max 5 iterations)
4. On success: proceed to PR creation
   \`\`\`

## Best Practices

- **Be specific:** Provide exact commands and tool names
- **Define success:** Clear exit criteria prevent infinite loops
- **Reference skills:** Load relevant skills for specialized workflows
- **Version control:** Commit hooks alongside code
- **Document context:** Explain WHY the workflow exists

## Customization

These are **erk-defined hooks that you can customize** for your project's needs:

- Modify existing hooks to match your CI/CD setup
- Add project-specific validation steps
- Reference your custom skills and commands
- Adjust iteration limits and error handling

## Future Hooks

Potential hooks for future workflows (create these as needed):

- `pre-plan-implement.md` - Setup before implementation starts
- `post-pr-create.md` - After PR creation workflow
- `pre-worktree-create.md` - Validation before worktree setup
