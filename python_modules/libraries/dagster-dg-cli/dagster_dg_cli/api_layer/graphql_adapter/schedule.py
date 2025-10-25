"""GraphQL implementation for schedule operations."""

from dagster_dg_cli.api_layer.schemas.schedule import DgApiSchedule, DgApiScheduleList
from dagster_dg_cli.utils.plus.gql_client import IGraphQLClient

# GraphQL queries
SCHEDULES_QUERY = """
query Schedules {
    workspaceOrError {
        __typename
        ... on Workspace {
            locationEntries {
                __typename
                ... on WorkspaceLocationEntry {
                    name
                    locationOrLoadError {
                        __typename
                        ... on RepositoryLocation {
                            repositories {
                                name
                                schedules {
                                    id
                                    name
                                    cronSchedule
                                    pipelineName
                                    description
                                    executionTimezone
                                    tags {
                                        key
                                        value
                                    }
                                    metadataEntries {
                                        label
                                        description
                                        ... on TextMetadataEntry {
                                            text
                                        }
                                        ... on UrlMetadataEntry {
                                            url
                                        }
                                        ... on PathMetadataEntry {
                                            path
                                        }
                                        ... on JsonMetadataEntry {
                                            jsonString
                                        }
                                        ... on MarkdownMetadataEntry {
                                            mdStr
                                        }
                                        ... on PythonArtifactMetadataEntry {
                                            module
                                            name
                                        }
                                        ... on FloatMetadataEntry {
                                            floatValue
                                        }
                                        ... on IntMetadataEntry {
                                            intValue
                                        }
                                        ... on BoolMetadataEntry {
                                            boolValue
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        ... on PythonError {
            message
        }
    }
}
"""

SCHEDULE_QUERY = """
query Schedule($scheduleName: String!, $repositoryName: String!, $repositoryLocationName: String!) {
    scheduleOrError(
        scheduleSelector: {
            scheduleName: $scheduleName
            repositoryName: $repositoryName
            repositoryLocationName: $repositoryLocationName
        }
    ) {
        __typename
        ... on Schedule {
            id
            name
            cronSchedule
            pipelineName
            description
            executionTimezone
            tags {
                key
                value
            }
            metadataEntries {
                label
                description
                ... on TextMetadataEntry {
                    text
                }
                ... on UrlMetadataEntry {
                    url
                }
                ... on PathMetadataEntry {
                    path
                }
                ... on JsonMetadataEntry {
                    jsonString
                }
                ... on MarkdownMetadataEntry {
                    mdStr
                }
                ... on PythonArtifactMetadataEntry {
                    module
                    name
                }
                ... on FloatMetadataEntry {
                    floatValue
                }
                ... on IntMetadataEntry {
                    intValue
                }
                ... on BoolMetadataEntry {
                    boolValue
                }
            }
        }
        ... on ScheduleNotFoundError {
            message
        }
        ... on PythonError {
            message
        }
    }
}
"""


def _transform_metadata_entries(metadata_entries):
    """Transform GraphQL metadata entries to dict format."""
    transformed = []
    for entry in metadata_entries:
        metadata_dict = {
            "label": entry.get("label", ""),
            "description": entry.get("description", ""),
        }

        # Add type-specific fields
        for field in [
            "text",
            "url",
            "path",
            "jsonString",
            "mdStr",
            "floatValue",
            "intValue",
            "boolValue",
        ]:
            if field in entry:
                metadata_dict[field] = entry[field]
        if "module" in entry and "name" in entry:
            metadata_dict.update({"module": entry["module"], "name": entry["name"]})

        transformed.append(metadata_dict)
    return transformed


def _transform_tags(tags):
    """Transform GraphQL tags to dict format."""
    return [{"key": tag.get("key", ""), "value": tag.get("value", "")} for tag in tags]


def list_dg_plus_api_schedules_via_graphql(client: IGraphQLClient) -> DgApiScheduleList:
    """List all schedules across all repositories."""
    result = client.execute(SCHEDULES_QUERY)

    workspace_or_error = result.get("workspaceOrError", {})
    if workspace_or_error.get("__typename") == "PythonError":
        raise Exception(f"GraphQL error: {workspace_or_error.get('message', 'Unknown error')}")

    schedules = []
    location_entries = workspace_or_error.get("locationEntries", [])

    for location_entry in location_entries:
        if location_entry.get("__typename") != "WorkspaceLocationEntry":
            continue

        location_or_load_error = location_entry.get("locationOrLoadError", {})
        if location_or_load_error.get("__typename") != "RepositoryLocation":
            continue

        repositories = location_or_load_error.get("repositories", [])

        for repo in repositories:
            repo_schedules = repo.get("schedules", [])

            for schedule_data in repo_schedules:
                schedule = DgApiSchedule(
                    id=schedule_data["id"],
                    name=schedule_data["name"],
                    cron_schedule=schedule_data["cronSchedule"],
                    pipeline_name=schedule_data["pipelineName"],
                    description=schedule_data.get("description"),
                    execution_timezone=schedule_data.get("executionTimezone", "UTC"),
                    tags=_transform_tags(schedule_data.get("tags", [])),
                    metadata_entries=_transform_metadata_entries(
                        schedule_data.get("metadataEntries", [])
                    ),
                )
                schedules.append(schedule)

    return DgApiScheduleList(items=schedules)


def get_dg_plus_api_schedule_via_graphql(
    client: IGraphQLClient, schedule_name: str
) -> DgApiSchedule:
    """Get single schedule by name.

    Note: This is simplified and assumes schedule is in the first repository found.
    For production use, we would need repository/location selection.
    """
    # First, get all schedules to find the one we want
    schedules_list = list_dg_plus_api_schedules_via_graphql(client)

    # Find the schedule by name
    for schedule in schedules_list.items:
        if schedule.name == schedule_name:
            return schedule

    raise Exception(f"Schedule not found: {schedule_name}")
