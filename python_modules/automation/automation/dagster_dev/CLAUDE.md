# Dagster Dev CLI Development Guide

## Command File Naming Convention

**IMPORTANT**: Command files in the `commands/` directory should be named after the actual command they implement, not generic names.

### Naming Rules

- File names should match the command name defined in the `@click.command()` decorator
- Use lowercase names with underscores for multi-word commands (e.g., `build_assets.py` for a `build-assets` command)
- Avoid generic names like `example.py`, `test.py`, or `utils.py`

### Examples

```python
# ✅ GOOD: greet.py
@click.command(name="greet")
def greet():
    """Greet someone with a customizable message."""
    pass

# ✅ GOOD: build_assets.py
@click.command(name="build-assets")
def build_assets():
    """Build Dagster assets."""
    pass

# ❌ BAD: example.py, utils.py, helper.py
```

### Rationale

- Makes it easy to find the implementation for a specific command
- Self-documenting file structure
- Consistent with CLI best practices
- Helps maintain the codebase as commands grow
