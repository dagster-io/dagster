from dataclasses import dataclass

from typing_extensions import assert_never

from dagster_rest_resources.__generated__.enums import RunStatus
from dagster_rest_resources.__generated__.input_types import (
    AssetKeyInput,
    ExecutionMetadata,
    ExecutionParams,
    ExecutionTag,
    JobOrPipelineSelector,
    RunsFilter,
)
from dagster_rest_resources.gql_client import IGraphQLClient
from dagster_rest_resources.schemas.exception import DagsterPlusGraphqlError
from dagster_rest_resources.schemas.run import DgApiRun, DgApiRunLaunchResult, DgApiRunList

PARTITION_TAG = "dagster/partition"


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

    def create_run(
        self,
        *,
        location_name: str,
        repository_name: str,
        job_name: str | None,
        asset_keys: list[str] | None,
        tags: dict[str, str] | None,
        run_config: dict | None,
        partition: str | None,
    ) -> DgApiRunLaunchResult:
        if not job_name and not asset_keys:
            raise DagsterPlusGraphqlError(
                "At least one of `job_name` or `asset_keys` must be provided."
            )

        execution_tags: list[ExecutionTag] = []
        if tags:
            execution_tags.extend(ExecutionTag(key=k, value=v) for k, v in tags.items())
        if partition:
            execution_tags.append(ExecutionTag(key=PARTITION_TAG, value=partition))

        selector = JobOrPipelineSelector(
            repositoryLocationName=location_name,
            repositoryName=repository_name,
            jobName=job_name,
            assetSelection=(
                [AssetKeyInput(path=key.split("/")) for key in asset_keys] if asset_keys else None
            ),
        )

        params = ExecutionParams(
            selector=selector,
            runConfigData=run_config,
            executionMetadata=(ExecutionMetadata(tags=execution_tags) if execution_tags else None),
        )

        result = self._client.launch_run(execution_params=params).launch_run

        match result.typename__:
            case "LaunchRunSuccess":
                return DgApiRunLaunchResult(
                    run_id=result.run.run_id,  # ty: ignore[unresolved-attribute]
                    status=result.run.status,  # ty: ignore[unresolved-attribute]
                )
            case "RunConfigValidationInvalid":
                joined = "\n  ".join(e.message for e in result.errors)  # ty: ignore[unresolved-attribute]
                raise DagsterPlusGraphqlError(f"Invalid run config:\n  {joined}")
            case "PipelineNotFoundError":
                raise DagsterPlusGraphqlError(f"Job not found: {result.message}")  # ty: ignore[unresolved-attribute]
            case "InvalidStepError":
                raise DagsterPlusGraphqlError(
                    f"Invalid step key: {result.invalid_step_key}"  # ty: ignore[unresolved-attribute]
                )
            case "InvalidOutputError":
                raise DagsterPlusGraphqlError(
                    f"Invalid output `{result.invalid_output_name}` on step `{result.step_key}`"  # ty: ignore[unresolved-attribute]
                )
            case "InvalidSubsetError":
                raise DagsterPlusGraphqlError(f"Invalid subset: {result.message}")  # ty: ignore[unresolved-attribute]
            case "PresetNotFoundError":
                raise DagsterPlusGraphqlError(f"Preset not found: {result.message}")  # ty: ignore[unresolved-attribute]
            case "ConflictingExecutionParamsError":
                raise DagsterPlusGraphqlError(
                    f"Conflicting execution params: {result.message}"  # ty: ignore[unresolved-attribute]
                )
            case "NoModeProvidedError":
                raise DagsterPlusGraphqlError(f"No mode provided: {result.message}")  # ty: ignore[unresolved-attribute]
            case "RunConflict":
                raise DagsterPlusGraphqlError(f"Run conflict: {result.message}")  # ty: ignore[unresolved-attribute]
            case "UnauthorizedError":
                raise DagsterPlusGraphqlError(f"Unauthorized: {result.message}")  # ty: ignore[unresolved-attribute]
            case "PythonError":
                raise DagsterPlusGraphqlError(f"Error launching run: {result.message}")  # ty: ignore[unresolved-attribute]
            case _ as unreachable:
                assert_never(unreachable)
