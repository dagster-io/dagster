"""GraphQL adapter for run events."""

from collections.abc import Sequence
from typing import Any

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


def _filter_events_by_type(events: list[dict], event_types: Sequence[str]) -> list[dict]:
    """Client-side filtering logic for event types."""
    if not event_types:
        return events

    types_upper = {t.upper() for t in event_types}

    return [event for event in events if (event.get("eventType") or "").upper() in types_upper]


def _filter_events_by_step(events: list[dict], step_keys: Sequence[str]) -> list[dict]:
    """Client-side filtering logic for step keys (partial matching)."""
    if not step_keys:
        return events

    keys_lower = [k.lower() for k in step_keys]

    return [
        event
        for event in events
        if event.get("stepKey") and any(k in event["stepKey"].lower() for k in keys_lower)
    ]


def _filter_events_by_level(events: list[dict], levels: Sequence[str]) -> list[dict]:
    """Client-side filtering logic for log levels."""
    if not levels:
        return events

    levels_upper = {level.upper() for level in levels}

    return [event for event in events if (event.get("level") or "").upper() in levels_upper]


def _apply_client_filters(
    events: list[dict],
    event_types: Sequence[str],
    levels: Sequence[str],
    step_keys: Sequence[str],
) -> list[dict]:
    """Apply all client-side filters to a list of events."""
    if event_types:
        events = _filter_events_by_type(events, event_types)
    if levels:
        events = _filter_events_by_level(events, levels)
    if step_keys:
        events = _filter_events_by_step(events, step_keys)
    return events


_MAX_PAGES = 100


def get_run_events_via_graphql(
    client: IGraphQLClient,
    run_id: str,
    limit: int = 100,
    after_cursor: str | None = None,
    event_types: Sequence[str] = (),
    step_keys: Sequence[str] = (),
    levels: Sequence[str] = (),
) -> dict[str, Any]:
    """Get run events via GraphQL with client-side filtering.

    When client-side filters are active, auto-paginates to collect up to
    ``limit`` matching events, since any single server page may yield fewer
    matches after filtering.
    """
    has_client_filters = bool(event_types or levels or step_keys)

    if not has_client_filters:
        # Fast path: no client-side filters, single page fetch
        variables: dict[str, Any] = {"runId": run_id, "limit": limit}
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

        return {
            "events": logs_result.get("events", []),
            "cursor": logs_result.get("cursor"),
            "hasMore": logs_result.get("hasMore", False),
        }

    # Auto-paginate when client-side filters are active
    collected: list[dict] = []
    cursor = after_cursor
    server_has_more = True

    for _ in range(_MAX_PAGES):
        if not server_has_more:
            break

        variables = {"runId": run_id, "limit": limit}
        if cursor:
            variables["afterCursor"] = cursor

        result = client.execute(RUN_EVENTS_QUERY, variables)
        logs_result = result.get("logsForRun")
        if not logs_result:
            raise Exception("Empty response from GraphQL API")

        typename = logs_result.get("__typename")
        if typename != "EventConnection":
            error_msg = logs_result.get("message", f"Unknown error: {typename}")
            raise Exception(error_msg)

        page_events = logs_result.get("events", [])
        filtered = _apply_client_filters(page_events, event_types, levels, step_keys)
        collected.extend(filtered)

        cursor = logs_result.get("cursor")
        server_has_more = logs_result.get("hasMore", False)

        if len(collected) >= limit:
            collected = collected[:limit]
            break

    return {
        "events": collected,
        "cursor": cursor,
        "hasMore": server_has_more and len(collected) >= limit,
    }
