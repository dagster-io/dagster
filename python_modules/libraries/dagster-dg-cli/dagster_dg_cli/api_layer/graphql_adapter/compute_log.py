"""GraphQL adapter for compute logs."""

from typing import Any

from dagster_dg_cli.utils.plus.gql_client import IGraphQLClient

# Query to find LogsCapturedEvent entries for a run
LOGS_CAPTURED_EVENTS_QUERY = """
query CliLogsCapturedEventsQuery($runId: ID!, $limit: Int, $afterCursor: String) {
    logsForRun(runId: $runId, limit: $limit, afterCursor: $afterCursor) {
        __typename
        ... on EventConnection {
            events {
                __typename
                ... on LogsCapturedEvent {
                    fileKey
                    stepKeys
                    externalStdoutUrl
                    externalStderrUrl
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

# Query to fetch actual log content for a log key
CAPTURED_LOGS_QUERY = """
query CliCapturedLogsQuery($logKey: [String!]!, $cursor: String, $limit: Int) {
    capturedLogs(logKey: $logKey, cursor: $cursor, limit: $limit) {
        stdout
        stderr
        cursor
    }
}
"""

# Query to fetch download URLs for a log key
CAPTURED_LOGS_METADATA_QUERY = """
query CliCapturedLogsMetadataQuery($logKey: [String!]!) {
    capturedLogsMetadata(logKey: $logKey) {
        stdoutDownloadUrl
        stderrDownloadUrl
    }
}
"""

_MAX_PAGES = 100


def get_logs_captured_events(
    client: IGraphQLClient,
    run_id: str,
    step_key: str | None = None,
) -> list[dict[str, Any]]:
    """Get LogsCapturedEvent entries for a run, auto-paginating through all events.

    Returns a list of dicts with keys: fileKey, stepKeys, externalStdoutUrl, externalStderrUrl.
    """
    collected: list[dict[str, Any]] = []
    cursor: str | None = None
    server_has_more = True

    for _ in range(_MAX_PAGES):
        if not server_has_more:
            break

        variables: dict[str, Any] = {"runId": run_id, "limit": 100}
        if cursor:
            variables["afterCursor"] = cursor

        result = client.execute(LOGS_CAPTURED_EVENTS_QUERY, variables)
        logs_result = result.get("logsForRun")
        if not logs_result:
            raise Exception("Empty response from GraphQL API")

        typename = logs_result.get("__typename")
        if typename != "EventConnection":
            error_msg = logs_result.get("message", f"Unknown error: {typename}")
            raise Exception(error_msg)

        for event in logs_result.get("events", []):
            if event.get("__typename") != "LogsCapturedEvent":
                continue
            if not event.get("fileKey"):
                continue
            if step_key and step_key not in (event.get("stepKeys") or []):
                continue
            collected.append(event)

        new_cursor = logs_result.get("cursor")
        server_has_more = logs_result.get("hasMore", False)

        if server_has_more and not new_cursor:
            break

        cursor = new_cursor

    return collected


def get_captured_log_content(
    client: IGraphQLClient,
    log_key: list[str],
    cursor: str | None = None,
    max_bytes: int | None = None,
) -> dict[str, Any]:
    """Fetch captured log content for a log key.

    Returns dict with keys: stdout, stderr, cursor.
    """
    variables: dict[str, Any] = {"logKey": log_key}
    if cursor:
        variables["cursor"] = cursor
    if max_bytes is not None:
        variables["limit"] = max_bytes

    result = client.execute(CAPTURED_LOGS_QUERY, variables)
    captured = result.get("capturedLogs")
    if not captured:
        return {"stdout": None, "stderr": None, "cursor": None}

    return {
        "stdout": captured.get("stdout"),
        "stderr": captured.get("stderr"),
        "cursor": captured.get("cursor"),
    }


def get_captured_log_metadata(
    client: IGraphQLClient,
    log_key: list[str],
) -> dict[str, Any]:
    """Fetch download URLs for a log key.

    Returns dict with keys: stdoutDownloadUrl, stderrDownloadUrl.
    """
    result = client.execute(CAPTURED_LOGS_METADATA_QUERY, {"logKey": log_key})
    metadata = result.get("capturedLogsMetadata")
    if not metadata:
        return {"stdoutDownloadUrl": None, "stderrDownloadUrl": None}

    return {
        "stdoutDownloadUrl": metadata.get("stdoutDownloadUrl"),
        "stderrDownloadUrl": metadata.get("stderrDownloadUrl"),
    }
