# Dagster Development Guide

## Quick References

- **Package Locations**: [.claude/python_packages.md](./.claude/python_packages.md) - Comprehensive list of all Python packages and their filesystem paths. **ALWAYS check this file first when looking for package locations.**
- **Development Workflow**: [.claude/dev_workflow.md](./.claude/dev_workflow.md) - Documentation of developer workflows in the Dagster OSS repo.
- **Coding Conventions**: [.claude/coding_conventions.md](./.claude/coding_conventions.md) - Type annotations and code style conventions. **ALWAYS check this before writing data structures - use @record instead of @dataclass.**
- **CRITICAL**: After ANY Python code changes, ALWAYS run `make ruff` - this is mandatory and must never be skipped.

## Environment Setup

See [docs/docs/about/contributing.md](docs/docs/about/contributing.md) for full setup instructions.

```bash
make dev_install  # Full development environment setup
```

## Essential Commands

```bash
# Code quality - RUN AFTER EVERY PYTHON EDIT
make ruff                    # Format, lint, and autofix code - MANDATORY AFTER ANY CODE CHANGES
make pyright                # Type checking (slow first run)
make quick_pyright          # Type check only changed files

# Testing
pytest path/to/tests/       # Run specific tests
pytest python_modules/dagster/dagster_tests/  # Run core tests
tox -e py39-pytest          # Test in isolated environment

# Development
make rebuild_ui             # Rebuild React UI after changes
make graphql               # Regenerate GraphQL schema
make sanity_check          # Check for non-editable installs
```

## Development Workflow

- **Python**: Core framework in `python_modules/dagster/`, libraries in `python_modules/libraries/`
- **UI**: React/TypeScript in `js_modules/dagster-ui/`
- **Docs**: Docusaurus in `docs/`
- **Testing**: pytest preferred, use tox for environment isolation

## UI Development

```bash
# Terminal 1: Start GraphQL server
cd examples/docs_snippets/docs_snippets/intro_tutorial/basics/connecting_ops/
dagster-webserver -p 3333 -f complex_job.py

# Terminal 2: Start UI development server
cd js_modules/dagster-ui
make dev_webapp
```

## Documentation

```bash
cd docs
yarn install && yarn start     # Start docs server
yarn build-api-docs          # Build API docs after .rst changes
```

## Code Style

- **See [.claude/coding_conventions.md](./.claude/coding_conventions.md) for all code style and convention guidelines**

## Code Quality Requirements

- **MANDATORY**: After any code changes, ALWAYS run `make ruff` to format, lint, and autofix code
- **MANDATORY**: If `make ruff` makes any changes, re-run tests to ensure everything still works
- **MANDATORY**: Address any linting issues before considering a task complete
- Never skip this step - code quality checks are essential for all contributions

## Package Management

- Always use uv instead of pip
- **IMPORTANT**: When command line entry_points change in setup.py, you must reinstall the package using `uv pip install -e .` for the changes to take effect

## Code searching

- DO NOT search for Python code (.py files) inside of .tox folders. These are temporary environments and this will only cause confusion.
- Always search for package dependencies in setup.py files only. This is the current source of truth for dependencies in this repository.

## Make Command Guidelines

- Whenever there is an instruction to run a make command, ALWAYS cd to $DAGSTER_GIT_REPO_DIR, as the Makefile is at the root of the repository

## Environment Variables

- **DAGSTER_GIT_REPO_DIR**: Always defined and points to the repository root directory. Use this for any absolute path references in agent configurations or file operations instead of hardcoding user-specific paths.

## PR Stack Operations

### Finding GitHub Usernames Efficiently

- **Best method**: `gh search commits "FirstName" --author="Full Name" --repo=dagster-io/dagster`
- **Why effective**: Co-authored commits reveal exact GitHub username format
- **Alternative**: Check recent PRs or issues for the person's contributions

### Stack Operations Always Use GT

- **Key rule**: When someone mentions "stacking" or "stack", always use `gt` commands first
- **Reason**: GT is the source of truth for stack metadata and relationships
- **Primary command**: `gt log` provides comprehensive PR numbers, statuses, and branch relationships
- **Impact**: Single command reveals entire stack structure vs. manual discovery

- Do not automatically do git commit --amend on user's behalf since you lose track of what the agent has done
