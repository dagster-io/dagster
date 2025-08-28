# API Test Recording Workflow

## Quick Start

### Add a new test case:

1. **Add command to registry**: Edit `{domain}_tests/fixtures/commands.yaml`:

   ```yaml
   your_fixture_name:
     command: "dg plus api your_noun your_verb --your-flag --json"
   ```

2. **Record with new folder structure**: `dagster-dev dg-api-record domain --fixture your_fixture_name --folder-structure`

3. **Record CLI snapshots**: `dagster-dev dg-api-record domain --cli`

### Re-record a single test case:

1. **Re-record with new structure** (if API response changed): `dagster-dev dg-api-record domain --fixture your_fixture_name --folder-structure`

2. **Re-record CLI** (always needed after GraphQL changes): `dagster-dev dg-api-record domain --fixture your_fixture_name --cli`

### Legacy Commands (for backwards compatibility):

- **Record GraphQL (old format)**: `dagster-dev dg-api-record domain --fixture your_fixture_name --graphql`
- **Record CLI**: `dagster-dev dg-api-record domain --fixture your_fixture_name --cli`

---

## Detailed Documentation

This document describes how to add snapshot tests for new Dagster Plus CLI API commands or scenarios using the two-step recording system.

## Overview

The two-step recording system separates GraphQL response capture from CLI output recording:

- **Step 1**: `dagster-dev dg-api-record-graphql` - Captures live GraphQL responses
- **Step 2**: `dagster-dev dg-api-record-cli-output` - Records CLI output using fixtures

## Directory Structure

### New Folder-per-Scenario Structure (Recommended)

```
api_tests/
├── shared/                      # Shared utilities across all domains
│   ├── fixture_config.py        # FixtureCommand dataclass
│   └── yaml_loader.py           # YAML loading utilities
├── deployment_tests/
│   ├── fixtures/
│   │   ├── __init__.py          # Loading utilities (supports both structures)
│   │   ├── success_multiple_deployments/  # Scenario folder
│   │   │   ├── 01_asset_records_query.json    # First GraphQL response
│   │   │   ├── 02_asset_nodes_query.json      # Second GraphQL response
│   │   │   └── cli_output.txt                 # Final CLI output
│   │   ├── error_deployment_not_found/        # Error scenario folder
│   │   │   ├── 01_error_response.json         # GraphQL error response
│   │   │   └── cli_output.txt                 # CLI error output
│   │   └── commands.yaml        # Command registry (YAML format)
│   ├── __snapshots__/           # Auto-generated snapshots
│   ├── test_business_logic.py   # Pure function tests
│   └── test_integration.py      # CLI integration tests
├── run_tests/                   # (similar structure for run commands)
└── asset_tests/                 # (similar structure for asset commands)
```

## Adding a New Test Scenario

### Step 1: Capture GraphQL Responses (New Folder Structure)

Use the `dg-api-record` command with `--folder-structure` to capture live API responses:

```bash
dagster-dev dg-api-record deployment --fixture success_single_deployment --folder-structure
dagster-dev dg-api-record deployment --fixture error_deployment_not_found --folder-structure
dagster-dev dg-api-record deployment --fixture empty_organization_deployments --folder-structure
```

**What this does:**

- Reads the command from `{domain}_tests/fixtures/commands.yaml`
- Executes the live `dg plus api` command
- Creates a scenario folder with the fixture name
- Captures each individual GraphQL call as numbered JSON files (01*\*.json, 02*\*.json, etc.)
- Saves final CLI output as `cli_output.txt`
- Handles both success and error cases automatically

### Step 1 (Legacy): Capture GraphQL Response (Old Format)

For backwards compatibility, you can still use the old single-file format:

```bash
dagster-dev dg-api-record deployment --fixture success_single_deployment --graphql
```

**What this does:**

- Updates `{domain}_tests/fixtures/responses.json` with the new fixture
- Creates individual `*_output.txt` files for CLI output

### Step 2: Record CLI Output Snapshots

Use the `dg-api-record` command with `--cli` to generate CLI output snapshots:

```bash
# Uses the fixture from Step 1 to mock GraphQL, runs CLI command, updates snapshots
dagster-dev dg-api-record deployment --cli
```

**What this does:**

- Uses the fixtures (from either folder structure or responses.json) to mock GraphQL client
- Runs all tests in the domain directory
- Updates snapshot files via `pytest --snapshot-update`
- Captures both JSON and text CLI output formats

## Writing the Actual Tests

After recording, write the test functions that use your new fixtures:

### Business Logic Test

```python
# deployment_tests/test_business_logic.py
from .fixtures import load_deployment_response_fixture

def test_single_deployment_processing(snapshot):
    """Test processing a single deployment response."""
    response = load_deployment_response_fixture("success_single_deployment")
    result = process_deployment_view_response(response)

    # Snapshot validates complete structure and data
    snapshot.assert_match(result)
```

### CLI Integration Test

```python
# deployment_tests/test_integration.py
from unittest.mock import patch
from click.testing import CliRunner
from .fixtures import load_deployment_response_fixture

@patch("dagster_dg_cli.cli.api.deployment._get_config_or_error")
@patch("dagster_dg_cli.dagster_plus_api.graphql_adapter.deployment.DagsterPlusGraphQLClient.from_config")
def test_view_deployment_json_output(mock_client_class, mock_config, snapshot):
    """Test deployment view command with JSON output."""
    mock_config.return_value = "mock-config"
    mock_client = mock_client_class.return_value
    mock_client.execute.return_value = load_deployment_response_fixture("success_single_deployment")

    runner = CliRunner()
    result = runner.invoke(view_deployment_command, ["my-deployment", "--json"])

    assert result.exit_code == 0

    # Snapshot the parsed CLI output
    actual_output = json.loads(result.output)
    snapshot.assert_match(actual_output)
```

## Adding a New API Domain

To add tests for a new API domain (e.g., `asset`):

### 1. Create Directory Structure

```bash
mkdir -p api_tests/asset_tests/fixtures
mkdir -p api_tests/asset_tests/__snapshots__
```

### 2. Create Domain-Specific Files

**`asset_tests/fixtures/commands.yaml`:**

```yaml
success_asset_list:
  command: "dg plus api asset list --json"

success_asset_details:
  command: "dg plus api asset view my-asset-key --json"

error_asset_not_found:
  command: "dg plus api asset view nonexistent-asset --json"
```

**`asset_tests/fixtures/__init__.py`:**

```python
"""Fixture loading utilities for asset API tests."""

import json
from pathlib import Path
from typing import Any

def load_asset_response_fixture(response_name: str) -> dict[str, Any]:
    """Load an asset GraphQL response fixture from JSON."""
    fixtures_file = Path(__file__).parent / "responses.json"

    if not fixtures_file.exists():
        raise ValueError(f"Fixture file not found: {fixtures_file}")

    with open(fixtures_file) as f:
        fixtures = json.load(f)

    if response_name not in fixtures:
        available = list(fixtures.keys())
        raise ValueError(
            f"Response fixture '{response_name}' not found. "
            f"Available fixtures: {available}"
        )

    return fixtures[response_name]
```

### 3. Record Initial Fixtures

```bash
# Step 1: Capture GraphQL responses
dagster-dev dg-api-record-graphql asset success_asset_list

# Step 2: Generate CLI snapshots
dagster-dev dg-api-record-cli-output asset success_asset_list
```

## Fixture Naming Conventions

- `success_{scenario}`: Successful API responses with data
- `empty_{scenario}`: Successful responses with no data
- `error_{error_type}`: Error responses (not_found, unauthorized, timeout, etc.)

Examples:

- `success_multiple_deployments`
- `success_single_deployment`
- `empty_deployment_list`
- `error_deployment_not_found`
- `error_unauthorized_access`

## Common Workflows

### Adding a New Command Scenario

1. **Add command to YAML**: Edit `{domain}_tests/fixtures/commands.yaml`
2. **Record GraphQL response**: `dagster-dev dg-api-record-graphql {domain} {fixture_name}`
3. **Write test functions** using the fixture name
4. **Record CLI snapshots**: `dagster-dev dg-api-record-cli-output {domain} {fixture_name}`
5. **Commit both** fixture and snapshot files

### Updating Existing Fixtures

**For API changes** (GraphQL responses changed):

1. Re-run Step 1: `dagster-dev dg-api-record-graphql {domain} {fixture_name}`
2. Re-run Step 2: `dagster-dev dg-api-record-cli-output {domain} {fixture_name}`
3. Review diffs and commit

**For CLI logic changes only** (same API data, different output):

1. Skip Step 1 (GraphQL data unchanged)
2. Run Step 2 only: `dagster-dev dg-api-record-cli-output {domain} {fixture_name}`
3. Review snapshot diffs and commit

### Testing Your Changes

```bash
# Run tests for specific domain
pytest api_tests/deployment_tests/ -v

# Run specific test
pytest api_tests/deployment_tests/test_integration.py::test_view_deployment_json_output -v

# Update snapshots manually if needed
pytest api_tests/deployment_tests/ --snapshot-update
```

## Benefits of This System

- **Separation of concerns**: GraphQL capture vs CLI recording are independent
- **Domain isolation**: Each API domain has its own fixtures and tests
- **Selective updates**: CLI changes only need Step 2 (no API calls)
- **Real data**: All fixtures come from actual API responses
- **Version control friendly**: Clear diffs for data vs output changes
- **Efficient**: Minimal API calls, fast snapshot updates

## Troubleshooting

### "Command not found" errors

Make sure you're running from the repo root and `dagster-dev` is available.

### "Domain directory not found"

Create the domain test directory structure first (see "Adding a New API Domain").

### "Fixture not found" errors

Run Step 1 first to capture the GraphQL response before trying Step 2.

### Tests failing after recording

Check the test functions are using the correct fixture loading function for the domain (e.g., `load_deployment_response_fixture` vs `load_asset_response_fixture`).
