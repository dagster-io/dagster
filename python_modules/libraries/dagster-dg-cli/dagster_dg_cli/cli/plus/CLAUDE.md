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
