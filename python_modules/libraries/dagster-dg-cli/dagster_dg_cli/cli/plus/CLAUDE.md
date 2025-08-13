# Dagster Plus GraphQL Schema Summary

This document summarizes the GraphQL schema located in `schema.graphql` to provide quick reference without needing to parse the entire schema file.

## Root Types

- **CloudQuery**: Main query root with 50+ fields for data retrieval
- **CloudMutation**: Mutation root with 30+ operations for data modification
- **CloudSubscription**: Subscription root for real-time updates (runs, alerts, logs)

## Key Query Operations

### Deployments & Infrastructure

- `fullDeployments`: Get all deployments with names, IDs, types
- `currentDeployment`: Current deployment info including agent type
- `agents`: Agent status and metadata
- `agentTokensOrError`: Manage agent authentication tokens

### Runs & Execution

- `pipelineRunsOrError`: Query pipeline runs with filtering
- `pipelineRunOrError`: Get specific run details
- `runMetricsOrError`: Run execution metrics and statistics

### Assets & Data

- `assetNodesOrError`: Asset catalog and lineage information
- `assetObservationsOrError`: Asset observation data
- `materializations`: Asset materialization events

### Logs & Events

- `logsForRunOrError`: Structured logs for pipeline runs
- `capturedLogsMetadata`: Log capture configuration and status

### Secrets & Configuration

- `secretsOrError`: Environment secrets management
- `environmentVariablesOrError`: Environment variable configuration

## Key Mutation Operations

### Deployment Management

- `launchPipelineExecution`: Start pipeline runs
- `terminateRun`: Stop running pipelines
- `deletePipelineRun`: Remove run records

### Secrets & Config

- `createOrUpdateSecretForScopes`: Manage deployment secrets
- `setEnvironmentVariables`: Configure environment variables

### Agent Tokens

- `createAgentToken`: Generate new agent authentication tokens
- `revokeAgentToken`: Revoke existing tokens

## Event System Architecture

The schema implements a comprehensive event-driven system:

### Event Interfaces

- `DagsterEvent`: Base event interface (timestamp, runId, message)
- `MessageEvent`: Events with structured messages
- `ObjectStoreOperationEvent`: Object storage operation tracking

### Event Categories (30+ types)

**Pipeline Events:**

- `RunStartingEvent`, `RunStartEvent`, `RunSuccessEvent`, `RunFailureEvent`
- `RunCancelingEvent`, `RunCanceledEvent`

**Step Events:**

- `StepStartEvent`, `StepSuccessEvent`, `StepFailureEvent`
- `StepSkippedEvent`, `StepRetryEvent`

**Asset Events:**

- `AssetMaterializationEvent`: Asset creation/updates
- `AssetObservationEvent`: Asset monitoring data
- `AssetCheckEvaluationEvent`: Asset quality checks

**Resource Events:**

- `EngineEvent`: Execution engine operations
- `HookErroredEvent`, `HookSkippedEvent`: Hook execution results
- `ResourceInitStartedEvent`, `ResourceInitFailureEvent`

**Alert Events:**

- `AlertStartEvent`, `AlertSuccessEvent`, `AlertFailureEvent`

### Event Unions

- `DagsterEventUnion`: Union of all event types for polymorphic queries
- `StepEvent`: Union of step-specific events

## Relationship to dagster-graphql

The schemas are **mostly disjoint** but share core Dagster domain types:

- **Plus Schema**: Cloud-specific operations (deployments, agents, cloud infrastructure)
- **OSS Schema**: Core Dagster types (runs, assets, schedules, sensors)
- **Shared**: Basic domain objects like PipelineRun, Asset, LogLevel enums

## Usage with DagsterPlusGraphQLClient

The schema is designed to work with `DagsterPlusGraphQLClient`:

```python
from dagster_dg_cli.utils.plus.gql_client import DagsterPlusGraphQLClient

# Example: Query deployments
query = """
query CliDeploymentsQuery {
    fullDeployments {
        deploymentName
        deploymentId
        deploymentType
    }
}
"""

client = DagsterPlusGraphQLClient.from_config(config)
result = client.execute(query)
```

## Common Query Patterns

1. **List Resources**: `fullDeployments`, `agents`, `secretsOrError`
2. **Get Details**: `pipelineRunOrError`, `currentDeployment`
3. **Filter/Search**: Most queries support filtering parameters
4. **Error Handling**: Results use `OrError` pattern with union types for error handling
5. **Pagination**: Many queries support cursor-based pagination

## Implementation Files

- **Schema**: `schema.graphql` (main schema definition)
- **Queries**: `dagster_dg_cli/utils/plus/gql.py` (common GraphQL queries)
- **Test**: `test_query.py` (example usage with deployments query)

---

# API Noun Group Structure Standard

This section documents the standard structure for API noun groups (e.g., `run`, `deployment`, `asset`, etc.) in the `dagster_dg_cli/cli/plus/api/` directory.

## Current Structure Pattern

Each API noun currently follows this single-file structure pattern (as seen in `deployment.py`):

```
api/<noun>.py                  # Single file containing all commands for the noun
```

## File Structure

Each API noun file contains:

1. **Imports**: Standard imports for Click, DagsterPlusGraphQLClient, configuration
2. **Utility Functions**: Shared helper functions (like `_get_config_or_error()`)
3. **Command Functions**: Individual Click command functions for each verb
4. **Group Definition**: Click group that registers all commands

## Example Structure (from `deployment.py`)

```python
"""Deployment API commands following GitHub CLI patterns."""

import click
from dagster_dg_core.utils import DgClickCommand, DgClickGroup
from dagster_dg_core.utils.telemetry import cli_telemetry_wrapper
from dagster_shared.plus.config import DagsterPlusCliConfig

def _get_config_or_error() -> DagsterPlusCliConfig:
    """Shared utility for getting config."""
    # Implementation here

@click.command(name="list", cls=DgClickCommand, unlaunched=True)
@click.option("--json", "output_json", is_flag=True)
@cli_telemetry_wrapper
def list_deployments_command(output_json: bool) -> None:
    """List all deployments in the organization."""
    # Implementation here

@click.group(
    name="deployment",
    cls=DgClickGroup,
    unlaunched=True,
    commands={
        "list": list_deployments_command,
    },
)
def deployment_group():
    """Manage deployments in Dagster Plus."""
```

## Integration Pattern

Noun groups are registered in `api/cli_group.py`:

```python
from dagster_dg_cli.cli.plus.api.deployment import deployment_group
from dagster_dg_cli.cli.plus.api.run import run_group  # To be created

@click.group(
    name="api",
    cls=DgClickGroup,
    unlaunched=True,
    commands={
        "deployment": deployment_group,
        "run": run_group,
    },
)
def api_group():
    """Make REST-like API calls to Dagster Plus."""
```

## Key Conventions

1. **File Naming**: `<noun>.py` (e.g., `run.py`, `deployment.py`)
2. **Group Naming**: `<noun>_group` (e.g., `run_group`, `deployment_group`)
3. **Command Naming**: `<verb>_<noun>_command` (e.g., `events_run_command`)
4. **Config Pattern**: Use `_get_config_or_error()` utility function
5. **Error Handling**: Consistent JSON vs human-readable error output
6. **Telemetry**: All commands use `@cli_telemetry_wrapper`
7. **Unlaunched**: All use `unlaunched=True` flag
