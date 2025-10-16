# Enforce Standards Command

## Step 0: Stack Preparation with Merge Conflict Detection

**CRITICAL**: Before running the code standards enforcer, we must prepare the stack properly and abort if there are merge conflicts.

**Sequential commands (must be run in order):**

1. `gt squash` - Squash commits in the current branch for cleaner history
2. `gt restack` - Ensure the stack is properly synced and up-to-date

**Important**: These commands must be run sequentially, not in parallel. If either command fails due to merge conflicts, abort the entire operation and inform the user that merge conflicts must be resolved manually before running standards enforcement.

**Merge Conflict Detection**:

- If `gt squash` fails with merge conflicts, abort and tell user to resolve conflicts first
- If `gt restack` fails with merge conflicts, abort and tell user to resolve conflicts first
- Only proceed to standards enforcement if both commands succeed without conflicts

## Step 1: Invoke Code Standards Enforcer Agent

After successful stack preparation, use the Task tool to launch the code-standards-enforcer agent with the following configuration:

**Agent Type**: `code-standards-enforcer`

**Task Description**: "Audit changed files for standards compliance"

**Detailed Prompt**:

```
Please perform a comprehensive audit of all changed files in the current PR against the coding standards defined in CLAUDE.md.

Focus on:
1. Files that have been modified in the current branch compared to the base branch
2. Compliance with coding conventions from .claude/coding_conventions.md
3. Adherence to development workflow requirements from .claude/dev_workflow.md
4. Proper use of type annotations and @record decorators
5. Code quality requirements including mandatory `make ruff` execution

After the audit, provide:
- A summary of any standards violations found
- Specific recommendations for fixes
- List of files that need attention
- Confirmation that mandatory code quality checks (make ruff) have been run

If no violations are found, confirm that all changed files comply with the project's coding standards.
```

## Error Handling

If the stack preparation fails:

1. Stop execution immediately
2. Inform the user about the specific conflict
3. Provide guidance on resolving the merge conflicts
4. Do not proceed with standards enforcement until conflicts are resolved

## Success Criteria

The command succeeds when:

1. `gt squash` completes without merge conflicts
2. `gt restack` completes without merge conflicts
3. Code standards enforcer agent completes its audit
4. Any identified violations are reported to the user
