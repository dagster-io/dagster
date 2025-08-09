# Dagster Documentation Validation System

## Overview

The `dagster_docs` module is a comprehensive documentation validation and linting system for the Dagster codebase. It ensures consistency between Python docstrings, Sphinx RST documentation, `@public` API decorators, and top-level package exports.

## Core Functions

1. **Docstring Validation**: Validates Python docstrings using Google-style format through the Sphinx parsing pipeline
2. **Public API Consistency**: Ensures `@public` decorated symbols are properly documented and exported
3. **RST Documentation Validation**: Checks that RST-documented symbols have corresponding `@public` decorators
4. **Export Validation**: Verifies top-level package exports are properly decorated and documented

## Quick Start

### Installation

The `dagster-docs` CLI is available after installing the automation package:

```bash
# Install from Dagster repository root
cd /path/to/dagster
make dev_install  # This installs the dagster-docs CLI

# Verify installation
dagster-docs --help
```

### Basic Commands

```bash
# Validate a single symbol's docstring
dagster-docs dagster.asset

# Validate all public symbols in a package
dagster-docs dagster --all-public

# Check documentation consistency
dagster-docs check docstrings --symbol dagster.asset
dagster-docs check docstrings --package dagster
dagster-docs check docstrings --changed

# Check @public API consistency
dagster-docs check public-symbols --all
dagster-docs check rst-symbols --all
dagster-docs check exports --all
```

### Watch Mode for Development

```bash
# Watch a file for changes and re-validate automatically
dagster-docs dagster.asset --watch
```

## Key Concepts

### Validation Pipeline

The system uses a functional validation pipeline:

1. **Symbol Import**: Dynamic import and metadata extraction
2. **Napoleon Processing**: Convert Google-style docstrings to RST
3. **Rule Application**: Apply validation rules (RST syntax, section headers, Sphinx filters)
4. **Result Aggregation**: Collect errors and warnings

### Public API System

The system enforces a three-way consistency requirement:

- `@public` decorated symbols MUST be documented in RST files
- `@public` decorated symbols MUST be exported at top-level
- RST documented symbols MUST have `@public` decorators

### Exclude Lists

During incremental migration, exclude lists in `exclude_lists.py` allow temporary exceptions:

- `EXCLUDE_MISSING_RST`: Symbols with `@public` but no RST docs
- `EXCLUDE_MISSING_PUBLIC`: RST symbols without `@public` decorators
- `EXCLUDE_MISSING_EXPORT`: `@public` symbols not exported at top-level

## Common Workflows

### Adding a New Public API

1. Add `@public` decorator to the symbol
2. Export it at the top-level module (`dagster/__init__.py` or library `__init__.py`)
3. Add RST documentation in `docs/sphinx/sections/api/apidocs/`
4. Validate: `dagster-docs check exports --all`

### Validating Documentation Changes

```bash
# Check only changed files in your branch
dagster-docs check docstrings --changed

# Check specific symbol during development
dagster-docs dagster.asset --watch
```

### Managing Exclude Lists

```bash
# Audit exclude lists to find items that can be removed
dagster-docs check exclude-lists --missing-public
dagster-docs check exclude-lists --missing-rst
dagster-docs check exclude-lists --missing-export
```

## Architecture Summary

- **CLI Interface**: `main.py` (simple validation), `cli.py` (complex commands)
- **Core Validation**: `validator.py` (function-based validation logic)
- **Rule System**: `docstring_rules/` (pluggable validation rules)
- **Public API**: `public_api_validator.py` (AST parsing and consistency checks)
- **File Operations**: `file_discovery.py`, `watcher.py`, `path_converters.py`
- **Configuration**: `exclude_lists.py` (temporary exceptions during migration)

## Error Types

- **Parsing Errors**: Napoleon processing failures, import errors
- **RST Syntax Errors**: Invalid reStructuredText in docstrings
- **Section Header Errors**: Malformed Google-style section headers
- **Consistency Errors**: Missing `@public`, missing RST docs, missing exports

## Development

Follow Dagster's standard development practices:

```bash
# Code quality (mandatory after any changes)
make ruff
make quick_pyright

# Test your changes
dagster-docs check docstrings --changed
```

**Extension Points**: See code comments in `docstring_rules/base.py` for custom rule patterns.

## Further Reading

- **[Architecture Overview](docs/architecture.md)** - System design and component relationships
- **[CLI Reference](docs/cli-reference.md)** - Complete command documentation
- **[Troubleshooting](docs/troubleshooting.md)** - Error solutions and debugging
- **[Exclude Lists](docs/exclude-lists.md)** - Managing incremental migration
