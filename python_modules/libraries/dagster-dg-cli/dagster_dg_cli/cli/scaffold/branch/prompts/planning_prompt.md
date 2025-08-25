# PLANNING MODE - Generate Complete Branch Plan

You are in **PLANNING MODE**. Your task is to create a detailed execution plan for the following scaffolding request, but **DO NOT execute anything yet**.

## User Request

**"{user_input}"**

## Your Mission

Analyze the user's request above and create a comprehensive plan showing exactly what you would do if given permission to execute. This plan will be reviewed by the user before any Git operations or scaffolding occurs.

## Context Information

{context_info}

## Required Plan Format

Please provide your plan in this exact structure:

# 📋 COMPLETE EXECUTION PLAN

**Summary:** Brief description of what this plan will accomplish

**Proposed Branch Name:** `suggested-branch-name`
**Proposed PR Title:** "Descriptive title for the pull request"

**Project modifications:**

- New deps `uv add [package-name] [package-name]`
- New component: [ComponentType] at [path]
  - Scaffold with: `dg scaffold defs [ComponentType] [path]`
  - defs.yaml: [include entire yaml file surrounded by ``` if just a few lines, otherwise single sentence summary]
  - NEXT_STEPS.md: Documentation for how to complete and extend scaffolded implementation
- File edits:
  - [file]: [brief description of changes]

**Environment requirements:** [list any environment variables or setup needed, or "None" if no special requirements]

**Verification** Run `dg check defs` to verify definitions are valid

## Important Guidelines

1. **Be Concise**: Keep the plan focused on essential project modifications only
2. **Be Specific**: Include exact package names, component types, and file paths
3. **Be Realistic**: Only plan actions you can actually perform with your allowed tools
4. **YAML Files**: If the defs.yaml will be short (under 20 lines), include the entire content in ``` code blocks. Otherwise, provide a single sentence summary
5. **NEXT_STEPS.md**: Move all detailed capabilities, usage instructions, and final state descriptions to the NEXT_STEPS.md file. Do not include subbullets in the plan
6. **dg scaffold Workflow**: When planning component creation, always specify using `dg scaffold defs` commands to create components and defs.yaml files, then editing the generated files. Never plan to create defs.yaml files directly.
7. **DO NOT USE ExitPlanMode**: Simply provide your plan as regular text output. Do not use any tools that exit planning mode.
