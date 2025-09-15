# Dagster Plus Run API Implementation Plan

This document provides a detailed implementation plan for the Run API specification defined in `RUN_API_SPECIFICATION.md`, adapted to the corrected command structure and following the existing Dagster Plus CLI architecture patterns.

## Command Structure

### Primary Commands

- **Run metadata**: `dg api run get <run-id>` - Returns basic run information/metadata
- **Run events**: `dg api run-events get <run-id>` - Returns events with comprehensive filtering options

### Command Arguments and Options

#### `dg api run get <run-id>`

- **Purpose**: Retrieve basic run metadata (status, timing, configuration)
- **Arguments**:
  - `run-id` (required): The unique identifier of the run
- **Options**:
  - `--json`: Output in JSON format for machine readability

#### `dg api run-events get <run-id>`

- **Purpose**: Retrieve run events with filtering and pagination
- **Arguments**:
  - `run-id` (required): The unique identifier of the run to query events for
- **Options**:
  - `--type`: Filter by event type (supports comma-separated values)
  - `--step`: Filter by step key (partial matching, case-insensitive)
  - `--limit`: Maximum number of events to return (default: 100)
  - `--json`: Output in JSON format for machine readability

## Implementation Architecture

Following the established 3-layer architecture: **CLI → REST API → GraphQL**

### Layer 1: Schema Definitions

#### File: `api_layer/schemas/run.py`

```python
"""Run metadata schema definitions."""

from pydantic import BaseModel
from typing import Optional, List
from enum import Enum

class RunStatus(str, Enum):
    """Run execution status."""
    QUEUED = "QUEUED"
    STARTING = "STARTING"
    STARTED = "STARTED"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    CANCELING = "CANCELING"
    CANCELED = "CANCELED"

class Run(BaseModel):
    """Single run metadata model."""
    id: str
    status: RunStatus
    created_at: str  # ISO 8601 timestamp
    started_at: Optional[str] = None  # ISO 8601 timestamp
    ended_at: Optional[str] = None  # ISO 8601 timestamp
    pipeline_name: Optional[str] = None
    mode: Optional[str] = None

    class Config:
        from_attributes = True
```

#### File: `api_layer/schemas/run_event.py`

```python
"""Run event schema definitions."""

from pydantic import BaseModel
from typing import Optional, List
from enum import Enum

class RunEventLevel(str, Enum):
    """Event severity levels."""
    CRITICAL = "CRITICAL"
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"
    DEBUG = "DEBUG"

class RunEvent(BaseModel):
    """Single run event model."""
    run_id: str
    message: str
    timestamp: str  # ISO 8601 timestamp
    level: RunEventLevel
    step_key: Optional[str] = None
    event_type: str

    class Config:
        from_attributes = True

class RunEventList(BaseModel):
    """Paginated run events response."""
    items: List[RunEvent]
    total: int
    cursor: Optional[str] = None
    has_more: bool = False

    class Config:
        from_attributes = True
```

### Layer 2: GraphQL Adapters

#### File: `api_layer/graphql_adapter/run.py`

```python
"""GraphQL adapter for run metadata."""

from typing import Dict, Any
from dagster_shared.plus.config import DagsterPlusCliConfig
from dagster_dg_cli.utils.plus.gql_client import IGraphQLClient
from dagster_dg_cli.cli.api.shared import DgApiError, get_graphql_error_mappings, get_default_error_mapping

RUN_METADATA_QUERY = """
query DgApiRunMetadataQuery($runId: ID!) {
    runOrError(runId: $runId) {
        __typename
        ... on Run {
            id
            status
            creationTime
            startTime
            endTime
            pipelineName
            mode
        }
        ... on RunNotFoundError {
            message
        }
        ... on PythonError {
            message
            stack
        }
    }
}
"""

def get_run_via_graphql(client: IGraphQLClient, run_id: str) -> Dict[str, Any]:
    """Get run metadata via GraphQL."""
    variables = {"runId": run_id}
    result = client.execute(RUN_METADATA_QUERY, variables)

    run_result = result.get("runOrError")
    if not run_result:
        raise DgApiError(
            message="Empty response from GraphQL API",
            code="INTERNAL_ERROR",
            status_code=500
        )

    typename = run_result.get("__typename")

    # Handle GraphQL errors
    error_mappings = get_graphql_error_mappings()
    if typename in error_mappings:
        mapping = error_mappings[typename]
        error_msg = run_result.get("message", f"Unknown error: {typename}")
        raise DgApiError(
            message=error_msg,
            code=mapping.code,
            status_code=mapping.status_code
        )

    if typename != "Run":
        # Unmapped error type
        mapping = get_default_error_mapping()
        error_msg = run_result.get("message", f"Unknown error: {typename}")
        raise DgApiError(
            message=error_msg,
            code=mapping.code,
            status_code=mapping.status_code
        )

    return run_result
```

#### File: `api_layer/graphql_adapter/run_event.py`

```python
"""GraphQL adapter for run events."""

from typing import Dict, Any, List, Optional
from dagster_shared.plus.config import DagsterPlusCliConfig
from dagster_dg_cli.utils.plus.gql_client import IGraphQLClient
from dagster_dg_cli.cli.api.shared import DgApiError, get_graphql_error_mappings, get_default_error_mapping

# Exact GraphQL query from specification
RUN_EVENTS_QUERY = """
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
"""

def _filter_events_by_type(events: List[Dict], event_type: Optional[str]) -> List[Dict]:
    """Client-side filtering logic for event types."""
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

def _filter_events_by_step(events: List[Dict], step_key: Optional[str]) -> List[Dict]:
    """Client-side filtering logic for step keys."""
    if not step_key:
        return events

    filtered = []
    for event in events:
        event_step = event.get("stepKey", "")
        if event_step and step_key.lower() in event_step.lower():
            filtered.append(event)

    return filtered

def get_run_events_via_graphql(
    client: IGraphQLClient,
    run_id: str,
    limit: int = 100,
    after_cursor: Optional[str] = None,
    event_type: Optional[str] = None,
    step_key: Optional[str] = None
) -> Dict[str, Any]:
    """Get run events via GraphQL with client-side filtering."""
    variables = {"runId": run_id, "limit": limit}
    if after_cursor:
        variables["afterCursor"] = after_cursor

    result = client.execute(RUN_EVENTS_QUERY, variables)

    logs_result = result.get("logsForRun")
    if not logs_result:
        raise DgApiError(
            message="Empty response from GraphQL API",
            code="INTERNAL_ERROR",
            status_code=500
        )

    typename = logs_result.get("__typename")

    # Handle GraphQL errors
    error_mappings = get_graphql_error_mappings()
    if typename in error_mappings:
        mapping = error_mappings[typename]
        error_msg = logs_result.get("message", f"Unknown error: {typename}")
        raise DgApiError(
            message=error_msg,
            code=mapping.code,
            status_code=mapping.status_code
        )

    if typename != "EventConnection":
        # Unmapped error type
        mapping = get_default_error_mapping()
        error_msg = logs_result.get("message", f"Unknown error: {typename}")
        raise DgApiError(
            message=error_msg,
            code=mapping.code,
            status_code=mapping.status_code
        )

    # Extract and filter events
    events_data = logs_result.get("events", [])

    # Apply client-side filters
    if event_type:
        events_data = _filter_events_by_type(events_data, event_type)

    if step_key:
        events_data = _filter_events_by_step(events_data, step_key)

    return {
        "events": events_data,
        "cursor": logs_result.get("cursor"),
        "hasMore": logs_result.get("hasMore", False)
    }
```

### Layer 3: API Classes

#### File: `api_layer/api/run.py`

```python
"""Run metadata API implementation."""

from dagster_shared.plus.config import DagsterPlusCliConfig
from dagster_dg_cli.utils.plus.gql_client import IGraphQLClient
from dagster_dg_cli.api_layer.schemas.run import Run
from dagster_dg_cli.api_layer.graphql_adapter.run import get_run_via_graphql

class DgApiRunApi:
    """API for run metadata operations."""

    def __init__(self, config: DagsterPlusCliConfig, client: IGraphQLClient):
        self.config = config
        self.client = client

    def get_run(self, run_id: str) -> Run:
        """Get run metadata by ID."""
        run_data = get_run_via_graphql(self.client, run_id)

        return Run(
            id=run_data["id"],
            status=run_data["status"],
            created_at=run_data["creationTime"],
            started_at=run_data.get("startTime"),
            ended_at=run_data.get("endTime"),
            pipeline_name=run_data.get("pipelineName"),
            mode=run_data.get("mode")
        )
```

#### File: `api_layer/api/run_event.py`

```python
"""Run events API implementation."""

from typing import Optional
from dagster_shared.plus.config import DagsterPlusCliConfig
from dagster_dg_cli.utils.plus.gql_client import IGraphQLClient
from dagster_dg_cli.api_layer.schemas.run_event import RunEvent, RunEventList, RunEventLevel
from dagster_dg_cli.api_layer.graphql_adapter.run_event import get_run_events_via_graphql

class DgApiRunEventApi:
    """API for run events operations."""

    def __init__(self, config: DagsterPlusCliConfig, client: IGraphQLClient):
        self.config = config
        self.client = client

    def get_events(
        self,
        run_id: str,
        event_type: Optional[str] = None,
        step_key: Optional[str] = None,
        limit: int = 100,
        after_cursor: Optional[str] = None
    ) -> RunEventList:
        """Get run events with filtering options."""
        events_data = get_run_events_via_graphql(
            self.client,
            run_id=run_id,
            limit=limit,
            after_cursor=after_cursor,
            event_type=event_type,
            step_key=step_key
        )

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
            for e in events_data["events"]
        ]

        return RunEventList(
            items=events,
            total=len(events),
            cursor=events_data.get("cursor"),
            has_more=events_data.get("hasMore", False)
        )
```

### Layer 4: CLI Commands

#### File: `cli/api/run.py`

```python
"""CLI commands for run metadata."""

import json
import click
from dagster_dg_cli.cli.api.client import create_dg_api_graphql_client
from dagster_dg_cli.cli.api.shared import get_config_or_error, format_error_for_output
from dagster_dg_cli.api_layer.api.run import DgApiRunApi

@click.group(name="run")
def run_group():
    """Manage runs."""
    pass

@run_group.command("get")
@click.argument("run_id")
@click.option("--json", "output_json", is_flag=True, help="Output in JSON format")
@click.pass_context
def get_run(ctx: click.Context, run_id: str, output_json: bool):
    """Get run metadata by ID."""
    try:
        config = get_config_or_error()
        client = create_dg_api_graphql_client(ctx, config)
        api = DgApiRunApi(config, client)

        run = api.get_run(run_id)

        if output_json:
            click.echo(run.model_dump_json(indent=2))
        else:
            click.echo(f"Run ID: {run.id}")
            click.echo(f"Status: {run.status}")
            click.echo(f"Created: {run.created_at}")
            if run.started_at:
                click.echo(f"Started: {run.started_at}")
            if run.ended_at:
                click.echo(f"Ended: {run.ended_at}")
            if run.pipeline_name:
                click.echo(f"Pipeline: {run.pipeline_name}")
            if run.mode:
                click.echo(f"Mode: {run.mode}")

    except Exception as e:
        formatted_output, exit_code = format_error_for_output(e, output_json)
        click.echo(formatted_output, err=True)
        ctx.exit(exit_code)
```

#### File: `cli/api/run_event.py`

```python
"""CLI commands for run events."""

import json
import click
from dagster_dg_cli.cli.api.client import create_dg_api_graphql_client
from dagster_dg_cli.cli.api.shared import get_config_or_error, format_error_for_output
from dagster_dg_cli.api_layer.api.run_event import DgApiRunEventApi

def format_run_events_table(events, run_id: str) -> str:
    """Format run events as human-readable table."""
    if not events.items:
        return f"No events found for run {run_id}"

    lines = [f"Events for run {run_id}:", ""]

    # Table header
    header = f"{'TIMESTAMP':<20} {'TYPE':<20} {'STEP_KEY':<30} {'MESSAGE':<50}"
    separator = "-" * len(header)
    lines.extend([header, separator])

    # Table rows
    for event in events.items:
        timestamp = event.timestamp[:19]  # Truncate to YYYY-MM-DDTHH:MM:SS
        event_type = event.event_type
        step_key = event.step_key or ""
        message = event.message[:47] + "..." if len(event.message) > 50 else event.message

        row = f"{timestamp:<20} {event_type:<20} {step_key:<30} {message:<50}"
        lines.append(row)

    lines.extend(["", f"Total events: {events.total}"])
    return "\n".join(lines)

def format_run_events_json(events, run_id: str) -> str:
    """Format run events as JSON."""
    return json.dumps({
        "run_id": run_id,
        "events": [
            {
                "runId": event.run_id,
                "message": event.message,
                "timestamp": event.timestamp,
                "level": event.level,
                "stepKey": event.step_key,
                "eventType": event.event_type
            }
            for event in events.items
        ],
        "count": events.total
    }, indent=2)

@click.group(name="run-events")
def run_events_group():
    """Manage run events."""
    pass

@run_events_group.command("get")
@click.argument("run_id")
@click.option("--type", "event_type", help="Filter by event type (comma-separated)")
@click.option("--step", "step_key", help="Filter by step key (partial matching)")
@click.option("--limit", type=int, default=100, help="Maximum number of events to return")
@click.option("--json", "output_json", is_flag=True, help="Output in JSON format")
@click.pass_context
def get_run_events(
    ctx: click.Context,
    run_id: str,
    event_type: str,
    step_key: str,
    limit: int,
    output_json: bool
):
    """Get run events with filtering options."""
    try:
        config = get_config_or_error()
        client = create_dg_api_graphql_client(ctx, config)
        api = DgApiRunEventApi(config, client)

        events = api.get_events(
            run_id=run_id,
            event_type=event_type,
            step_key=step_key,
            limit=limit
        )

        if output_json:
            click.echo(format_run_events_json(events, run_id))
        else:
            click.echo(format_run_events_table(events, run_id))

    except Exception as e:
        if output_json:
            error_output = json.dumps({
                "error": str(e),
                "run_id": run_id
            })
            click.echo(error_output, err=True)
        else:
            click.echo(f"Error querying Dagster Plus API: {e}", err=True)

        # Use appropriate exit code based on error type
        formatted_output, exit_code = format_error_for_output(e, output_json)
        ctx.exit(exit_code)
```

### Layer 5: Integration

#### File: `cli/api/cli_group.py` (Modified)

```python
"""Main API group registration."""

import click
from dagster_dg_core.utils import DgClickGroup

from dagster_dg_cli.cli.api.asset import asset_group
from dagster_dg_cli.cli.api.deployment import deployment_group
from dagster_dg_cli.cli.api.run import run_group
from dagster_dg_cli.cli.api.run_event import run_events_group

@click.group(
    name="api",
    cls=DgClickGroup,
    unlaunched=True,
    commands={
        "asset": asset_group,
        "deployment": deployment_group,
        "run": run_group,
        "run-events": run_events_group,
    },
)
def api_group():
    """Make REST-like API calls to Dagster Plus."""
```

#### File: `cli/api/formatters.py` (Modified)

Add the run event formatters to the existing formatters file:

```python
# Add to existing imports
from dagster_dg_cli.api_layer.schemas.run import Run
from dagster_dg_cli.api_layer.schemas.run_event import RunEventList

def format_run(run: Run, as_json: bool) -> str:
    """Format single run for output."""
    if as_json:
        return run.model_dump_json(indent=2)

    lines = [
        f"Run ID: {run.id}",
        f"Status: {run.status}",
        f"Created: {run.created_at}",
    ]

    if run.started_at:
        lines.append(f"Started: {run.started_at}")
    if run.ended_at:
        lines.append(f"Ended: {run.ended_at}")
    if run.pipeline_name:
        lines.append(f"Pipeline: {run.pipeline_name}")
    if run.mode:
        lines.append(f"Mode: {run.mode}")

    return "\n".join(lines)

def format_run_events(events: RunEventList, run_id: str, as_json: bool) -> str:
    """Format run events for output."""
    if as_json:
        return format_run_events_json(events, run_id)
    else:
        return format_run_events_table(events, run_id)
```

#### Import/Export Updates

**File: `api_layer/schemas/__init__.py`**

```python
from .run import Run, RunStatus
from .run_event import RunEvent, RunEventLevel, RunEventList
```

**File: `api_layer/api/__init__.py`**

```python
from .run import DgApiRunApi
from .run_event import DgApiRunEventApi
```

## Testing Strategy

### Test Structure

Following existing patterns from `api_tests/`:

#### File: `dagster_dg_cli_tests/cli_tests/api_tests/run_tests/scenarios.yaml`

```yaml
success_get_run:
  command: "dg api run get test-run-123 --json"

success_get_run_human:
  command: "dg api run get test-run-123"

run_not_found:
  command: "dg api run get nonexistent-run --json"
```

#### File: `dagster_dg_cli_tests/cli_tests/api_tests/run_event_tests/scenarios.yaml`

```yaml
success_get_events:
  command: "dg api run-events get test-run-123 --json"

success_get_events_filtered:
  command: "dg api run-events get test-run-123 --type STEP_SUCCESS,STEP_FAILURE --step transform --limit 50 --json"

success_get_events_human:
  command: "dg api run-events get test-run-123"

events_run_not_found:
  command: "dg api run-events get nonexistent-run --json"
```

### Test Execution

1. **Record GraphQL responses**: `dagster-dev dg-api-record run --recording success_get_run`
2. **Record event responses**: `dagster-dev dg-api-record run-events --recording success_get_events`
3. **Generate snapshots**: `pytest api_tests/run_tests/ --snapshot-update`
4. **Update compliance tests**: Add new API classes to `test_rest_compliance.py`

## Implementation Phases

### Phase 1: Core Infrastructure

1. Create schema definitions (`run.py`, `run_event.py`)
2. Implement GraphQL adapters with exact queries from spec
3. Add error mappings for `RunNotFoundError` to `shared.py`

### Phase 2: API Layer

1. Implement `DgApiRunApi` class with `get_run()` method
2. Implement `DgApiRunEventApi` class with full filtering support
3. Add client-side filtering functions as specified

### Phase 3: CLI Layer

1. Create CLI commands with exact argument/option structure
2. Implement output formatters matching specification exactly
3. Add proper error handling and authentication checks

### Phase 4: Integration & Testing

1. Update CLI group registration and imports
2. Create test scenarios and record GraphQL fixtures
3. Generate snapshot tests for output consistency
4. Update compliance tests for new API classes

## Compliance with Specification

This implementation ensures 100% compliance with `RUN_API_SPECIFICATION.md`:

- **CLI Interface**: Exact command structure, arguments, and options
- **Data Models**: All Pydantic models match specification exactly
- **GraphQL Query**: Uses the exact `logsForRun` query from spec
- **Filtering Logic**: Client-side filtering algorithms as specified
- **Output Formats**: Table and JSON formats match specification exactly
- **Error Handling**: Proper error mapping and consistent error responses
- **Authentication**: Uses existing Dagster Plus authentication patterns

The implementation maintains the established patterns while providing the exact interface defined in the specification.
