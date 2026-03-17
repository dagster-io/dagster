"""GraphQL adapter for instigation ticks (sensors and schedules)."""

from typing import TYPE_CHECKING, Any

from dagster_dg_cli.utils.plus.gql_client import IGraphQLClient

if TYPE_CHECKING:
    from dagster_dg_cli.api_layer.schemas.tick import DgApiTickList

# Error fragment shared by tick queries
_ERROR_FRAGMENT = """
fragment errorFragment on PythonError {
    message
    stack
}
"""

SENSOR_TICKS_QUERY = (
    _ERROR_FRAGMENT
    + """
query CliSensorTicksQuery(
    $sensorSelector: SensorSelector!,
    $limit: Int,
    $cursor: String,
    $statuses: [InstigationTickStatus!],
    $beforeTimestamp: Float,
    $afterTimestamp: Float
) {
    sensorOrError(sensorSelector: $sensorSelector) {
        __typename
        ... on Sensor {
            name
            sensorState {
                ticks(
                    limit: $limit
                    cursor: $cursor
                    statuses: $statuses
                    beforeTimestamp: $beforeTimestamp
                    afterTimestamp: $afterTimestamp
                ) {
                    id
                    status
                    timestamp
                    endTimestamp
                    runIds
                    skipReason
                    cursor
                    error {
                        ...errorFragment
                    }
                }
            }
        }
        ... on SensorNotFoundError {
            message
        }
        ... on PythonError {
            ...errorFragment
        }
    }
}
"""
)

SCHEDULE_TICKS_QUERY = (
    _ERROR_FRAGMENT
    + """
query CliScheduleTicksQuery(
    $scheduleSelector: ScheduleSelector!,
    $limit: Int,
    $cursor: String,
    $statuses: [InstigationTickStatus!],
    $beforeTimestamp: Float,
    $afterTimestamp: Float
) {
    scheduleOrError(scheduleSelector: $scheduleSelector) {
        __typename
        ... on Schedule {
            name
            scheduleState {
                ticks(
                    limit: $limit
                    cursor: $cursor
                    statuses: $statuses
                    beforeTimestamp: $beforeTimestamp
                    afterTimestamp: $afterTimestamp
                ) {
                    id
                    status
                    timestamp
                    endTimestamp
                    runIds
                    skipReason
                    cursor
                    error {
                        ...errorFragment
                    }
                }
            }
        }
        ... on ScheduleNotFoundError {
            message
        }
        ... on PythonError {
            ...errorFragment
        }
    }
}
"""
)

# Query to list repositories so we can find the selector for a sensor/schedule by name
_LIST_REPOSITORIES_QUERY = """
query ListRepositories {
    repositoriesOrError {
        __typename
        ... on RepositoryConnection {
            nodes {
                name
                location {
                    name
                }
                sensors {
                    name
                }
                schedules {
                    name
                }
            }
        }
        ... on PythonError {
            message
            stack
        }
    }
}
"""


def _find_selector_for_name(
    client: IGraphQLClient,
    name: str,
    entity_type: str,
) -> dict[str, str]:
    """Find the repository selector for a sensor or schedule by name.

    Returns a dict with repositoryLocationName, repositoryName, and the entity name key.
    """
    result = client.execute(_LIST_REPOSITORIES_QUERY)
    repos_result = result.get("repositoriesOrError")
    if not repos_result:
        raise Exception("Empty response from GraphQL API")

    typename = repos_result.get("__typename")
    if typename != "RepositoryConnection":
        error_msg = repos_result.get("message", f"GraphQL error: {typename}")
        raise Exception(error_msg)

    matches: list[dict[str, str]] = []
    for repo in repos_result.get("nodes", []):
        repo_name = repo.get("name", "")
        location_name = repo.get("location", {}).get("name", "")
        entities = repo.get(f"{entity_type}s", [])

        for entity in entities:
            if entity.get("name") == name:
                matches.append(
                    {
                        "repositoryLocationName": location_name,
                        "repositoryName": repo_name,
                        f"{entity_type}Name": name,
                    }
                )

    if not matches:
        raise Exception(f"{entity_type.capitalize()} not found: {name}")

    if len(matches) > 1:
        origins = [f"{m['repositoryLocationName']}@{m['repositoryName']}" for m in matches]
        raise Exception(
            f"Multiple {entity_type}s found with name '{name}' in repositories: {', '.join(origins)}"
        )

    return matches[0]


def _process_ticks_response(ticks_data: list[dict[str, Any]]) -> "DgApiTickList":
    """Convert raw tick dicts to DgApiTickList."""
    from dagster_dg_cli.api_layer.schemas.tick import (
        DgApiTick,
        DgApiTickError,
        DgApiTickList,
        DgApiTickStatus,
    )

    items: list[DgApiTick] = []
    for t in ticks_data:
        error_data = t.get("error")
        error = None
        if error_data:
            error = DgApiTickError(
                message=error_data.get("message", ""),
                stack=error_data.get("stack"),
            )

        items.append(
            DgApiTick(
                id=t["id"],
                status=DgApiTickStatus(t["status"]),
                timestamp=t["timestamp"],
                end_timestamp=t.get("endTimestamp"),
                run_ids=t.get("runIds", []),
                error=error,
                skip_reason=t.get("skipReason"),
                cursor=t.get("cursor"),
            )
        )

    # Use the last tick's ID as cursor for pagination
    cursor = items[-1].id if items else None

    return DgApiTickList(items=items, total=len(items), cursor=cursor)


def get_sensor_ticks_via_graphql(
    client: IGraphQLClient,
    *,
    sensor_name: str,
    limit: int = 25,
    cursor: str | None = None,
    statuses: tuple[str, ...] = (),
    before_timestamp: float | None = None,
    after_timestamp: float | None = None,
) -> "DgApiTickList":
    """Fetch ticks for a sensor by name."""
    selector = _find_selector_for_name(client, sensor_name, "sensor")

    variables: dict[str, Any] = {
        "sensorSelector": selector,
        "limit": limit,
    }
    if cursor:
        variables["cursor"] = cursor
    if statuses:
        variables["statuses"] = list(statuses)
    if before_timestamp is not None:
        variables["beforeTimestamp"] = before_timestamp
    if after_timestamp is not None:
        variables["afterTimestamp"] = after_timestamp

    result = client.execute(SENSOR_TICKS_QUERY, variables)
    sensor_result = result.get("sensorOrError")
    if not sensor_result:
        raise Exception("Empty response from GraphQL API")

    typename = sensor_result.get("__typename")
    if typename != "Sensor":
        error_msg = sensor_result.get("message", f"GraphQL error: {typename}")
        raise Exception(error_msg)

    ticks_data = sensor_result.get("sensorState", {}).get("ticks", [])
    return _process_ticks_response(ticks_data)


def get_schedule_ticks_via_graphql(
    client: IGraphQLClient,
    *,
    schedule_name: str,
    limit: int = 25,
    cursor: str | None = None,
    statuses: tuple[str, ...] = (),
    before_timestamp: float | None = None,
    after_timestamp: float | None = None,
) -> "DgApiTickList":
    """Fetch ticks for a schedule by name."""
    selector = _find_selector_for_name(client, schedule_name, "schedule")

    variables: dict[str, Any] = {
        "scheduleSelector": selector,
        "limit": limit,
    }
    if cursor:
        variables["cursor"] = cursor
    if statuses:
        variables["statuses"] = list(statuses)
    if before_timestamp is not None:
        variables["beforeTimestamp"] = before_timestamp
    if after_timestamp is not None:
        variables["afterTimestamp"] = after_timestamp

    result = client.execute(SCHEDULE_TICKS_QUERY, variables)
    schedule_result = result.get("scheduleOrError")
    if not schedule_result:
        raise Exception("Empty response from GraphQL API")

    typename = schedule_result.get("__typename")
    if typename != "Schedule":
        error_msg = schedule_result.get("message", f"GraphQL error: {typename}")
        raise Exception(error_msg)

    ticks_data = schedule_result.get("scheduleState", {}).get("ticks", [])
    return _process_ticks_response(ticks_data)
