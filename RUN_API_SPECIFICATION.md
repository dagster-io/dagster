# Dagster Plus Run API Specification

This document preserves the specification and implementation details for the Dagster Plus run API functionality, focusing on the CLI interface, data models, and GraphQL queries that can be reused across different infrastructure implementations.

## CLI Interface Specification

### Command Structure

```bash
dg plus api run events <run-id> [OPTIONS]
```

### Command Arguments

- **`run-id`** (required): The unique identifier of the run to query events for

### Command Options

| Option    | Type    | Default | Description                                                                                                |
| --------- | ------- | ------- | ---------------------------------------------------------------------------------------------------------- |
| `--type`  | string  | none    | Filter by event type (STEP_SUCCESS, STEP_FAILURE, MATERIALIZATION, etc.) - supports comma-separated values |
| `--step`  | string  | none    | Filter by step key (supports partial matching, case-insensitive)                                           |
| `--limit` | integer | 100     | Maximum number of events to return                                                                         |
| `--json`  | flag    | false   | Output in JSON format for machine readability                                                              |

### Usage Examples

```bash
# Basic usage - get all events for a run
dg plus api run events abc123-def456

# Filter by event type
dg plus api run events abc123-def456 --type STEP_SUCCESS,STEP_FAILURE

# Filter by step key (partial matching)
dg plus api run events abc123-def456 --step transform

# Limit results and output as JSON
dg plus api run events abc123-def456 --limit 50 --json

# Combined filtering
dg plus api run events abc123-def456 --type MATERIALIZATION --step asset --limit 20
```

### Output Formats

#### Human-Readable Table Format

```
Events for run abc123-def456:

TIMESTAMP            TYPE                 STEP_KEY                      MESSAGE
-------------------- -------------------- ----------------------------- --------------------------------------------------
2025-08-12T18:04:12  STEP_SUCCESS        transform_data                Step completed successfully
2025-08-12T18:04:15  MATERIALIZATION     create_asset                  Asset materialized: my_asset

Total events: 2
```

#### JSON Format

```json
{
  "run_id": "abc123-def456",
  "events": [
    {
      "runId": "abc123-def456",
      "message": "Step completed successfully",
      "timestamp": "2025-08-12T18:04:12",
      "level": "INFO",
      "stepKey": "transform_data",
      "eventType": "STEP_SUCCESS"
    }
  ],
  "count": 1
}
```

### Error Handling

#### Human-Readable Error Format

```
Error querying Dagster Plus API: Run abc123-def456 not found
```

#### JSON Error Format

```json
{
  "error": "Run abc123-def456 not found",
  "run_id": "abc123-def456"
}
```

## Data Models & Schemas

### RunEvent Model

Represents a single event from a run execution.

```python
class RunEvent(BaseModel):
    run_id: str                    # The run identifier
    message: str                   # Human-readable event message
    timestamp: str                 # ISO 8601 timestamp string
    level: RunEventLevel          # Event severity level
    step_key: Optional[str]       # Step identifier (may be None for run-level events)
    event_type: str               # Event type identifier
```

### RunEventLevel Enum

Defines the severity levels for run events.

```python
class RunEventLevel(str, Enum):
    CRITICAL = "CRITICAL"
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"
    DEBUG = "DEBUG"
```

### RunEventList Model

Represents a paginated response containing multiple run events.

```python
class RunEventList(BaseModel):
    items: list[RunEvent]         # List of run events
    total: int                    # Total number of events returned
    cursor: Optional[str]         # Pagination cursor for next page
    has_more: bool               # Whether more events are available
```

### Model Configuration

All models use Pydantic with the following configuration:

```python
class Config:
    from_attributes = True  # For future ORM compatibility
```

## GraphQL Query Specifications

### Primary Query: RUN_EVENTS_QUERY

The core GraphQL query for retrieving run events:

```graphql
query CliRunEventsQuery($runId: ID!, $limit: Int, $afterCursor: String) {
  logsForRun(runId: $runId, limit: $limit, afterCursor: $afterCursor) {
    __typename
    ... on EventConnection {
      events {
        __typename
        ... on MessageEvent {
          runId
          message
          timestamp
          level
          stepKey
          eventType
        }
      }
      cursor
      hasMore
    }
    ... on PythonError {
      message
      stack
    }
    ... on RunNotFoundError {
      message
    }
  }
}
```

### Query Variables

| Variable      | Type   | Required | Description                                       |
| ------------- | ------ | -------- | ------------------------------------------------- |
| `runId`       | ID     | Yes      | The run identifier to query events for            |
| `limit`       | Int    | No       | Maximum number of events to return (default: 100) |
| `afterCursor` | String | No       | Pagination cursor for retrieving subsequent pages |

### Response Structure

The query returns a union type that can be one of:

#### Success Response: EventConnection

```graphql
{
  "__typename": "EventConnection",
  "events": [
    {
      "__typename": "MessageEvent",
      "runId": "abc123-def456",
      "message": "Step completed successfully",
      "timestamp": "2025-08-12T18:04:12",
      "level": "INFO",
      "stepKey": "transform_data",
      "eventType": "STEP_SUCCESS"
    }
  ],
  "cursor": "eyJvZmZzZXQiOjEwfQ==",
  "hasMore": false
}
```

#### Error Response: PythonError

```graphql
{
  "__typename": "PythonError",
  "message": "Internal server error occurred",
  "stack": "Traceback (most recent call last)..."
}
```

#### Error Response: RunNotFoundError

```graphql
{
  "__typename": "RunNotFoundError",
  "message": "Run abc123-def456 not found"
}
```

### GraphQL Schema Context

The query operates within the broader Dagster Plus GraphQL schema:

- **Root Query Type**: `CloudQuery`
- **Operation**: `logsForRun(runId: ID!, limit: Int, afterCursor: String)`
- **Return Type**: Union of `EventConnection | PythonError | RunNotFoundError`

## Filtering & Data Processing

### Event Type Filtering

Client-side filtering logic for event types:

```python
def _filter_events_by_type(events: list[dict], event_type: Optional[str]) -> list[dict]:
    if not event_type:
        return events

    # Split comma-separated types and normalize to uppercase
    types = [t.strip().upper() for t in event_type.split(",")]

    filtered = []
    for event in events:
        event_type_val = event.get("eventType")
        if event_type_val and event_type_val.upper() in types:
            filtered.append(event)

    return filtered
```

### Step Key Filtering

Client-side filtering logic for step keys:

```python
def _filter_events_by_step(events: list[dict], step_key: Optional[str]) -> list[dict]:
    if not step_key:
        return events

    filtered = []
    for event in events:
        event_step = event.get("stepKey", "")
        if event_step and step_key.lower() in event_step.lower():
            filtered.append(event)

    return filtered
```

### Data Transformation

Converting GraphQL response to Pydantic models:

```python
# Extract events from GraphQL response
events_data = logs_result.get("events", [])

# Apply client-side filters
if event_type:
    events_data = _filter_events_by_type(events_data, event_type)

if step_key:
    events_data = _filter_events_by_step(events_data, step_key)

# Convert to Pydantic models
events = [
    RunEvent(
        run_id=e["runId"],
        message=e["message"],
        timestamp=e["timestamp"],
        level=RunEventLevel[e["level"]],
        step_key=e.get("stepKey"),
        event_type=e["eventType"],
    )
    for e in events_data
]
```

### Pagination Strategy

The API uses cursor-based pagination:

1. **Initial Request**: No cursor provided, returns first page of results
2. **Subsequent Requests**: Use `cursor` from previous response as `afterCursor` parameter
3. **Completion**: When `hasMore` is `false`, no more pages available

Example pagination flow:

```python
# Initial request
result = client.execute(RUN_EVENTS_QUERY, {"runId": run_id, "limit": 100})

# Check for more pages
if result["logsForRun"]["hasMore"]:
    cursor = result["logsForRun"]["cursor"]

    # Next page request
    next_result = client.execute(RUN_EVENTS_QUERY, {
        "runId": run_id,
        "limit": 100,
        "afterCursor": cursor
    })
```

## Error Response Patterns

### GraphQL Error Detection

The implementation checks for error types in the GraphQL response:

```python
# Check response type
logs_result = result.get("logsForRun")
typename = logs_result.get("__typename")

if typename == "PythonError":
    error_msg = logs_result.get("message", "Unknown error")
    raise RuntimeError(f"Failed to get events for run {run_id}: {error_msg}")

if typename == "RunNotFoundError":
    error_msg = logs_result.get("message", f"Run {run_id} not found")
    raise RuntimeError(error_msg)
```

### Common Error Scenarios

1. **Run Not Found**: When querying a non-existent run ID
2. **Python Error**: Internal server errors during query execution
3. **Empty Response**: No response from GraphQL API
4. **Authentication Error**: Invalid or missing authentication credentials
5. **Network Error**: Connection issues to Dagster Plus

## Authentication & Configuration

### Required Authentication

The API requires Dagster Plus authentication:

```python
# Configuration check
if not DagsterPlusCliConfig.exists():
    raise click.UsageError(
        "`dg plus` commands require authentication with Dagster Plus. Run `dg plus login` to authenticate."
    )
```

### GraphQL Client Headers

The implementation uses the following headers:

```python
headers = {
    "Dagster-Cloud-Api-Token": config.user_token,
    "Dagster-Cloud-Organization": config.organization,
    "Dagster-Cloud-Deployment": config.default_deployment,
}
```

### Endpoint Structure

GraphQL endpoint follows the pattern:

```
{organization_url}/graphql
```

Where `organization_url` is retrieved from the user's Dagster Plus configuration.

## Implementation Contract

This specification defines the contract for run event querying that must be preserved across different infrastructure implementations:

1. **CLI Interface**: Command structure, options, and output formats must remain consistent
2. **Data Models**: Pydantic model structure and field types must be maintained
3. **Filtering Logic**: Client-side filtering algorithms for event type and step key
4. **Error Handling**: Consistent error response patterns and messaging
5. **Authentication**: Dagster Plus configuration and authentication requirements

The GraphQL query implementation serves as the reference for data retrieval patterns, but the underlying transport mechanism may be adapted for different infrastructure while preserving the same data contract.
