# CLI Reference

## Overview

The dagster_docs module provides two CLI interfaces available through the `dagster-docs` command:

1. **Simple Interface**: Direct docstring validation for development
2. **Complex Interface**: Comprehensive validation commands with subcommands

## Installation

The `dagster-docs` CLI is installed as part of the automation package:

```bash
# Install from Dagster repository root
cd /path/to/dagster
make dev_install  # This installs the dagster-docs CLI

# Verify installation
dagster-docs --help
```

## Simple Interface

### Basic Usage

```bash
dagster-docs SYMBOL_PATH [OPTIONS]
```

### Arguments

- `SYMBOL_PATH`: Dotted path to the Python symbol (e.g., 'dagster.asset', 'dagster.OpDefinition')

### Options

- `--verbose, -v`: Enable verbose output with detailed error traces
- `--all-public`: Validate all top-level exported symbols in the specified module
- `--public-methods`: Validate all @public-annotated methods on top-level exported classes
- `--watch`: Watch the file containing the symbol for changes and re-validate automatically

### Examples

```bash
# Validate single symbol
dagster-docs dagster.asset

# Validate with verbose output
dagster-docs dagster.asset --verbose

# Validate all public symbols in dagster module
dagster-docs dagster --all-public

# Validate all @public methods in dagster module
dagster-docs dagster --public-methods

# Watch mode for development
dagster-docs dagster.asset --watch
```

### Watch Mode

Watch mode monitors the source file containing the symbol and automatically re-validates when changes are detected:

- Real-time validation during development
- Debounced change detection (avoids rapid re-validation)
- Graceful shutdown with Ctrl+C
- Optional debug output showing file system events

## Complex Interface

### Main Command

```bash
dagster-docs [COMMAND] [SUBCOMMAND] [OPTIONS]
```

## Commands

### check

Comprehensive documentation validation commands.

#### check docstrings

Validate Python docstrings using Sphinx parsing pipeline.

```bash
dagster-docs check docstrings [OPTIONS]
```

**Options (exactly one required):**

- `--changed`: Validate docstrings in changed files only
- `--symbol SYMBOL`: Validate specific symbol (e.g., 'dagster.asset')
- `--all`: Check all docstrings (not implemented yet)
- `--package PACKAGE`: Validate all public symbols in package

**Examples:**

```bash
# Check changed files only
dagster-docs check docstrings --changed

# Check specific symbol
dagster-docs check docstrings --symbol dagster.asset

# Check all public symbols in package
dagster-docs check docstrings --package dagster
```

#### check rst-symbols

Check that all symbols in RST files have corresponding `@public` decorators and top-level exports.

```bash
dagster-docs check rst-symbols [OPTIONS]
```

**Options (one required):**

- `--all`: Check all RST symbols (with exclude lists applied)
- `--package PACKAGE`: Filter to a particular package

**Examples:**

```bash
# Check all RST symbols
dagster-docs check rst-symbols --all

# Check specific package
dagster-docs check rst-symbols --package dagster
```

#### check public-symbols

Check that all `@public` classes and functions are documented in RST files and exported at top-level.

```bash
dagster-docs check public-symbols [OPTIONS]
```

**Options (one required):**

- `--all`: Check all @public symbols (with exclude lists applied)
- `--package PACKAGE`: Filter to a particular package

**Examples:**

```bash
# Check all @public symbols
dagster-docs check public-symbols --all

# Check specific package
dagster-docs check public-symbols --package dagster
```

#### check exports

Bidirectional check ensuring consistency between RST documentation and @public decorators.

```bash
dagster-docs check exports [OPTIONS]
```

**Options (one required):**

- `--all`: Check all exports (with exclude lists applied)
- `--package PACKAGE`: Filter to a particular package

**Examples:**

```bash
# Check all exports bidirectionally
dagster-docs check exports --all

# Check specific package
dagster-docs check exports --package dagster
```

#### check exclude-lists

Audit exclude lists to find entries that can be removed (symbols that now comply).

```bash
dagster-docs check exclude-lists [OPTIONS]
```

**Options (at least one required):**

- `--missing-public`: Audit EXCLUDE_MISSING_PUBLIC for symbols that now have @public decorators
- `--missing-rst`: Audit EXCLUDE_MISSING_RST for symbols that now have RST documentation
- `--missing-export`: Audit EXCLUDE_MISSING_EXPORT for symbols that are now exported at top-level

**Examples:**

```bash
# Audit all exclude lists
dagster-docs check exclude-lists --missing-public --missing-rst --missing-export

# Audit specific exclude list
dagster-docs check exclude-lists --missing-public
```

### ls

List symbols and their validation status (implementation in `commands/ls.py`).

```bash
dagster-docs ls [OPTIONS]
```

### watch

File watching capabilities for continuous validation (implementation in `commands/watch.py`).

```bash
dagster-docs watch [OPTIONS]
```

## Exit Codes

All commands follow standard Unix exit code conventions:

- **0**: Success, no issues found
- **1**: Validation errors found or command failed
- **2**: Usage error (invalid arguments, not in git repo, etc.)

## Output Formats

### Docstring Validation Output

```
Validating docstring for: dagster.asset

ERRORS:
  - Section header 'Args:' not followed by blank line
  - Invalid RST syntax on line 15

WARNINGS:
  - No docstring found

✗ Docstring validation failed
```

### Public API Validation Output

```
Found 5 issues:
  missing_rst: dagster.ComponentTypeSpec - Symbol marked @public but not documented in RST files
  missing_export: dagster.components.core.context.ComponentLoadContext - Symbol marked @public but not available as top-level export
  missing_public: dagster.BetaWarning - Symbol documented in RST but missing @public decorator
```

### Exclude List Audit Output

```
Found 3 symbols in EXCLUDE_MISSING_PUBLIC that now have @public decorators:
These entries can be removed from the exclude list:

  dagster.AssetSelection
  dagster.ConfigMapping
  dagster.DependencyDefinition

To remove these entries, edit:
  python_modules/automation/automation/docstring_lint/exclude_lists.py
```

## Common Patterns

### Development Workflow

```bash
# Start with watch mode for active development
dagster-docs dagster.asset --watch

# Check your changes before committing
dagster-docs check docstrings --changed

# Full consistency check
dagster-docs check exports --all
```

### CI/CD Integration

```bash
# Quick check for changed files
dagster-docs check docstrings --changed

# Full validation (use in comprehensive CI)
dagster-docs check exports --all
```

### Maintenance Workflow

```bash
# Regular audit of exclude lists
dagster-docs check exclude-lists --missing-public --missing-rst --missing-export

# Package-specific validation
dagster-docs check docstrings --package dagster_aws
```

## Environment Requirements

- Must be run from within the Dagster repository root
- Git repository required for `--changed` option
- Python environment with Dagster dependencies installed
- Access to `python_modules/` directory structure

## Performance Notes

- Single symbol validation: ~100-500ms
- Package validation: ~1-10s depending on package size
- Full repository validation: ~30-60s
- Watch mode: Near-instant re-validation after file changes
- Changed files validation: ~1-5s depending on number of changed files
