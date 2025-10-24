# Error Code Testing Infrastructure

This directory contains comprehensive tests for structured error handling across all Dagster API CLI domains. It provides a single source of truth for testing error mapping from GraphQL to REST conventions.

## Directory Structure

```
error_code_tests/
├── scenarios.yaml              # All error scenarios across domains
├── recordings/                 # Recorded GraphQL error responses
│   ├── error_asset_not_found/
│   │   └── 01_response.json
│   └── error_unauthorized/
│       └── 01_response.json
├── __snapshots__/             # Error output snapshots
├── test_error_structure.py    # Error format validation tests
├── test_error_mapping.py      # GraphQL->REST mapping tests
├── test_error_integration.py  # End-to-end error testing
├── Makefile                   # Common tasks shortcuts
└── README.md                  # This file
```

## Quick Start

### 1. Record Error Scenarios

Record all error scenarios:

```bash
cd error_code_tests
make record-all
# or: dagster-dev dg-api-record error_code
```

Record a specific scenario:

```bash
make record SCENARIO=error_asset_not_found
# or: dagster-dev dg-api-record error_code --recording error_asset_not_found
```

### 2. Run Tests

Run all error code tests:

```bash
make test
# or: pytest . -v
```

Update snapshots after changes:

```bash
make update-snapshots
# or: pytest . --snapshot-update
```

## Test Categories

### Error Structure Tests (`test_error_structure.py`)

Tests that validate error response format and structure:

- **JSON Response Structure**: Validates presence of `error`, `code`, `statusCode`, `type` fields
- **Text Response Format**: Validates consistent "Error querying Dagster Plus API: " prefix
- **Exit Code Mapping**: Tests that 4xx errors → exit code 1, 5xx errors → exit code 5
- **Error Type Categorization**: Validates error type field matches status code
- **Error Message Quality**: Ensures error messages are non-empty and descriptive

### Error Mapping Tests (`test_error_mapping.py`)

Tests that validate GraphQL to REST error mapping:

- **Mapping Completeness**: Verifies all expected GraphQL error types have mappings
- **Mapping Structure**: Validates all mappings have proper code and status_code
- **Status Code Consistency**: Tests similar error types have consistent status codes
- **Error Code Conventions**: Validates naming conventions (uppercase, underscores, etc.)
- **Categorization Logic**: Tests status code to error type mapping
- **Unknown Error Fallback**: Tests fallback to INTERNAL_ERROR for unknown types

### Integration Tests (`test_error_integration.py`)

Tests that validate end-to-end error handling:

- **Complete Error Flow**: Tests full pipeline from GraphQL response to CLI output
- **Cross-Domain Consistency**: Ensures similar errors handled consistently across domains
- **Error Propagation**: Tests errors bubble up correctly through API layers
- **Fallback Handling**: Tests graceful handling of malformed responses
- **Output Format Testing**: Validates both JSON and text output with snapshots

## Scenario Configuration

Error scenarios are defined in `scenarios.yaml` with the following structure:

```yaml
error_asset_not_found:
  command: "dg api asset get nonexistent-asset --json"
  expected_code: "ASSET_NOT_FOUND"
  expected_status: 404
  description: "Asset does not exist in the deployment"
```

### Fields:

- **command**: CLI command to execute (should trigger the error)
- **expected_code**: Expected error code from the mapping system
- **expected_status**: Expected HTTP status code
- **description**: Human-readable description of the error scenario

### Scenario Naming Convention:

- Start with `error_` prefix
- Use descriptive names: `error_asset_not_found`, `error_unauthorized_access`
- Include format suffix for text variants: `error_asset_not_found_text`

## Error Categories Covered

### 400 Client Errors

- Invalid asset keys, limits, cursors
- Malformed partition subsets
- Validation failures

### 401 Authentication Errors

- Unauthorized access to assets, deployments
- Missing or invalid authentication

### 403 Authorization Errors (future)

- Access to restricted resources
- Insufficient permissions

### 404 Not Found Errors

- Nonexistent assets, pipelines, runs, schedules
- Missing repositories, config types

### 422 Migration Errors

- Assets requiring data migration
- User code upgrade requirements
- Agent upgrade requirements

### 500 Server Errors

- Python exceptions during processing
- Missing scheduler configuration
- Generic internal errors

## Recording Infrastructure

The recording system captures GraphQL error responses for later replay in tests:

1. **Real API Calls**: Records actual GraphQL error responses from live APIs
2. **Error Response Capture**: Saves both successful and error GraphQL responses
3. **Deterministic Testing**: Tests replay recorded responses without network calls
4. **Snapshot Testing**: Output is validated against saved snapshots

### Recording Process:

1. Execute command against real API
2. Capture GraphQL error response(s)
3. Save to `recordings/{scenario_name}/01_response.json`
4. Tests replay recorded responses during execution

## Common Workflows

### Adding New Error Scenario

1. Add scenario to `scenarios.yaml`:

   ```yaml
   error_new_scenario:
     command: "dg api resource action --json"
     expected_code: "EXPECTED_ERROR_CODE"
     expected_status: 400
     description: "Description of error condition"
   ```

2. Record the scenario:

   ```bash
   make record SCENARIO=error_new_scenario
   ```

3. Run tests and update snapshots:
   ```bash
   make test
   make update-snapshots  # if output changed
   ```

### Updating Error Mappings

When GraphQL error mappings change:

1. Update mappings in `dagster_dg_cli/cli/api/shared.py`
2. Update expected codes in `scenarios.yaml`
3. Re-record affected scenarios
4. Update snapshots

### Debugging Test Failures

#### Missing Recordings

```
Recording not found for error_asset_not_found. Run: make record SCENARIO=error_asset_not_found
```

**Solution**: Record the missing scenario

#### Snapshot Mismatches

```
AssertionError: snapshot != expected_output
```

**Solution**: Review changes, then update snapshots if correct

#### Import/Circular Import Issues

```
ImportError: cannot import name 'IGraphQLClient' from partially initialized module
```

**Solution**: Check for circular imports in the API layer imports

## Integration with Existing Infrastructure

This error testing infrastructure integrates with the existing API test framework:

- **Shared YAML Loader**: Uses `shared/yaml_loader.py` for scenario loading
- **Test Context**: Uses `DgApiTestContext` for response mocking
- **Snapshot Testing**: Uses syrupy for output validation
- **Recording System**: Extends `dg_api_record.py` for error response capture

## Benefits

- **Comprehensive Coverage**: Tests all error types across all domains
- **Single Source of Truth**: All error scenarios in one place
- **Domain Agnostic**: No duplication across asset/deployment/etc tests
- **Maintainable**: Easy to add new error scenarios
- **Consistent**: Uniform error testing approach
- **Future-Proof**: Extensible for new API domains
