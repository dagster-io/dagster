# Dagster API CLI Conventions

This document outlines the conventions for implementing CLI commands in the `dg api` namespace, following GitHub CLI best practices.

## Command Structure

The API commands follow the pattern: `dg api <noun> <verb>`

### Examples:

```bash
dg api deployment list
dg api deployment view <id>
dg api secret list
dg api secret create
dg api agent list
```

This mirrors GitHub CLI patterns like:

- `gh repo list`
- `gh issue create`
- `gh pr view`

## File Organization

### Directory Structure:

```
dagster_dg_cli/cli/plus/api/
├── __init__.py                 # Main API group
├── deployment.py               # Deployment noun with all verbs
├── secret.py                   # Secret noun with all verbs
├── agent.py                    # Agent noun with all verbs
├── check.py                    # Asset check noun with all verbs
├── code_location.py            # Code location noun with all verbs
├── env_var.py                  # Environment variable noun with all verbs
└── shared.py                   # Shared utilities
```

### Implementation Pattern:

Each noun file (e.g., `deployment.py`) contains:

1. **Noun group** - Click group for the resource
2. **Verb commands** - Individual commands for operations
3. **Helper functions** - Shared utilities for that noun

## Standard Flags

### Required for ALL API Commands:

- `--json` flag for machine-readable JSON output
- Human-readable table format as default

### Common Optional Flags:

- `--limit <n>` for pagination (default: 50)
- `--cursor <cursor>` for cursor-based pagination (preferred)
- `--filter <query>` for filtering results
- `--format <table|json>` (alternative to --json flag)

## Output Formatting

### Human-Readable (Default):

```
Name: my-deployment
ID: abc-123
Type: SERVERLESS

Name: other-deployment
ID: def-456
Type: HYBRID
```

### JSON Format (--json flag):

```json
[
  {
    "name": "my-deployment",
    "id": "abc-123",
    "type": "SERVERLESS"
  },
  {
    "name": "other-deployment",
    "id": "def-456",
    "type": "HYBRID"
  }
]
```

## Error Handling Standards

### Enhanced JSON Error Format (--json flag):

```json
{
  "error": "Human-readable error message",
  "code": "MACHINE_READABLE_CODE",
  "statusCode": 401,
  "type": "error_category"
}
```

### HTTP Status Code Mapping:
- **401**: Authentication errors (UNAUTHORIZED)
- **403**: Authorization errors (FORBIDDEN, INSUFFICIENT_PERMISSIONS)
- **400**: Client errors (INVALID_INPUT, VALIDATION_ERROR)
- **404**: Resource not found (RESOURCE_NOT_FOUND, PIPELINE_NOT_FOUND)
- **422**: Migration/upgrade required (MIGRATION_REQUIRED, UPGRADE_REQUIRED)
- **500**: Server errors (INTERNAL_ERROR, PYTHON_ERROR)

### Error Types:
- `authentication_error`: Authentication required or failed
- `authorization_error`: Valid auth but insufficient permissions
- `client_error`: Invalid request parameters or format
- `server_error`: Internal server or GraphQL errors
- `not_found_error`: Requested resource doesn't exist
- `migration_error`: Migration or upgrade required

### Human-Readable Format (default):

```
Error querying Dagster Plus API: Unauthorized access
```

### Example Usage:

```bash
# Command that fails with authentication error
$ dg api deployment list --json
{
  "error": "Authentication required. Run 'dg plus login' to authenticate.",
  "code": "UNAUTHORIZED",
  "statusCode": 401,
  "type": "authentication_error"
}

# Client can handle programmatically
if error.code == "UNAUTHORIZED":
    prompt_for_login()
elif error.type == "client_error":
    show_usage_help()
```

## Pagination Standards

**All list commands MUST implement pagination by default:**

1. **Default Limit**: 50 items per page (always applied)
2. **Cursor-based Pagination**: ALWAYS prefer cursor-based over offset-based
3. **Standard Flags**:
   - `--limit <n>`: Override default limit (max: 1000)
   - `--cursor <cursor>`: Continue from specific cursor
   - `--all`: Bypass pagination (use with caution)

4. **Response Format**:
   ```json
   {
     "items": [...],
     "cursor": "next_cursor_value",
     "hasMore": true
   }
   ```

## GraphQL Abstraction

The API commands provide a REST-like interface that abstracts GraphQL complexity:

1. **Transform GraphQL responses** into REST-like JSON structures
2. **Normalize field names** (e.g., `deploymentName` → `name`)
3. **Hide GraphQL-specific concepts** like `__typename`
4. **Provide intuitive resource operations** (list, view, create, update, delete)

## Implementation Template

```python
"""<Noun> API commands following GitHub CLI patterns."""

import json
from typing import Any

import click
from dagster_dg_core.utils import DgClickCommand, DgClickGroup
from dagster_dg_core.utils.telemetry import cli_telemetry_wrapper
from dagster_shared.plus.config import DagsterPlusCliConfig


def _get_config_or_error() -> DagsterPlusCliConfig:
    """Get Dagster Plus config or raise error if not authenticated."""
    if not DagsterPlusCliConfig.exists():
        raise click.UsageError(
            "`dg plus` commands require authentication with Dagster Plus. Run `dg plus login` to authenticate."
        )
    return DagsterPlusCliConfig.get()


def _format_output(data: Any, as_json: bool) -> None:
    """Format output as JSON or human-readable format."""
    if as_json:
        click.echo(json.dumps(data, indent=2))
    else:
        # Human-readable format implementation
        # ... format logic here ...


@click.command(name="list", cls=DgClickCommand, unlaunched=True)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    help="Output in JSON format for machine readability",
)
@cli_telemetry_wrapper
def list_command(output_json: bool) -> None:
    """List all <resources> in the organization."""
    from dagster_dg_cli.utils.plus.gql_client import DagsterPlusGraphQLClient

    config = _get_config_or_error()

    # GraphQL query
    query = """
    query <QueryName> {
        <graphqlField> {
            field1
            field2
        }
    }
    """

    try:
        client = DagsterPlusGraphQLClient.from_config(config)
        result = client.execute(query)
        raw_data = result.get("<graphqlField>", [])

        # Transform to REST-like format
        api_response = [
            {
                "field1": item["field1"],
                "field2": item["field2"],
            }
            for item in raw_data
        ]

        _format_output(api_response, output_json)

    except Exception as e:
        if output_json:
            error_response = {"error": str(e)}
            click.echo(json.dumps(error_response), err=True)
        else:
            click.echo(f"Error querying Dagster Plus API: {e}", err=True)
        raise click.ClickException(f"Failed to list <resources>: {e}")


@click.group(
    name="<noun>",
    cls=DgClickGroup,
    unlaunched=True,
    commands={
        "list": list_command,
        # Add other verbs here
    },
)
def <noun>_group():
    """Manage <noun> in Dagster Plus."""
```

## Standard Verbs

### Read Operations:

- `list` - List all resources
- `view <id>` - View specific resource details
- `search <query>` - Search resources

### Write Operations:

- `create` - Create new resource
- `update <id>` - Update existing resource
- `delete <id>` - Delete resource

### Special Operations:

- `sync` - Synchronize resources
- `status` - Show status information

## Integration with DagsterPlusGraphQLClient

Always use `DagsterPlusGraphQLClient` from `dagster_dg_cli.utils.plus.gql_client`:

```python
from dagster_dg_cli.utils.plus.gql_client import DagsterPlusGraphQLClient

client = DagsterPlusGraphQLClient.from_config(config)
result = client.execute(query, variables)
```

**Never use** `dagster-cloud-cli` GraphQL client - the plus API has its own dedicated client.

## Testing Conventions

- Test both JSON and human-readable output formats
- Mock GraphQL responses for consistency
- Test error handling in both output modes
- Verify REST-like data transformation
- Ensure --json flag works on all commands

## Future Extensions

When adding new nouns or verbs:

1. **Follow the same file structure**
2. **Implement consistent flag patterns**
3. **Maintain output format consistency**
4. **Add comprehensive error handling**
5. **Update this documentation**

## Examples

### Current Implementation:

```bash
# List deployments in table format
dg api deployment list

# List deployments in JSON format
dg api deployment list --json
```

### Planned Extensions:

```bash
# Secret management
dg api secret list
dg api secret create --name API_KEY --value secret123

# Agent management
dg api agent list
dg api agent view <agent-id>

# Run management
dg api run list --limit 10
dg api run view <run-id>

# Asset check management
dg api check list
dg api check view <check-name>

# Code location management
dg api code-location list
dg api code-location view <location-name>

# Environment variable management
dg api env-var list
dg api env-var view <var-name>
```

This structure provides a clean, REST-like interface while hiding the complexity of GraphQL operations underneath.
