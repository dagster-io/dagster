"""Constants and shared configuration for scaffold branch operations.

This module contains constants that are shared across different modules
to avoid circular dependencies.
"""

from typing import Literal, get_args

# Type alias for valid AI model names
ModelType = Literal["opus", "sonnet", "haiku"]

# Allowed commands for different operation types

ALLOWED_COMMANDS_SCAFFOLDING = [
    "Bash(dg scaffold defs:*)",
    "Bash(dg list defs:*)",
    "Bash(dg list components:*)",
    "Bash(dg check yaml:*)",
    "Bash(dg check defs:*)",
    "Bash(dg list env:*)",
    "Bash(dg utils inspect-component:*)",
    "Bash(dg docs integrations:*)",
    "Bash(uv add:*)",
    "Bash(uv sync:*)",
    # update yaml files
    "Edit(**/*defs.yaml)",
    "Replace(**/*defs.yaml)",
    "Update(**/*defs.yaml)",
    "Write(**/*defs.yaml)",
    "Edit(**/*NEXT_STEPS.md)",
    "Replace(**/*NEXT_STEPS.md)",
    "Update(**/*NEXT_STEPS.md)",
    "Write(**/*NEXT_STEPS.md)",
    "Bash(touch:*)",
]


# Valid AI model names derived from the type alias
VALID_MODELS = set(get_args(ModelType))


ALLOWED_COMMANDS_PLANNING = [
    # Read-only file operations
    "Read(**/*.py)",
    "Read(**/*.yaml)",
    "Read(**/*.yml)",
    "Read(**/*.md)",
    "Read(**/*.json)",
    "Glob(**/*)",
    # Read-only dg commands for analysis
    "Bash(dg list defs:*)",
    "Bash(dg list components:*)",
    "Bash(dg utils inspect-component:*)",
    "Bash(dg docs integrations:*)",
    "Bash(dg list env:*)",
    # Git commands for understanding repository state
    "Bash(git log:*)",
    "Bash(git status:*)",
    "Bash(git branch:*)",
    "Bash(git diff:*)",
    # Directory listing for structure analysis
    "LS(**/*)",
]
