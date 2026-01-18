"""GraphQL adapter for run events."""

from typing import Any, Optional

from dagster_dg_cli.utils.plus.gql_client import IGraphQLClient

# Enhanced GraphQL query with error information
RUN_EVENTS_QUERY = """
fragment errorFragment on PythonError {
    message
    className
    stack
    cause {
        message
        className
        stack
        cause {
            message
            className
            stack
        }
    }
}

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
                ... on ExecutionStepFailureEvent {
                    runId
                    message
                    timestamp
                    level
                    stepKey
                    eventType
                    error {
                        ...errorFragment
                    }
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


def _filter_events_by_type(events: list[dict], event_type: Optional[str]) -> list[dict]:
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


def _filter_events_by_step(events: list[dict], step_key: Optional[str]) -> list[dict]:
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
    step_key: Optional[str] = None,
) -> dict[str, Any]:
    """Get run events via GraphQL with client-side filtering."""
    variables = {"runId": run_id, "limit": limit}
    if after_cursor:
        variables["afterCursor"] = after_cursor

    result = client.execute(RUN_EVENTS_QUERY, variables)

    logs_result = result.get("logsForRun")
    if not logs_result:
        raise Exception("Empty response from GraphQL API")

    typename = logs_result.get("__typename")

    if typename != "EventConnection":
        error_msg = logs_result.get("message", f"Unknown error: {typename}")
        raise Exception(error_msg)

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
        "hasMore": logs_result.get("hasMore", False),
    }
