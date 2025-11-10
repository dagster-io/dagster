"""GraphQL implementation for schedule operations."""

from typing import TYPE_CHECKING, Any, Optional

from dagster_dg_cli.utils.plus.gql_client import IGraphQLClient

if TYPE_CHECKING:
    from dagster_dg_cli.api_layer.schemas.schedule import DgApiSchedule, DgApiScheduleList

LIST_SCHEDULES_QUERY = """
query ListSchedules($repositorySelector: RepositorySelector!) {
    schedulesOrError(repositorySelector: $repositorySelector) {
        __typename
        ... on Schedules {
            results {
                id
                name
                cronSchedule
                pipelineName
                description
                executionTimezone
                scheduleState {
                    status
                }
            }
        }
        ... on RepositoryNotFoundError {
            message
        }
        ... on PythonError {
            message
            stack
        }
    }
}
"""

LIST_REPOSITORIES_QUERY = """
query ListRepositories {
    repositoriesOrError {
        __typename
        ... on RepositoryConnection {
            nodes {
                name
                location {
                    name
                }
                schedules {
                    id
                    name
                    cronSchedule
                    pipelineName
                    description
                    executionTimezone
                    scheduleState {
                        status
                    }
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

GET_SCHEDULE_QUERY = """
query GetSchedule($scheduleSelector: ScheduleSelector!) {
    scheduleOrError(scheduleSelector: $scheduleSelector) {
        __typename
        ... on Schedule {
            id
            name
            cronSchedule
            pipelineName
            description
            executionTimezone
            scheduleState {
                status
            }
        }
        ... on ScheduleNotFoundError {
            message
        }
        ... on PythonError {
            message
            stack
        }
    }
}
"""


def process_repositories_response(graphql_response: dict[str, Any]) -> "DgApiScheduleList":
    """Process GraphQL response from repositories query into DgApiScheduleList."""
    from dagster_dg_cli.api_layer.schemas.schedule import (
        DgApiSchedule,
        DgApiScheduleList,
        DgApiScheduleStatus,
    )

    repositories_result = graphql_response.get("repositoriesOrError")
    if not repositories_result:
        raise Exception("No repositories data in GraphQL response")

    typename = repositories_result.get("__typename")
    if typename != "RepositoryConnection":
        error_msg = repositories_result.get("message", f"GraphQL error: {typename}")
        raise Exception(error_msg)

    repositories_data = repositories_result.get("nodes", [])

    schedules = []
    for repo in repositories_data:
        repo_name = repo.get("name", "")
        location_name = repo.get("location", {}).get("name", "")
        code_location_origin = (
            f"{location_name}@{repo_name}" if location_name and repo_name else None
        )

        for s in repo.get("schedules", []):
            schedule_state = s.get("scheduleState", {})
            status = schedule_state.get("status", "STOPPED")

            schedule = DgApiSchedule(
                id=s["id"],
                name=s["name"],
                status=DgApiScheduleStatus(status),
                cron_schedule=s.get("cronSchedule", ""),
                pipeline_name=s.get("pipelineName", ""),
                description=s.get("description"),
                execution_timezone=s.get("executionTimezone"),
                code_location_origin=code_location_origin,
                next_tick_timestamp=None,
            )
            schedules.append(schedule)

    return DgApiScheduleList(
        items=schedules,
        total=len(schedules),
    )


def process_schedules_response(graphql_response: dict[str, Any]) -> "DgApiScheduleList":
    """Process GraphQL response into DgApiScheduleList.

    Args:
        graphql_response: Raw GraphQL response containing "schedulesOrError"

    Returns:
        DgApiScheduleList: Processed schedule data
    """
    from dagster_dg_cli.api_layer.schemas.schedule import (
        DgApiSchedule,
        DgApiScheduleList,
        DgApiScheduleStatus,
    )

    schedules_result = graphql_response.get("schedulesOrError")
    if not schedules_result:
        raise Exception("No schedules data in GraphQL response")

    typename = schedules_result.get("__typename")
    if typename != "Schedules":
        error_msg = schedules_result.get("message", f"GraphQL error: {typename}")
        raise Exception(error_msg)

    schedules_data = schedules_result.get("results", [])

    schedules = []
    for s in schedules_data:
        schedule_state = s.get("scheduleState", {})
        status = schedule_state.get("status", "STOPPED")

        schedule = DgApiSchedule(
            id=s["id"],
            name=s["name"],
            status=DgApiScheduleStatus(status),
            cron_schedule=s.get("cronSchedule", ""),
            pipeline_name=s.get("pipelineName", ""),
            description=s.get("description"),
            execution_timezone=s.get("executionTimezone"),
            code_location_origin=None,
            next_tick_timestamp=None,
        )
        schedules.append(schedule)

    return DgApiScheduleList(
        items=schedules,
        total=len(schedules),
    )


def process_schedule_response(graphql_response: dict[str, Any]) -> "DgApiSchedule":
    """Process GraphQL response into DgApiSchedule.

    Args:
        graphql_response: Raw GraphQL response containing "scheduleOrError"

    Returns:
        DgApiSchedule: Processed schedule data
    """
    from dagster_dg_cli.api_layer.schemas.schedule import DgApiSchedule, DgApiScheduleStatus

    schedule_result = graphql_response.get("scheduleOrError")
    if not schedule_result:
        raise Exception("No schedule data in GraphQL response")

    typename = schedule_result.get("__typename")
    if typename != "Schedule":
        error_msg = schedule_result.get("message", f"GraphQL error: {typename}")
        raise Exception(error_msg)

    schedule_state = schedule_result.get("scheduleState", {})
    status = schedule_state.get("status", "STOPPED")

    return DgApiSchedule(
        id=schedule_result["id"],
        name=schedule_result["name"],
        status=DgApiScheduleStatus(status),
        cron_schedule=schedule_result.get("cronSchedule", ""),
        pipeline_name=schedule_result.get("pipelineName", ""),
        description=schedule_result.get("description"),
        execution_timezone=schedule_result.get("executionTimezone"),
        code_location_origin=None,
        next_tick_timestamp=None,
    )


def list_schedules_via_graphql(
    client: IGraphQLClient,
    repository_location_name: Optional[str] = None,
    repository_name: Optional[str] = None,
) -> "DgApiScheduleList":
    """Fetch schedules using GraphQL."""
    if repository_location_name and repository_name:
        variables = {
            "repositorySelector": {
                "repositoryLocationName": repository_location_name,
                "repositoryName": repository_name,
            }
        }
        result = client.execute(LIST_SCHEDULES_QUERY, variables)
        return process_schedules_response(result)
    else:
        result = client.execute(LIST_REPOSITORIES_QUERY)
        return process_repositories_response(result)


def get_schedule_via_graphql(
    client: IGraphQLClient,
    schedule_name: str,
    repository_location_name: str,
    repository_name: str,
) -> "DgApiSchedule":
    """Get single schedule via GraphQL."""
    variables = {
        "scheduleSelector": {
            "scheduleName": schedule_name,
            "repositoryLocationName": repository_location_name,
            "repositoryName": repository_name,
        }
    }

    try:
        result = client.execute(GET_SCHEDULE_QUERY, variables)
        if (
            result.get("data", {}).get("scheduleOrError", {}).get("__typename")
            == "ScheduleNotFoundError"
        ):
            raise Exception(f"Schedule not found: {schedule_name}")
        return process_schedule_response(result)
    except Exception:
        raise


def get_schedule_by_name_via_graphql(client: IGraphQLClient, schedule_name: str) -> "DgApiSchedule":
    """Get schedule by name, searching across all code locations."""
    result = client.execute(LIST_REPOSITORIES_QUERY)
    all_schedules = process_repositories_response(result)

    matching_schedules = [
        schedule for schedule in all_schedules.items if schedule.name == schedule_name
    ]

    if not matching_schedules:
        raise Exception(f"Schedule not found: {schedule_name}")

    if len(matching_schedules) > 1:
        code_location_origins = [
            schedule.code_location_origin or "unknown" for schedule in matching_schedules
        ]
        raise Exception(
            f"Multiple schedules found with name '{schedule_name}' in code locations: {', '.join(code_location_origins)}"
        )

    return matching_schedules[0]
