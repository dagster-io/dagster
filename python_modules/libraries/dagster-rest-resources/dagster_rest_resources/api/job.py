from dataclasses import dataclass

from typing_extensions import assert_never

from dagster_rest_resources.gql_client import IGraphQLClient
from dagster_rest_resources.schemas.exception import DagsterPlusGraphqlError
from dagster_rest_resources.schemas.job import (
    DgApiJob,
    DgApiJobList,
    DgApiJobScheduleSummary,
    DgApiJobSensorSummary,
    DgApiJobTag,
)


@dataclass(frozen=True)
class DgApiJobApi:
    _client: IGraphQLClient

    def list_jobs(self) -> DgApiJobList:
        result = self._client.list_repositories().repositories_or_error

        match result.typename__:
            case "RepositoryConnection":
                jobs: list[DgApiJob] = []
                for repo in result.nodes:  # ty: ignore[unresolved-attribute]
                    location_name = repo.location.name
                    repo_name = repo.name
                    repository_origin = (
                        f"{location_name}@{repo_name}" if location_name and repo_name else None
                    )
                    for j in repo.jobs:
                        jobs.append(
                            DgApiJob(
                                id=j.id,
                                name=j.name,
                                description=j.description,
                                is_asset_job=j.is_asset_job,
                                tags=[DgApiJobTag(key=t.key, value=t.value) for t in j.tags],
                                schedules=[
                                    DgApiJobScheduleSummary(
                                        name=s.name,
                                        cron_schedule=s.cron_schedule or "",
                                        status=s.schedule_state.status,
                                    )
                                    for s in j.schedules
                                ],
                                sensors=[
                                    DgApiJobSensorSummary(
                                        name=s.name,
                                        status=s.sensor_state.status,
                                    )
                                    for s in j.sensors
                                ],
                                repository_origin=repository_origin,
                            )
                        )
                return DgApiJobList(items=jobs, total=len(jobs))
            case "RepositoryNotFoundError":
                raise DagsterPlusGraphqlError(f"Repository not found: {result.message}")  # ty: ignore[unresolved-attribute]
            case "PythonError":
                raise DagsterPlusGraphqlError(f"Error fetching jobs: {result.message}")  # ty: ignore[unresolved-attribute]
            case _ as unreachable:
                assert_never(unreachable)

    def get_job_by_name(self, job_name: str) -> "DgApiJob":
        all_jobs = self.list_jobs()
        matching_jobs = [job for job in all_jobs.items if job.name == job_name]

        if not matching_jobs:
            raise DagsterPlusGraphqlError(f"Job not found: {job_name}")

        if len(matching_jobs) > 1:
            repo_origins = [job.repository_origin or "unknown" for job in matching_jobs]
            raise DagsterPlusGraphqlError(
                f"Multiple jobs found with name '{job_name}' in repositories: {', '.join(repo_origins)}"
            )

        return matching_jobs[0]
