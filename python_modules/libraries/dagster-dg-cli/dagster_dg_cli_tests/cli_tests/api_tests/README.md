# API Test Infrastructure

This directory contains infrastructure for testing Dagster Plus CLI API commands with syrupy snapshot testing and GraphQL response mocking.

## Quick Start

### Record fixtures for a new test scenario:

1. **Add scenario to registry**: Edit `{domain}_tests/fixtures/scenarios.yaml`:

   ```yaml
   success_list_assets:
     command: "dg api asset list --json"
   ```

2. **Record GraphQL responses**: `dagster-dev dg-api-record asset --fixture success_list_assets`

3. **Run tests to generate syrupy snapshots**: `pytest api_tests/{domain}_tests/ --snapshot-update`

## Directory Structure

```
api_tests/
├── shared/                           # Shared utilities
│   ├── fixture_config.py             # FixtureScenario dataclass
│   └── yaml_loader.py                # YAML loading utilities
├── deployment_tests/                 # Deployment API tests
│   ├── fixtures/
│   │   ├── __init__.py               # Fixture loading functions
│   │   ├── scenarios.yaml            # Test scenarios registry
│   │   ├── success_multiple_deployments/  # Individual scenario directories
│   │   │   ├── 01_response.json      # GraphQL response from recording
│   │   │   └── cli_output.txt        # Raw CLI output
│   │   └── empty_deployments/
│   │       ├── 01_response.json
│   │       └── cli_output.txt
│   ├── __snapshots__/                # Syrupy-generated snapshot files
│   │   ├── test_business_logic.ambr  # Business logic snapshots
│   │   └── test_dynamic_command_execution.ambr  # CLI output snapshots
│   ├── test_business_logic.py        # Pure function tests with syrupy
│   └── test_dynamic_command_execution.py  # CLI integration tests with syrupy
├── asset_tests/                      # Asset API tests (similar structure)
├── rest_compliance_infrastructure.py # REST API compliance utilities
├── test_rest_compliance.py          # REST compliance test suite
└── conftest.py                       # Shared test configuration with syrupy
```

## Test Types

### 1. Business Logic Tests (`test_business_logic.py`)

Tests pure functions that process GraphQL responses without external dependencies.

```python
def test_process_deployments_response(snapshot):
    """Test the deployment response processing function."""
    response = load_deployment_response_fixture("success_multiple_deployments")[0]
    result = process_deployments_response(response)
    snapshot.assert_match(result)
```

### 2. Dynamic CLI Integration Tests (`test_dynamic_command_execution.py`)

Automatically tests all scenarios from `scenarios.yaml` by mocking GraphQL responses and using syrupy for output validation.

```python
@pytest.mark.parametrize("domain,fixture_name,command", list(discover_scenario_fixtures()))
def test_command_execution(self, domain: str, fixture_name: str, command: str, snapshot):
    """Test executing a command against its recorded GraphQL responses."""
    # Load fixtures, mock GraphQL, run command
    result = self._test_deployment_command(click_command, args, graphql_responses, fixture_name)

    # Syrupy snapshot validation
    if "--json" in args:
        parsed_output = json.loads(result.output)
        snapshot.assert_match(parsed_output, name=f"{fixture_name}_json_output")
    else:
        snapshot.assert_match(result.output, name=f"{fixture_name}_text_output")
```

### 3. REST Compliance Tests (`test_rest_compliance.py`)

Automated tests ensuring API classes follow REST conventions:

- Method naming (get*, list*, create*, update*, delete\_)
- Type signatures (primitives + Pydantic models only)
- Response consistency (list methods return objects with `items` field)
- Parameter patterns (consistent ID naming, Optional typing)

## Recording New Test Scenarios

### Step 1: Define Scenario

Add to `{domain}_tests/fixtures/scenarios.yaml`:

```yaml
success_asset_details:
  command: "dg api asset view my-asset-key --json"
```

### Step 2: Record Live Responses

```bash
# Records GraphQL responses and CLI output to fixture folders
dagster-dev dg-api-record asset --fixture success_asset_details
```

This creates:

- `success_asset_details/01_response.json` - GraphQL response
- `success_asset_details/cli_output.txt` - Raw CLI output

### Step 3: Run Tests to Generate Snapshots

```bash
# Generate syrupy snapshots from recorded fixtures
pytest api_tests/asset_tests/ --snapshot-update
```

Tests automatically use the recorded fixtures and validate CLI outputs with syrupy snapshots.

## Commands Available

- `dagster-dev dg-api-record {domain}` - Record all scenarios for a domain
- `dagster-dev dg-api-record {domain} --fixture {name}` - Record specific scenario
- `pytest api_tests/{domain}_tests/ --snapshot-update` - Update syrupy snapshots when outputs change

## Fixture Loading

Each domain provides a fixture loader in `{domain}_tests/fixtures/__init__.py`:

```python
def load_deployment_response_fixture(fixture_name: str) -> list[dict[str, Any]]:
    """Load GraphQL responses for a deployment test scenario."""
    # Returns list of GraphQL responses (one per API call made)
```

## Adding New API Domains

1. **Create directory structure**:

   ```bash
   mkdir -p api_tests/new_domain_tests/{fixtures,__snapshots__}
   ```

2. **Create `fixtures/scenarios.yaml`**:

   ```yaml
   success_basic_operation:
     command: "dg api new-domain operation --json"
   ```

3. **Create `fixtures/__init__.py`** with domain-specific loader:

   ```python
   def load_new_domain_response_fixture(fixture_name: str) -> list[dict[str, Any]]:
       # Implementation following pattern from deployment_tests
   ```

4. **Record fixtures**: `dagster-dev dg-api-record new-domain`

5. **Write tests** following the established patterns

## Benefits

- **Syrupy snapshot testing**: Superior diff experience with colored output and atomic updates
- **Simplified recording**: No complex JSON fixture management - just capture and snapshot
- **Separation of concerns**: GraphQL recording vs CLI testing
- **Real data**: All fixtures from actual API responses
- **Fast updates**: CLI changes only need `pytest --snapshot-update`, no API calls
- **Domain isolation**: Each API area has independent fixtures
- **REST compliance**: Automated enforcement of API conventions
- **Version control friendly**: Clear diffs for API vs CLI changes
- **Batch updates**: `pytest --snapshot-update` updates all snapshots atomically
