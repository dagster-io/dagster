# Dagster Development Guide

## Quick References

- **Package Locations**: [.claude/python_packages.md](./.claude/python_packages.md) - Comprehensive list of all Python packages and their filesystem paths. Use this to quickly find packages when the users requests it.
- **Development Workflow**: [.claude/dev_workflow.md](./.claude/dev_workflow.md) - Documentation of developer workflows in the Dagster OSS repo. 
- **Coding Conventions**: [.claude/coding_conventions.md](./.claude/coding_conventions.md) - Type annotations and code style conventions

## Environment Setup

See [docs/docs/about/contributing.md](docs/docs/about/contributing.md) for full setup instructions.

```bash
make dev_install  # Full development environment setup
```

## Essential Commands

```bash
# Code quality
make ruff                    # Format, lint, and autofix code
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

- Follow Google-style docstrings
