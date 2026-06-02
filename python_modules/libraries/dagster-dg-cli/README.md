# dagster-dg-cli

The `dg` CLI tool.

Includes commands for:

- Scaffolding, checking, and listing Dagster entities
- Running pipelines in a local Dagster instance
- Interacting with Dagster Plus (REST-style API commands)

## REST API Commands

`dg` depends on [`dagster-rest-resources`](../dagster-rest-resources/README.md) for REST-style API interactions with Dagster Plus.
To add a new CLI command that requires new API calls, add them to `dagster-rest-resources` first, then call through to that library from `dg`.

## Testing

API command tests live in `dagster_dg_cli_tests/cli_tests/api_tests/`. Each domain (e.g. `asset_check_tests`, `deployment_tests`) follows the same structure:

```
<domain>_tests/
├── scenarios.yaml        # Test scenario definitions (command to run)
├── recordings/           # Recorded GraphQL responses (JSON)
├── __snapshots__/        # Syrupy output snapshots
└── test_business_logic.py
```

### Adding a test for a new command

1. Add your scenario to `scenarios.yaml`:

   ```yaml
   my_new_test:
     command: "dg api asset list --json"
   ```

2. Record the GraphQL response:

   ```bash
   dagster-dev dg-api-record asset --recording my_new_test
   ```

3. Generate snapshots:

   ```bash
   pytest dagster_dg_cli_tests/cli_tests/api_tests/asset_tests/ --snapshot-update
   ```

### Common commands

```bash
# Run tests for a domain
pytest dagster_dg_cli_tests/cli_tests/api_tests/asset_check_tests/

# Update snapshots after output changes
pytest dagster_dg_cli_tests/cli_tests/api_tests/asset_check_tests/ --snapshot-update

# Re-record API responses after API changes
dagster-dev dg-api-record asset --recording success_single_asset

# Run a specific scenario
pytest dagster_dg_cli_tests/cli_tests/api_tests/asset_check_tests/ -k "my_new_test"
```
