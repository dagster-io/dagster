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

## Dagster Plus CLI API Testing Strategy

### Overview

The Dagster Plus CLI API commands follow a structured testing approach that separates business logic from CLI concerns and uses real GraphQL responses as test fixtures. This strategy avoids mocks for business logic while maintaining fast, reliable tests.

### Directory Structure for API Noun Groups

API command groups should follow this standard structure (using `run` as example):

```
cli/plus/api/run/
├── __init__.py                 # Empty - no meaningful code
├── cli_group.py               # Main CLI group definition
├── view.py                    # Individual command implementations
├── queries.py                 # GraphQL query strings
├── shared.py                  # Common utilities and recording support
├── business_logic.py          # Pure functions for testability
└── recording.py               # Recording functionality

# Corresponding test structure:
cli_tests/plus_tests/api_tests/run_tests/
├── __init__.py
├── conftest.py                # Test configuration
├── test_business_logic.py     # Direct business logic tests
├── test_view_integration.py   # CLI integration tests
└── fixtures/
    ├── __init__.py
    └── run_responses.py       # GraphQL response fixtures
```

### Recording Test Fixtures

#### Using the --record Flag

All API commands support a `--record` flag for capturing real GraphQL traffic:

```bash
# Record successful responses
dg plus api run view 9d38c7ea --record

# Record error responses  
dg plus api run view nonexistent --record
```

Recordings are saved to `recordings/` directory with timestamped filenames:
- `recordings/run_view_20240813_143022.json`

#### Processing Recordings into Test Fixtures

Use the processing script to convert raw recordings into test-friendly Python fixtures:

```bash
# Process single file
python scripts/process_recordings.py recordings/run_view_20240813_143022.json

# Process all recordings in directory to specific output file
python scripts/process_recordings.py recordings/ path/to/fixtures/run_responses.py run_
```

The script automatically:
- Generates appropriate fixture names based on response patterns
- Formats as Python dictionaries
- Handles both success and error responses
- Preserves GraphQL response structure

### Testing Architecture

#### Business Logic Testing (Primary Layer)

Test pure functions directly with recorded GraphQL responses:

```python
# test_business_logic.py
from dagster_dg_cli.cli.plus.api.run.business_logic import process_run_view_response
from .fixtures.run_responses import RUN_VIEW_SUCCESS_RESPONSE

def test_successful_response_processing():
    api_response = process_run_view_response(RUN_VIEW_SUCCESS_RESPONSE)
    assert api_response["run_id"] == "9d38c7ea"
    assert api_response["status"] == "SUCCESS"
```

**Benefits:**
- No mocks required for business logic
- Tests actual data transformation logic
- Fast execution
- Easy to debug

#### Integration Testing (Minimal Layer)  

Test CLI interface with minimal mocking:

```python
# test_view_integration.py
def test_successful_command_execution_json():
    with patch("...DagsterPlusGraphQLClient.from_config") as mock_client:
        mock_client.return_value.execute.return_value = RUN_VIEW_SUCCESS_RESPONSE
        
        runner = CliRunner()
        result = runner.invoke(view_run_command, ["9d38c7ea", "--json"])
        
        assert result.exit_code == 0
        # Verify CLI-specific concerns only
```

**Focus areas:**
- CLI argument parsing
- Exit codes
- Output formatting
- Recording flag functionality

#### Business Logic Extraction Pattern

Extract processing logic into pure functions in `business_logic.py`:

```python
def process_run_view_response(graphql_response: Dict[str, Any]) -> Dict[str, Any]:
    """Process GraphQL response for run view command."""
    # Pure function - no side effects, easy to test
    
def format_run_view_output(api_response: Dict[str, Any], as_json: bool) -> str:
    """Format API response for output."""
    # Another pure function
```

CLI commands become thin wrappers:

```python
def view_run_command(run_id: str, output_json: bool, record: bool):
    graphql_response = execute_with_optional_recording(...)
    api_response = process_run_view_response(graphql_response)
    formatted_output = format_run_view_output(api_response, output_json)
    click.echo(formatted_output)
```

### Test Fixtures Best Practices

#### Fixture Generation Workflow

1. **Manual Developer Process**: Recording and processing require intentional developer steps
2. **Real Response Capture**: Always use `--record` flag with actual API calls
3. **Review Before Processing**: Examine raw recordings for sensitive data
4. **Structured Processing**: Use script to ensure consistent fixture format

#### Fixture Organization

```python
# fixtures/run_responses.py
"""Test fixtures for run API commands.

Generated from recordings using --record flag and process_recordings.py script.
"""

RUN_VIEW_SUCCESS_RESPONSE = {
    "runOrError": {
        "__typename": "Run",
        "id": "abc123def456",
        "runId": "9d38c7ea",
        # ... rest of response
    }
}

RUN_VIEW_NOT_FOUND_RESPONSE = {
    "runOrError": {
        "__typename": "RunNotFoundError", 
        "message": "Run with id 'nonexistent' was not found"
    }
}
```

### Implementation Standards

#### Shared Utilities

Each API noun group should include common utilities in `shared.py`:

```python
# Common Click option for all commands
recording_option = click.option(
    "--record", is_flag=True, help="Record GraphQL request/response for testing"
)

def execute_with_optional_recording(
    client, query: str, variables: Dict[str, Any], 
    command_name: str, record: bool = False
) -> Dict[str, Any]:
    """Execute GraphQL query with optional recording."""
```

#### Recording Implementation

Recording should be non-intrusive and optional:

```python
def record_graphql_interaction(
    query: str, variables: Dict[str, Any], response: Dict[str, Any],
    command_name: str, record_dir: Optional[str] = None
) -> None:
    """Record GraphQL interaction to timestamped JSON file."""
```

### Testing Command Examples

```bash
# Run business logic tests (fast)
pytest dagster_dg_cli_tests/cli_tests/plus_tests/api_tests/run_tests/test_business_logic.py

# Run integration tests  
pytest dagster_dg_cli_tests/cli_tests/plus_tests/api_tests/run_tests/test_view_integration.py

# Run all run API tests
pytest dagster_dg_cli_tests/cli_tests/plus_tests/api_tests/run_tests/

# Generate new fixtures
dg plus api run view real-run-id --record
python scripts/process_recordings.py recordings/ -o fixtures/run_responses.py
```

This testing strategy ensures maintainable, fast tests while working with real API responses and avoiding the complexity of mocking GraphQL interactions.

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
