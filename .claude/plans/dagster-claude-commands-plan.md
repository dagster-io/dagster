# Dagster Claude Commands Implementation Plan

## Overview

This plan outlines the implementation of `dagster-claude-commands`, a new CLI tool to provide structured Python implementations for functionality currently in `.claude/commands/*.md` files. The focus is on creating a solid scaffolding that can be extended with specific commands as needed.

## Architecture Analysis: dagster-docs

The existing `dagster-docs` CLI provides an excellent pattern to follow:

```
automation/dagster_docs/
├── __init__.py
├── main.py              # Click group entry point
├── cli.py               # Individual command (legacy)
└── commands/
    ├── __init__.py
    ├── check.py         # Multi-subcommand group
    ├── ls.py            # Simple command
    └── watch.py         # Simple command
```

**Entry point structure in setup.py:**

```python
entry_points={
    "console_scripts": [
        "dagster-docs = automation.dagster_docs:main",
    ]
}
```

**Command patterns observed:**

1. **Simple commands** (`ls`, `watch`) - Single functionality
2. **Command groups** (`check`) - Multiple related subcommands
3. **Rich CLI options** - Boolean flags, optional parameters, argument validation
4. **Comprehensive error handling** - Graceful failures with helpful messages

## Proposed Architecture: dagster-claude-commands

### Directory Structure

```
automation/dagster_claude_commands/
├── __init__.py               # Package init and main entry point
├── utils/                    # Shared utility modules (add as needed)
│   └── __init__.py
└── commands/                 # Individual command implementations (add as needed)
    └── __init__.py
```

### Command Structure

Commands will be added as needed to mirror `.claude/commands/` functionality. Each command will be a simple Click command that can be imported and registered with the main CLI group.

## Implementation Strategy

### Phase 1: Basic Scaffolding

1. Create minimal package structure
2. Set up main CLI entry point with Click
3. Add entry point to setup.py
4. Test basic CLI functionality (`dagster-claude-commands --help`)

### Phase 2: Command-by-Command Addition

Commands will be added incrementally as needed:

1. Create command module in `commands/`
2. Implement command logic
3. Register command with main CLI
4. Add any required utilities to `utils/`

### Extensible Architecture

- Each command is self-contained
- Utilities added only when needed
- Main CLI dynamically discovers and registers commands

## Installation and Setup

### Entry Point Configuration

Add to `setup.py`:

```python
entry_points={
    "console_scripts": [
        "dagster-image = automation.docker.cli:main",
        "dagster-graphql-client = automation.graphql.python_client.cli:main",
        "dagster-docs = automation.dagster_docs:main",
        "dagster-claude-commands = automation.dagster_claude_commands:main",  # NEW
    ]
}
```

### Installation Steps

After implementation:

```bash
cd python_modules/automation
uv pip install -e .  # Reinstall to register new entry point
```

### Dependencies

- `click` (already present in setup.py)
- Standard library modules (`subprocess`, `pathlib`)
- External CLI tools will be validated at runtime as needed

## Basic CLI Structure

The main CLI will be a simple Click group:

```python
import click

@click.group()
def main():
    """Dagster Claude Commands - Automated workflows for development."""
    pass

if __name__ == "__main__":
    main()
```

Commands are added by importing and registering them:

```python
# In __init__.py
from automation.dagster_claude_commands.commands.example import example_command

main.add_command(example_command)
```

## Next Steps

1. Create basic package structure
2. Add entry point to setup.py
3. Test CLI installation and help output
4. Add first command when needed
