# Plan: Hard Cutover to Folder-per-Scenario Structure

## New Structure
```
fixtures/
├── success_multiple_assets/           # Scenario folder
│   ├── 01_asset_records_query.json    # First GraphQL response
│   ├── 02_asset_nodes_query.json      # Second GraphQL response
│   └── cli_output.txt                 # Final CLI output (JSON or text)
├── error_asset_not_found/
│   ├── 01_error_response.json          # GraphQL error response  
│   └── cli_output.txt                 # CLI error output
├── commands.yaml                      # Unchanged
```

## Implementation Steps

1. **Update fixture loading functions** 
   - Change from loading single `responses.json[name]` to loading scenario folders
   - Return list of GraphQL responses from numbered JSON files
   - Support loading `cli_output.txt` for reference

2. **Update recording script** (`dg_api_record.py`)
   - Create scenario folder per fixture name
   - Intercept and save each GraphQL `client.execute()` call as numbered JSON files
   - Save final CLI output as `cli_output.txt`

3. **Update documentation** in README.md to reflect new folder structure

4. **Hard cutover**: Delete old `responses.json` files and `*_output.txt` files

5. **Re-record everything** using new system for all existing scenarios in asset_tests and deployment_tests

6. **Test changes** by running existing test suites

## Benefits
- **No migration complexity** - Clean slate approach
- **Proper GraphQL granularity** - Individual queries captured
- **Better version control** - Changes isolated to specific scenarios  
- **Handles multi-query commands** - Each GraphQL request gets its own file

## No Backwards Compatibility
- Remove all existing fixture files
- Re-record all scenarios from scratch
- Update all loading code to use new folder structure

## Context: Multiple GraphQL Queries per Command

Individual `dg api` invocations may call multiple independent GraphQL queries. For example, `dg api asset list` executes:

1. `ASSET_RECORDS_QUERY` - Get paginated asset keys
2. `ASSET_NODES_QUERY` - Get detailed metadata for those keys

The current single `responses.json` approach only captures the final combined result, losing the individual GraphQL responses. The folder-per-scenario structure will capture each GraphQL query separately, enabling better testing and debugging.

## Final Output Format

The `cli_output.txt` file contains the actual CLI output, which may be:
- JSON format (if `--json` flag is used)
- Formatted text (if no `--json` flag)

This is separate from the individual GraphQL responses which are always JSON.