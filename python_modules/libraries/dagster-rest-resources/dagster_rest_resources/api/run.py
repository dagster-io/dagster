from dataclasses import dataclass

from typing_extensions import assert_never

from dagster_rest_resources.__generated__.enums import RunStatus
from dagster_rest_resources.__generated__.input_types import RunsFilter
from dagster_rest_resources.gql_client import IGraphQLClient
from dagster_rest_resources.schemas.exception import DagsterPlusGraphqlError
from dagster_rest_resources.schemas.run import DgApiRun, DgApiRunList


@dataclass(frozen=True)
class DgApiRunApi:
    _client: IGraphQLClient

    def get_run(self, run_id: str) -> DgApiRun:
        result = self._client.get_run(run_id=run_id).run_or_error

        match result.typename__:
            case "Run":
                return DgApiRun(
                    id=result.run_id,  # ty: ignore[unresolved-attribute]
                    status=result.status,  # ty: ignore[unresolved-attribute]
                    created_at=result.creation_time,  # ty: ignore[unresolved-attribute]
                    started_at=result.start_time,  # ty: ignore[unresolved-attribute]
                    ended_at=result.end_time,  # ty: ignore[unresolved-attribute]
                    job_name=result.job_name,  # ty: ignore[unresolved-attribute]
                )
            case "RunNotFoundError":
                raise DagsterPlusGraphqlError(f"Run not found: {result.message}")  # ty: ignore[unresolved-attribute]
            case "PythonError":
                raise DagsterPlusGraphqlError(f"Error fetching run: {result.message}")  # ty: ignore[unresolved-attribute]
            case _ as unreachable:
                assert_never(unreachable)

    def list_runs(
        self,
        limit: int = 50,
        cursor: str | None = None,
        statuses: list[RunStatus] | None = None,
        job_name: str | None = None,
    ) -> DgApiRunList:
        run_filter = None
        if statuses or job_name:
            run_filter = RunsFilter(
                statuses=statuses if statuses else None,
                pipelineName=job_name if job_name else None,
            )

        result = self._client.list_runs(filter=run_filter, cursor=cursor, limit=limit).runs_or_error

        match result.typename__:
            case "Runs":
                return DgApiRunList(
                    items=[
                        DgApiRun(
                            id=r.run_id,
                            status=r.status,
                            created_at=r.creation_time,
                            started_at=r.start_time,
                            ended_at=r.end_time,
                            job_name=r.job_name,
                        )
                        for r in result.results  # ty: ignore[unresolved-attribute]
                    ],
                    total=result.count,  # ty: ignore[unresolved-attribute]
                )
            case "InvalidPipelineRunsFilterError":
                raise DagsterPlusGraphqlError(
                    f"Invalid runs filter:\n  statuses: {', '.join(statuses or [])}\n  job_name: {job_name}"
                )
            case "PythonError":
                raise DagsterPlusGraphqlError(f"Error fetching runs: {result.message}")  # ty: ignore[unresolved-attribute]
            case _ as unreachable:
                assert_never(unreachable)
