"""GraphQL implementation for job operations."""

from typing import TYPE_CHECKING, Any

from dagster_dg_cli.utils.plus.gql_client import IGraphQLClient

if TYPE_CHECKING:
    from dagster_dg_cli.api_layer.schemas.job import DgApiJob, DgApiJobList

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
                jobs {
                    id
                    name
                    description
                    isAssetJob
                    tags {
                        key
                        value
                    }
                    schedules {
                        name
                        cronSchedule
                        scheduleState {
                            status
                        }
                    }
                    sensors {
                        name
                        sensorState {
                            status
                        }
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


def process_repositories_response(graphql_response: dict[str, Any]) -> "DgApiJobList":
    """Process GraphQL response from repositories query into DgApiJobList."""
    from dagster_dg_cli.api_layer.schemas.job import (
        DgApiJob,
        DgApiJobList,
        DgApiJobScheduleSummary,
        DgApiJobSensorSummary,
        DgApiJobTag,
    )

    repositories_result = graphql_response.get("repositoriesOrError")
    if not repositories_result:
        raise Exception("No repositories data in GraphQL response")

    typename = repositories_result.get("__typename")
    if typename != "RepositoryConnection":
        error_msg = repositories_result.get("message", f"GraphQL error: {typename}")
        raise Exception(error_msg)

    repositories_data = repositories_result.get("nodes", [])

    jobs: list[DgApiJob] = []
    for repo in repositories_data:
        repo_name = repo.get("name", "")
        location_name = repo.get("location", {}).get("name", "")
        repository_origin = f"{location_name}@{repo_name}" if location_name and repo_name else None

        for j in repo.get("jobs", []):
            tags = [DgApiJobTag(key=t["key"], value=t["value"]) for t in j.get("tags", [])]
            schedules = [
                DgApiJobScheduleSummary(
                    name=s["name"],
                    cron_schedule=s.get("cronSchedule", ""),
                    status=s.get("scheduleState", {}).get("status", "STOPPED"),
                )
                for s in j.get("schedules", [])
            ]
            sensors = [
                DgApiJobSensorSummary(
                    name=s["name"],
                    status=s.get("sensorState", {}).get("status", "STOPPED"),
                )
                for s in j.get("sensors", [])
            ]

            job = DgApiJob(
                id=j["id"],
                name=j["name"],
                description=j.get("description"),
                is_asset_job=j.get("isAssetJob", False),
                tags=tags,
                schedules=schedules,
                sensors=sensors,
                repository_origin=repository_origin,
            )
            jobs.append(job)

    return DgApiJobList(
        items=jobs,
        total=len(jobs),
    )


def list_jobs_via_graphql(client: IGraphQLClient) -> "DgApiJobList":
    """Fetch jobs using GraphQL."""
    result = client.execute(LIST_REPOSITORIES_QUERY)
    return process_repositories_response(result)


def get_job_by_name_via_graphql(client: IGraphQLClient, job_name: str) -> "DgApiJob":
    """Get job by name, searching across all repositories."""
    result = client.execute(LIST_REPOSITORIES_QUERY)
    all_jobs = process_repositories_response(result)

    matching_jobs = [job for job in all_jobs.items if job.name == job_name]

    if not matching_jobs:
        raise Exception(f"Job not found: {job_name}")

    if len(matching_jobs) > 1:
        repo_origins = [job.repository_origin or "unknown" for job in matching_jobs]
        raise Exception(
            f"Multiple jobs found with name '{job_name}' in repositories: {', '.join(repo_origins)}"
        )

    return matching_jobs[0]
