from dataclasses import dataclass
from typing import Any

from typing_extensions import assert_never

from dagster_rest_resources.__generated__.enums import ReexecutionStrategy, RunStatus
from dagster_rest_resources.__generated__.input_types import (
    AssetKeyInput,
    ExecutionMetadata,
    ExecutionParams,
    ExecutionTag,
    JobOrPipelineSelector,
    ReexecutionParams,
    RunsFilter,
)
from dagster_rest_resources.gql_client import IGraphQLClient
from dagster_rest_resources.schemas.exception import DagsterPlusGraphqlError
from dagster_rest_resources.schemas.run import (
    DgApiBackfillReexecuteResult,
    DgApiRun,
    DgApiRunLaunchResult,
    DgApiRunList,
    DgApiRunReexecuteResult,
    DgApiRunStats,
    DgApiRunTag,
    DgApiRunTerminateResult,
)

PARTITION_TAG = "dagster/partition"

# Launching an ad hoc selection of assets means launching the implicit asset job with an
# asset selection. Defined here rather than imported so the library does not depend on
# dagster itself; the source of truth is
# dagster._core.definitions.assets.job.asset_job.IMPLICIT_ASSET_JOB_NAME.
IMPLICIT_ASSET_JOB_NAME = "__ASSET_JOB"


def _reexecution_params(
    *,
    parent_run_id: str,
    strategy: ReexecutionStrategy,
    use_parent_run_tags: bool | None,
    extra_tags: dict[str, str] | None,
) -> ReexecutionParams:
    return ReexecutionParams(
        parentRunId=parent_run_id,
        strategy=strategy,
        useParentRunTags=use_parent_run_tags,
        extraTags=(
            [ExecutionTag(key=k, value=v) for k, v in extra_tags.items()] if extra_tags else None
        ),
    )


def _reexecution_error(result: Any) -> str:
    """Describe a re-execution failure.

    Both mutations can fail as any of a dozen union members, most carrying a message and a
    few carrying only a step or output name, so this reports whichever is present.
    """
    for attr in ("message", "invalid_step_key", "invalid_output_name", "preset"):
        value = getattr(result, attr, None)
        if value:
            return f"{result.typename__}: {value}"
    errors = getattr(result, "errors", None)
    if errors:
        return f"{result.typename__}: " + "; ".join(e.message for e in errors)
    return str(result.typename__)


@dataclass(frozen=True)
class DgApiRunApi:
    _client: IGraphQLClient

    def get_run(self, run_id: str) -> DgApiRun:
        result = self._client.get_run(run_id=run_id).run_or_error

        match result.typename__:
            case "Run":
                stats = None
                if result.stats.typename__ == "RunStatsSnapshot":  # ty: ignore[unresolved-attribute]
                    stats = DgApiRunStats(
                        steps_succeeded=result.stats.steps_succeeded,  # ty: ignore[unresolved-attribute]
                        steps_failed=result.stats.steps_failed,  # ty: ignore[unresolved-attribute]
                        materializations=result.stats.materializations,  # ty: ignore[unresolved-attribute]
                        expectations=result.stats.expectations,  # ty: ignore[unresolved-attribute]
                    )
                return DgApiRun(
                    id=result.run_id,  # ty: ignore[unresolved-attribute]
                    status=result.status,  # ty: ignore[unresolved-attribute]
                    created_at=result.creation_time,  # ty: ignore[unresolved-attribute]
                    started_at=result.start_time,  # ty: ignore[unresolved-attribute]
                    ended_at=result.end_time,  # ty: ignore[unresolved-attribute]
                    job_name=result.job_name,  # ty: ignore[unresolved-attribute]
                    tags=[DgApiRunTag(key=t.key, value=t.value) for t in result.tags],  # ty: ignore[unresolved-attribute]
                    run_config_yaml=result.run_config_yaml,  # ty: ignore[unresolved-attribute]
                    stats=stats,
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
                            tags=[DgApiRunTag(key=t.key, value=t.value) for t in r.tags],
                        )
                        for r in result.results  # ty: ignore[unresolved-attribute]
                    ],
                    total=result.count,  # ty: ignore[unresolved-attribute]
                )
            case "InvalidPipelineRunsFilterError":
                raise DagsterPlusGraphqlError(f"Invalid runs filter: {result.message}")  # ty: ignore[unresolved-attribute]
            case "PythonError":
                raise DagsterPlusGraphqlError(f"Error fetching runs: {result.message}")  # ty: ignore[unresolved-attribute]
            case _ as unreachable:
                assert_never(unreachable)

    def create_run(
        self,
        *,
        location_name: str,
        repository_name: str,
        job_name: str,
        asset_keys: list[list[str]] | None = None,
        tags: dict[str, str] | None = None,
        run_config: dict | None = None,
        partition: str | None = None,
    ) -> DgApiRunLaunchResult:
        """Launch a run of a job, optionally narrowed to a subset of its assets.

        Asset keys are path components, as `[["marts", "dim_customers"]]`, because a single
        component may itself contain a slash and a joined form cannot be split back
        unambiguously.
        """
        return self._launch(
            location_name=location_name,
            repository_name=repository_name,
            job_name=job_name,
            asset_keys=asset_keys,
            tags=tags,
            run_config=run_config,
            partition=partition,
        )

    def create_asset_run(
        self,
        *,
        location_name: str,
        repository_name: str,
        asset_keys: list[list[str]],
        tags: dict[str, str] | None = None,
        run_config: dict | None = None,
        partition: str | None = None,
    ) -> DgApiRunLaunchResult:
        """Materialize an ad hoc selection of assets.

        This launches the implicit asset job with the given selection, which is what the
        graphql api expects; there is no separate asset materialization mutation. All the
        assets must live in the same repository and code location.
        """
        if not asset_keys:
            raise DagsterPlusGraphqlError("At least one asset key is required.")

        return self._launch(
            location_name=location_name,
            repository_name=repository_name,
            job_name=IMPLICIT_ASSET_JOB_NAME,
            asset_keys=asset_keys,
            tags=tags,
            run_config=run_config,
            partition=partition,
        )

    def _launch(
        self,
        *,
        location_name: str,
        repository_name: str,
        job_name: str,
        asset_keys: list[list[str]] | None,
        tags: dict[str, str] | None,
        run_config: dict | None,
        partition: str | None,
    ) -> DgApiRunLaunchResult:
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
                [AssetKeyInput(path=key) for key in asset_keys] if asset_keys else None
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
                    job_name=result.run.job_name,  # ty: ignore[unresolved-attribute]
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

    def action_terminate_run(self, run_id: str) -> DgApiRunTerminateResult:
        result = self._client.terminate_run(run_id=run_id).terminate_run

        match result.typename__:
            case "TerminateRunSuccess":
                return DgApiRunTerminateResult(
                    run_id=result.run.run_id,  # ty: ignore[unresolved-attribute]
                    status=result.run.status,  # ty: ignore[unresolved-attribute]
                )
            case "TerminateRunFailure":
                raise DagsterPlusGraphqlError(f"Could not terminate run: {result.message}")  # ty: ignore[unresolved-attribute]
            case "RunNotFoundError":
                raise DagsterPlusGraphqlError(f"Run not found: {result.message}")  # ty: ignore[unresolved-attribute]
            case "UnauthorizedError":
                raise DagsterPlusGraphqlError(f"Unauthorized: {result.message}")  # ty: ignore[unresolved-attribute]
            case "PythonError":
                raise DagsterPlusGraphqlError(f"Error terminating run: {result.message}")  # ty: ignore[unresolved-attribute]
            case _ as unreachable:
                assert_never(unreachable)

    def action_reexecute_run(
        self,
        parent_run_id: str,
        strategy: ReexecutionStrategy = ReexecutionStrategy.FROM_FAILURE,
        use_parent_run_tags: bool | None = None,
        extra_tags: dict[str, str] | None = None,
    ) -> DgApiRunReexecuteResult:
        result = self._client.rerun_run(
            reexecution_params=_reexecution_params(
                parent_run_id=parent_run_id,
                strategy=strategy,
                use_parent_run_tags=use_parent_run_tags,
                extra_tags=extra_tags,
            )
        ).launch_run_reexecution

        match result.typename__:
            case "LaunchRunSuccess":
                return DgApiRunReexecuteResult(
                    run_id=result.run.run_id,  # ty: ignore[unresolved-attribute]
                    status=result.run.status,  # ty: ignore[unresolved-attribute]
                    job_name=result.run.job_name,  # ty: ignore[unresolved-attribute]
                    root_run_id=result.run.root_run_id,  # ty: ignore[unresolved-attribute]
                    parent_run_id=result.run.parent_run_id,  # ty: ignore[unresolved-attribute]
                )
            case _:
                raise DagsterPlusGraphqlError(
                    f"Error re-executing run: {_reexecution_error(result)}"
                )

    def action_reexecute_backfill(
        self,
        parent_run_id: str,
        strategy: ReexecutionStrategy = ReexecutionStrategy.FROM_FAILURE,
        use_parent_run_tags: bool | None = None,
        extra_tags: dict[str, str] | None = None,
    ) -> DgApiBackfillReexecuteResult:
        result = self._client.rerun_backfill(
            reexecution_params=_reexecution_params(
                parent_run_id=parent_run_id,
                strategy=strategy,
                use_parent_run_tags=use_parent_run_tags,
                extra_tags=extra_tags,
            )
        ).reexecute_partition_backfill

        match result.typename__:
            case "LaunchBackfillSuccess":
                return DgApiBackfillReexecuteResult(
                    backfill_id=result.backfill_id,  # ty: ignore[unresolved-attribute]
                    launched_run_ids=[
                        run_id
                        for run_id in (result.launched_run_ids or [])  # ty: ignore[unresolved-attribute]
                        if run_id is not None
                    ],
                )
            case _:
                raise DagsterPlusGraphqlError(
                    f"Error re-executing backfill: {_reexecution_error(result)}"
                )
