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

## Core Concepts

### Test Infrastructure

The API test infrastructure provides a comprehensive framework for testing CLI commands that interact with GraphQL APIs. It separates concerns between:

- **GraphQL response recording**: Capturing real API responses for test scenarios
- **Business logic testing**: Validating data processing functions
- **CLI integration testing**: Ensuring commands produce correct output
- **REST compliance**: Enforcing API design conventions

### Domain Organization

Each API domain (deployments, assets, etc.) maintains its own test directory with:

- **Scenario registry** (`scenarios.yaml`): Defines test commands and their context
- **Recorded fixtures**: GraphQL responses as JSON files (e.g., `01_placeholder_query.json`)
- **Test modules**: Business logic and CLI integration tests
- **Snapshots**: Syrupy-managed expected outputs for validation

## Test Types

### Business Logic Tests

Pure function tests that validate data processing logic without external dependencies. These tests use recorded GraphQL responses as input and snapshot the transformed output.

### Dynamic CLI Integration Tests

Automated tests that execute CLI commands with mocked GraphQL responses. The test framework discovers scenarios from YAML registries and validates outputs using syrupy snapshots.

The `test_dynamic_command_execution.py` file:

- Discovers all scenarios from `scenarios.yaml` files across domains
- Loads corresponding GraphQL response fixtures (JSON files)
- Executes commands with mocked GraphQL clients
- Validates output using syrupy snapshots (both JSON and text formats)

### REST Compliance Tests

Automated validation ensuring API classes follow REST conventions:

- Method naming patterns (get*, list*, create*, update*, delete\_)
- Type signatures (primitives + Pydantic models only)
- Response consistency (list methods return standardized structures)
- Parameter patterns (consistent naming and typing conventions)

## Fixture Structure

Each test scenario has a corresponding directory under `{domain}_tests/fixtures/{scenario_name}/` containing:

- `01_placeholder_query.json`: The GraphQL response data used by tests
- Additional numbered JSON files if multiple GraphQL calls are needed

The JSON files are loaded by `load_deployment_response_fixture()` (or equivalent for other domains) and used to mock GraphQL responses during testing.

## Working with Test Scenarios

### Creating New Scenarios

1. **Define the scenario** in the domain's `scenarios.yaml` file with a descriptive name and command
2. **Record live responses** using `dagster-dev dg-api-record` to capture real API interactions
3. **Generate snapshots** by running tests with `--snapshot-update` to establish baselines

### Updating Existing Scenarios

When CLI output changes (e.g., formatting updates, new fields):

- Run tests with `--snapshot-update` to accept new outputs
- Review snapshot diffs to ensure changes are intentional
- Commit both code and snapshot changes together

When API responses change:

- Re-record fixtures using `dagster-dev dg-api-record`
- Update snapshots to match new responses
- Validate that business logic handles the changes correctly

## Key Commands

- `dagster-dev dg-api-record {domain}` - Record all scenarios for a domain
- `dagster-dev dg-api-record {domain} --fixture {name}` - Record specific scenario
- `pytest api_tests/{domain}_tests/ --snapshot-update` - Update snapshots when outputs change

## Extending the Test Suite

### Adding New API Domains

When introducing a new API domain:

1. Create the domain test directory structure
2. Define test scenarios in `scenarios.yaml`
3. Implement fixture loading functions
4. Record initial fixtures from the live API
5. Write domain-specific tests as needed
6. Ensure REST compliance tests cover new API classes

### Adding Test Categories

The infrastructure supports various test categories beyond the core types:

- **Error handling tests**: Validate graceful failures and error messages
- **Performance tests**: Monitor response times and data processing efficiency
- **Integration tests**: Verify interactions between multiple API domains
- **Migration tests**: Ensure backward compatibility during API evolution

## Architecture Benefits

### Development Velocity

- **Rapid iteration**: Update snapshots instantly when outputs change intentionally
- **Real data testing**: Work with actual API responses, not mocked data
- **Parallel development**: Multiple domains can evolve independently

### Maintainability

- **Clear separation**: GraphQL fixtures, business logic, and CLI output are distinct
- **Version control friendly**: Human-readable diffs for all test artifacts
- **Automated compliance**: REST conventions enforced programmatically

### Test Quality

- **Comprehensive coverage**: Every command path tested with real scenarios
- **Regression detection**: Snapshots catch unintended output changes
- **Consistency validation**: Ensures uniform behavior across API domains
