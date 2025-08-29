# API Test Infrastructure

## QUICKSTART

1. **Add your command to `scenarios.yaml`:**

   ```yaml
   my_new_test:
     command: "dg api asset list --json"
   ```

2. **Record the GraphQL response:**

   ```bash
   dagster-dev dg-api-record asset --recording my_new_test
   ```

3. **Generate snapshots:**
   ```bash
   pytest api_tests/asset_tests/ --snapshot-update
   ```

That's it! Your test is now ready. 🎉

### Running tests:

```bash
# Run all tests for a domain
pytest api_tests/asset_tests/

# Update snapshots when output changes
pytest api_tests/asset_tests/ --snapshot-update
```

## Overview

This directory contains the test infrastructure for Dagster Plus CLI API commands. The system uses:

- **GraphQL response recording** from real APIs
- **Syrupy snapshot testing** for output validation
- **Dynamic test discovery** from YAML configuration files

## Directory Structure

```
api_tests/
├── asset_tests/              # Asset API domain tests
│   ├── scenarios.yaml        # Test scenario definitions
│   ├── recordings/             # Recorded GraphQL responses
│   │   ├── success_single_asset/
│   │   │   └── 01_response.json
│   │   └── error_asset_not_found/
│   │       └── 01_response.json
│   ├── __snapshots__/        # Syrupy test snapshots
│   └── test_business_logic.py
├── deployment_tests/         # Deployment API domain tests
│   └── ...                   # Same structure as asset_tests
└── test_dynamic_command_execution.py  # Shared test runner
```

## Key Concepts

### Scenarios

Each test scenario is defined in `scenarios.yaml` with:

- **Scenario name**: Descriptive identifier (e.g., `success_single_asset`)
- **Command**: The CLI command to test (e.g., `dg api asset list --json`)

### Recordings

GraphQL responses are recorded from live APIs and stored as JSON files:

- Located in `recordings/{scenario_name}/01_response.json`
- Multiple responses supported with numbered files (01, 02, etc.)
- Automatically created by `dg-api-record` command

### Snapshots

Output validation uses syrupy snapshots:

- Automatically generated on first test run
- Stored in `__snapshots__/` directories
- Both JSON and text output formats supported

## Common Tasks

### Add a new API domain

1. **Create domain directory:**

   ```bash
   mkdir api_tests/my_domain_tests
   mkdir api_tests/my_domain_tests/recordings
   ```

2. **Create scenarios.yaml:**

   ```yaml
   # api_tests/my_domain_tests/scenarios.yaml
   success_list:
     command: "dg api my_domain list --json"
   ```

3. **Record responses:**

   ```bash
   dagster-dev dg-api-record my_domain
   ```

4. **Run tests to generate snapshots:**
   ```bash
   pytest api_tests/my_domain_tests/ --snapshot-update
   ```

### Update existing tests

When CLI output changes:

```bash
# Re-run tests and update snapshots
pytest api_tests/asset_tests/ --snapshot-update

# Review changes
git diff api_tests/asset_tests/__snapshots__/
```

When API responses change:

```bash
# Re-record responses
dagster-dev dg-api-record asset --recording success_single_asset

# Update snapshots
pytest api_tests/asset_tests/ --snapshot-update
```

### Debug test failures

```bash
# Run tests with verbose output
pytest api_tests/asset_tests/ -v

# Run specific test scenario
pytest api_tests/asset_tests/ -k "success_single_asset"

# Show detailed diff on snapshot mismatch
pytest api_tests/asset_tests/ --snapshot-diff
```

## Command Reference

### dg-api-record

Record GraphQL responses for test scenarios:

```bash
# Record all scenarios in a domain
dagster-dev dg-api-record asset

# Record specific scenario
dagster-dev dg-api-record asset --recording success_single_asset

# Available domains
dagster-dev dg-api-record [asset|deployment|run|...]
```

### pytest options

```bash
--snapshot-update    # Accept current output as new baseline
--snapshot-diff      # Show detailed diff on mismatch
-k PATTERN          # Run only tests matching pattern
-v                  # Verbose output
```

## Test Types

### Business Logic Tests (`test_business_logic.py`)

- Test data processing functions in isolation
- Use recorded responses as input
- Validate transformed output with snapshots

### Dynamic Command Execution Tests (`test_dynamic_command_execution.py`)

- Automatically discover and run all scenarios
- Mock GraphQL client with recorded responses
- Validate CLI output against snapshots

### REST Compliance Tests (`test_rest_compliance.py`)

- Validate API method naming conventions
- Check type signatures and response patterns
- Ensure consistency across API domains

## Best Practices

1. **Descriptive scenario names**: Use clear names like `success_multiple_assets` or `error_not_found`
2. **Test both success and error cases**: Include `error_*` scenarios for failure paths
3. **Keep recordings minimal**: Record only the data needed for tests
4. **Review snapshot changes**: Always inspect diffs before committing
5. **Update recordings when APIs change**: Re-record to match current behavior

## Troubleshooting

### "Exhausted responses" error

The test tried to make more GraphQL calls than recorded. Re-record the scenario.

### Snapshot mismatches

Either the output changed (update snapshots) or there's a regression (fix the code).

### Missing recordings

Run `dg-api-record` to create the recording directory and record responses.

### Tests not discovering scenarios

Ensure `scenarios.yaml` exists and has valid YAML syntax.

## Architecture Notes

The test infrastructure separates concerns:

- **Recording**: Captures real API responses once
- **Mocking**: Replays recorded responses during tests
- **Validation**: Snapshots verify output consistency
- **Discovery**: Dynamic test generation from YAML

This design enables:

- Fast test execution (no network calls)
- Reliable tests (deterministic responses)
- Easy updates (re-record or update snapshots)
- Broad coverage (all scenarios tested automatically)
