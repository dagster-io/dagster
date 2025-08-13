"""GraphQL implementation for run operations."""

from typing import TYPE_CHECKING, Any, Optional

from dagster_shared.plus.config import DagsterPlusCliConfig

from dagster_dg_cli.utils.plus.gql_client import DagsterPlusGraphQLClient

if TYPE_CHECKING:
    from dagster_dg_cli.dagster_plus_api.schemas.run import RunEventList

# GraphQL queries
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


def _filter_events_by_type(
    events: list[dict[str, Any]], event_type: Optional[str]
) -> list[dict[str, Any]]:
    """Filter events by event type if specified."""
    if not event_type:
        return events

    # Split comma-separated types and normalize
    types = [t.strip().upper() for t in event_type.split(",")]

    filtered = []
    for event in events:
        event_type_val = event.get("eventType")
        if event_type_val and event_type_val.upper() in types:
            filtered.append(event)

    return filtered


def _filter_events_by_step(
    events: list[dict[str, Any]], step_key: Optional[str]
) -> list[dict[str, Any]]:
    """Filter events by step key if specified."""
    if not step_key:
        return events

    filtered = []
    for event in events:
        event_step = event.get("stepKey", "")
        if event_step and step_key.lower() in event_step.lower():
            filtered.append(event)

    return filtered


def list_run_events_via_graphql(
    config: DagsterPlusCliConfig,
    run_id: str,
    limit: Optional[int] = None,
    event_type: Optional[str] = None,
    step_key: Optional[str] = None,
) -> "RunEventList":
    """Fetch run events using GraphQL.
    This is an implementation detail that can be replaced with REST calls later.
    """
    # Import pydantic models only when needed
    from dagster_dg_cli.dagster_plus_api.schemas.run import RunEvent, RunEventLevel, RunEventList

    client = DagsterPlusGraphQLClient.from_config(config)
    result = client.execute(RUN_EVENTS_QUERY, {"runId": run_id, "limit": limit or 100})

    # Handle case where result is None (empty response)
    if result is None:
        raise RuntimeError(f"No response from GraphQL API for run {run_id}")

    # Handle GraphQL response structure
    logs_result = result.get("logsForRun")
    if not logs_result:
        raise RuntimeError(f"No events found for run {run_id}")

    # Check for error types in GraphQL response
    if logs_result.get("__typename") == "PythonError":
        error_msg = logs_result.get("message", "Unknown error")
        raise RuntimeError(f"Failed to get events for run {run_id}: {error_msg}")

    if logs_result.get("__typename") == "RunNotFoundError":
        error_msg = logs_result.get("message", f"Run {run_id} not found")
        raise RuntimeError(error_msg)

    # Extract events from the connection
    events_data = []
    if logs_result.get("events"):
        events_data = logs_result["events"]

    # Apply filtering
    if event_type:
        events_data = _filter_events_by_type(events_data, event_type)

    if step_key:
        events_data = _filter_events_by_step(events_data, step_key)

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

    return RunEventList(
        items=events,
        total=len(events),
        cursor=logs_result.get("cursor"),
        has_more=logs_result.get("hasMore", False),
    )
