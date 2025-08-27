# dagster-docs CLI Utility

The `dagster-docs` command-line utility is a comprehensive tool for documentation inspection and validation in the Dagster codebase. It consolidates various documentation-related capabilities into a single, unified interface.

## Installation

The utility is automatically installed with the `automation` package:

This makes the `dagster-docs` command available system-wide.

## Command Structure

The CLI follows a hierarchical command structure with three main command groups:

```
dagster-docs
├── ls              # List packages and symbols
├── check           # Check documentation aspects
└── watch           # Watch files for changes
```

## Commands

### `ls` - List Resources

Lists various documentation-related resources in the codebase.

#### `ls packages`

```bash
dagster-docs ls packages
```

Lists all Dagster public packages that are introspectable by the docs tool.

#### `ls symbols`

```bash
# List symbols in a specific package
dagster-docs ls symbols --package dagster

# List all symbols
dagster-docs ls symbols --all
```

**Options**:

- `--package PKG`: Filter to symbols in a particular package
- `--all`: List all symbols across all packages

### `check` - Validation Commands

Performs various documentation validation checks.

#### `check docstrings`

```bash
# Validate a single symbol
dagster-docs check docstrings --symbol dagster.asset

# Validate all symbols in a package
dagster-docs check docstrings --package dagster

# Validate symbols in changed files. Good for use before commit.
dagster-docs check docstrings --changed

# Validate all docstrings. Good for CI.
dagster-docs check docstrings --all
```

**Options** (exactly one required):

- `--symbol SYMBOL`: Validate a specific symbol
- `--package PKG`: Validate all symbols in a package
- `--changed`: Validate symbols in uncommitted
- `--all`: Validate all docstrings

#### `check rst-symbols`

```bash
dagster-docs check rst-symbols --all
dagster-docs check rst-symbols --package dagster
```

Checks that all symbols in .rst files have corresponding top-level exports marked with `@public`.

#### `check public-symbols`

```bash
dagster-docs check public-symbols --all
dagster-docs check public-symbols --package dagster
```

Checks that all public classes and functions have corresponding entries in .rst files and are exported at the top level.

#### `check exports`

```bash
dagster-docs check exports --all
dagster-docs check exports --package dagster
```

Checks that top-level package exports have public decorators and entries in .rst files.

### `watch` - File Watching

Monitors files for changes and performs real-time validation.

#### `watch docstrings`

```bash
# Watch a specific symbol
dagster-docs watch docstrings --symbol dagster.asset --verbose

# Watch changed files
dagster-docs watch docstrings --changed
```

**Options** (exactly one required):

- `--symbol SYMBOL`: Watch a specific symbol's source file
- `--changed`: Watch all currently changed files

## Usage Examples

```bash
# Basic docstring validation
dagster-docs check docstrings --symbol dagster.asset

# Package-wide validation
dagster-docs check docstrings --package dagster

# Validate only changed files
dagster-docs check docstrings --changed

# List symbols in a package
dagster-docs ls symbols --package dagster._core

# Watch a symbol for changes
dagster-docs watch docstrings --symbol dagster.asset --verbose
```

## Development Notes

- All code changes must pass `make ruff` formatting and linting
- Helper functions are designed to be unit testable
- CLI follows Click framework conventions
- Error messages use `click.echo(err=True)` for stderr output
- Watch mode uses signal handlers for graceful shutdown
