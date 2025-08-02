# Dagster Claude Commands CLI

## Overview

This CLI provides structured Python implementations for functionality currently in `.claude/commands/*.md` files. It follows the same patterns as `dagster-docs` CLI for consistency.

## Architecture

### Directory Structure

```
automation/dagster_claude_commands/
├── __init__.py               # Main CLI entry point and command registration
├── CLAUDE.md                 # This documentation file
├── utils/                    # Shared utility modules (add as needed)
│   └── __init__.py
└── commands/                 # Individual command implementations (add as needed)
    └── __init__.py
```

### CLI Pattern

The main CLI is a Click group in `__init__.py`:

```python
import click

@click.group()
def main():
    """Dagster Claude Commands - Automated workflows for development."""
    pass
```

### Command Organization Patterns

#### Simple Commands

For simple standalone commands:

```python
# commands/my_command.py
import click

@click.command()
def my_command():
    """Description of what this command does."""
    click.echo("Command implementation")
```

#### Namespace Commands (Recommended)

For commands that correspond to `.claude/commands/*.md` files, use the **namespace subcommand pattern** where the namespace aligns with the claude command name:

```python
# commands/my_claude_command_group.py
import click

@click.group("my-claude-command")
def my_claude_command():
    """My Claude Command - command namespace."""
    pass

@my_claude_command.command("execute")
def execute():
    """Execute the main functionality (equivalent to the .md file)."""
    # Main implementation here
    pass

@my_claude_command.command("test")
def test():
    """Test/preview functionality without side effects."""
    # Testing implementation here
    pass
```

This creates a CLI structure like:

- `dagster-claude-commands my-claude-command execute` (main functionality)
- `dagster-claude-commands my-claude-command test` (testing/preview)

**Example: submit-summarized-pr namespace**

The `submit-summarized-pr` command follows this pattern:

```bash
# Main functionality (equivalent to running the .claude/commands/submit_summarized_pr.md)
dagster-claude-commands submit-summarized-pr submit [--dry-run] [--no-squash]

# Testing/preview (generates summary without creating PR)
dagster-claude-commands submit-summarized-pr print-pr-summary
```

This aligns the CLI namespace (`submit-summarized-pr`) with the claude command file name, making it intuitive for users familiar with the `.claude/commands/` structure.

#### Registration

Register commands in `__init__.py`:

```python
# For simple commands
from automation.dagster_claude_commands.commands.my_command import my_command
main.add_command(my_command)

# For namespace commands
from automation.dagster_claude_commands.commands.my_claude_command_group import my_claude_command
main.add_command(my_claude_command)
```

#### Installation

After adding new commands, reinstall the package:

```bash
cd python_modules/automation
uv pip install -e .
```

### Command Naming Convention

- Use hyphens in CLI commands: `dagster-claude-commands my-command`
- Use underscores in Python modules: `commands/my_command.py`
- Commands should mirror `.claude/commands/*.md` file names

### Utility Modules

Add utilities to `utils/` only when needed by multiple commands:

```python
# utils/git.py
def get_current_branch():
    """Get the current git branch."""
    # Implementation
```

Import utilities in command modules:

```python
from automation.dagster_claude_commands.utils.git import get_current_branch
```

### Error Handling Pattern

Follow this pattern for consistent error handling:

```python
import sys
import click

@click.command()
def my_command():
    try:
        # Command logic
        pass
    except SomeSpecificError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Unexpected error: {e}", err=True)
        sys.exit(1)
```

### External Tool Validation

When commands need external CLI tools, validate at runtime:

```python
import subprocess
import click

def check_tool_available(tool_name: str) -> bool:
    """Check if external CLI tool is available."""
    try:
        subprocess.run([tool_name, "--version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

@click.command()
def my_command():
    if not check_tool_available("gh"):
        click.echo("Error: GitHub CLI (gh) is required but not installed", err=True)
        sys.exit(1)
```

### Testing New Commands

Create tests in `automation_tests/dagster_claude_commands_tests/`:

- Mock external CLI tools using `unittest.mock`
- Test error conditions and edge cases
- Follow existing test patterns in the automation package

## Development Workflow

1. **Identify need**: A `.claude/commands/*.md` file would benefit from automation
2. **Create command**: Add command module and register it
3. **Implement utilities**: Add shared utilities if needed by multiple commands
4. **Test**: Add tests for the new command
5. **Reinstall**: Run `uv pip install -e .` to register the command
6. **Validate**: Test the command works as expected

## Integration with .claude/commands

Commands should:

- Provide the same functionality as their `.md` counterparts
- Be significantly faster (5-10x improvement target)
- Have better error handling and user feedback
- Support the same use cases and workflows

The `.md` files can eventually be updated to reference the CLI commands for better performance.

## Entry Point

The CLI is registered in `setup.py`:

```python
entry_points={
    "console_scripts": [
        "dagster-claude-commands = automation.dagster_claude_commands:main",
    ]
}
```

After any changes to entry points, reinstall the package. This is NOT necessary if you are just changing a subcommand.

```bash
cd python_modules/automation
uv pip install -e .
```
