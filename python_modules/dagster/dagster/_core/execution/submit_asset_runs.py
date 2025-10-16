import asyncio
import logging
import sys
import time
from collections.abc import Sequence
from typing import AbstractSet, NamedTuple, Optional  # noqa: UP035

import dagster._check as check
from dagster._core.definitions.asset_key import EntityKey
from dagster._core.definitions.assets.graph.remote_asset_graph import RemoteWorkspaceAssetGraph
from dagster._core.definitions.assets.job.asset_job import IMPLICIT_ASSET_JOB_NAME
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.run_request import RunRequest
from dagster._core.definitions.selector import JobSubsetSelector
from dagster._core.errors import DagsterInvalidSubsetError, DagsterUserCodeProcessError
from dagster._core.instance import DagsterInstance
from dagster._core.remote_representation.external import RemoteExecutionPlan, RemoteJob
from dagster._core.snap import ExecutionPlanSnapshot
from dagster._core.storage.dagster_run import DagsterRun, DagsterRunStatus
from dagster._core.workspace.context import BaseWorkspaceRequestContext, IWorkspaceProcessContext
from dagster._utils import SingleInstigatorDebugCrashFlags, check_for_debug_crash

EXECUTION_PLAN_CREATION_RETRIES = 1


class RunRequestExecutionData(NamedTuple):
    remote_job: RemoteJob
    remote_execution_plan: RemoteExecutionPlan


def _get_implicit_job_name_for_assets(
    asset_graph: RemoteWorkspaceAssetGraph, asset_keys: Sequence[AssetKey]
) -> Optional[str]:
    job_names = set(asset_graph.get_materialization_job_names(asset_keys[0]))
    for asset_key in asset_keys[1:]:
        job_names &= set(asset_graph.get_materialization_job_names(asset_key))

    return next(
        (job_name for job_name in job_names if job_name.startswith(IMPLICIT_ASSET_JOB_NAME)), None
    )


def _get_execution_plan_entity_keys(
    execution_plan_snapshot: ExecutionPlanSnapshot,
) -> AbstractSet[EntityKey]:
    output_entity_keys = set()
    for step in execution_plan_snapshot.steps:
        if step.key in execution_plan_snapshot.step_keys_to_execute:
            for output in step.outputs:
                output_properties = check.not_none(output.properties)
                if output_properties.asset_key:
                    output_entity_keys.add(output_properties.asset_key)
                if output_properties.asset_check_key:
                    output_entity_keys.add(output_properties.asset_check_key)
    return output_entity_keys


async def get_job_execution_data_from_run_request(
    asset_graph: RemoteWorkspaceAssetGraph,
    run_request: RunRequest,
    instance: DagsterInstance,
    workspace: BaseWorkspaceRequestContext,
    run_request_execution_data_cache: dict[JobSubsetSelector, RunRequestExecutionData],
) -> RunRequestExecutionData:
    check.invariant(
        len(run_request.entity_keys) > 0,
        "Expected RunRequest to have an asset selection or asset check keys",
    )
    handle = asset_graph.get_repository_handle(run_request.entity_keys[0])
    location_name = handle.location_name
    job_name = (
        _get_implicit_job_name_for_assets(asset_graph, run_request.asset_selection)
        if run_request.asset_selection
        # if we're only executing checks, then this must have been created after the single implicit
        # asset job changes, so we don't need to do the more exhaustive check
        else IMPLICIT_ASSET_JOB_NAME
    )
    if job_name is None:
        check.failed(
            "Could not find an implicit asset job for the given assets:"
            f" {run_request.asset_selection}"
        )

    pipeline_selector = JobSubsetSelector(
        location_name=location_name,
        repository_name=handle.repository_name,
        job_name=job_name,
        asset_selection=run_request.asset_selection,
        asset_check_selection=run_request.asset_check_keys,
        op_selection=None,
        run_config=run_request.run_config or {},
    )

    if pipeline_selector not in run_request_execution_data_cache:
        remote_job, remote_execution_plan = await asyncio.gather(
            RemoteJob.gen(workspace, pipeline_selector),
            RemoteExecutionPlan.gen(workspace, pipeline_selector),
        )
        run_request_execution_data_cache[pipeline_selector] = RunRequestExecutionData(
            check.not_none(remote_job),
            check.not_none(remote_execution_plan),
        )

    return run_request_execution_data_cache[pipeline_selector]


async def _create_asset_run(
    run_id: Optional[str],
    run_request: RunRequest,
    run_request_index: int,
    instance: DagsterInstance,
    run_request_execution_data_cache: dict[JobSubsetSelector, RunRequestExecutionData],
    workspace_process_context: IWorkspaceProcessContext,
    workspace: BaseWorkspaceRequestContext,
    debug_crash_flags: SingleInstigatorDebugCrashFlags,
    logger: logging.Logger,
) -> DagsterRun:
    """Creates a run on the instance for the given run request. Ensures that the created run results
    in an ExecutionPlan that targets the given asset selection. If it does not, attempts to create
    a valid ExecutionPlan by reloading the workspace.
    """
    from dagster._daemon.controller import RELOAD_WORKSPACE_INTERVAL

    if not run_request.asset_selection and not run_request.asset_check_keys:
        check.failed("Expected RunRequest to have an asset selection")

    for i in range(EXECUTION_PLAN_CREATION_RETRIES + 1):
        should_retry = False
        execution_data = None

        # retry until the execution plan targets the asset selection
        try:
            asset_graph = workspace.asset_graph
            execution_data = await get_job_execution_data_from_run_request(
                asset_graph,
                run_request,
                instance,
                workspace=workspace,
                run_request_execution_data_cache=run_request_execution_data_cache,
            )

        except (DagsterInvalidSubsetError, DagsterUserCodeProcessError) as e:
            # Only retry on DagsterInvalidSubsetErrors raised within the code server
            if isinstance(e, DagsterUserCodeProcessError) and not any(
                error_info.cls_name == "DagsterInvalidSubsetError"
                for error_info in e.user_code_process_error_infos
            ):
                raise

            logger.warning(
                "Error while generating the execution plan, possibly because the code server is "
                "out of sync with the daemon. The daemon periodically refreshes its representation "
                f"of the workspace every {RELOAD_WORKSPACE_INTERVAL} seconds - pausing long enough "
                "to ensure that that refresh will happen to bring them back in sync.",
                exc_info=sys.exc_info(),
            )
            should_retry = True

        check_for_debug_crash(debug_crash_flags, "EXECUTION_PLAN_CREATED")
        check_for_debug_crash(debug_crash_flags, f"EXECUTION_PLAN_CREATED_{run_request_index}")

        if not should_retry:
            execution_plan_entity_keys = _get_execution_plan_entity_keys(
                check.not_none(execution_data).remote_execution_plan.execution_plan_snapshot
            )

            if not all(
                key in execution_plan_entity_keys
                for key in [
                    *(run_request.asset_selection or []),
                    *(run_request.asset_check_keys or []),
                ]
            ):
                logger.warning(
                    f"Execution plan targeted the following keys: {execution_plan_entity_keys}, "
                    "which did not include all assets / checks on the run request, "
                    "possibly because the code server is out of sync with the daemon. The daemon "
                    "periodically refreshes its representation of the workspace every "
                    f"{RELOAD_WORKSPACE_INTERVAL} seconds - pausing long enough "
                    "to ensure that that refresh will happen to bring them back in sync.",
                )

                should_retry = True

        if not should_retry:
            remote_job = check.not_none(execution_data).remote_job
            remote_execution_plan = check.not_none(execution_data).remote_execution_plan

            run = instance.create_run(
                job_snapshot=remote_job.job_snapshot,
                execution_plan_snapshot=remote_execution_plan.execution_plan_snapshot,
                parent_job_snapshot=remote_job.parent_job_snapshot,
                job_name=remote_job.name,
                run_id=run_id,
                resolved_op_selection=None,
                op_selection=None,
                run_config=run_request.run_config or {},
                step_keys_to_execute=None,
                tags=run_request.tags,
                root_run_id=None,
                parent_run_id=None,
                status=DagsterRunStatus.NOT_STARTED,
                remote_job_origin=remote_job.get_remote_origin(),
                job_code_origin=remote_job.get_python_origin(),
                asset_selection=frozenset(run_request.asset_selection)
                if run_request.asset_selection
                else None,
                asset_check_selection=frozenset(run_request.asset_check_keys)
                if run_request.asset_check_keys
                else None,
                asset_graph=asset_graph,  # pyright: ignore[reportPossiblyUnboundVariable]
            )

            return run

        if i < EXECUTION_PLAN_CREATION_RETRIES:
            # Sleep for RELOAD_WORKSPACE_INTERVAL seconds since the workspace can be refreshed
            # at most once every interval
            time.sleep(RELOAD_WORKSPACE_INTERVAL)
            # Clear the execution plan cache as this data is no longer valid
            run_request_execution_data_cache = {}

            # If the execution plan does not targets the asset selection, the asset graph
            # likely is outdated and targeting the wrong job, refetch the asset
            # graph from the workspace
            workspace = workspace_process_context.create_request_context()
            asset_graph = workspace.asset_graph

    check.failed(
        f"Failed to target asset selection {run_request.asset_selection} in run after retrying."
    )


async def submit_asset_run(
    run_id: Optional[str],
    run_request: RunRequest,
    run_request_index: int,
    instance: DagsterInstance,
    workspace_process_context: IWorkspaceProcessContext,
    workspace: BaseWorkspaceRequestContext,
    run_request_execution_data_cache: dict[JobSubsetSelector, RunRequestExecutionData],
    debug_crash_flags: SingleInstigatorDebugCrashFlags,
    logger: logging.Logger,
) -> DagsterRun:
    """Submits a run for a run request that targets an asset selection. If the run already exists,
    submits the existing run. If the run does not exist, creates a new run and submits it, ensuring
    that the created run targets the given asset selection.
    """
    entity_keys: Sequence[EntityKey] = [
        *(run_request.asset_selection or []),
        *(run_request.asset_check_keys or []),
    ]

    check.invariant(len(entity_keys) > 0)

    # check if the run already exists
    existing_run = instance.get_run_by_id(run_id) if run_id else None
    if existing_run:
        if existing_run.status != DagsterRunStatus.NOT_STARTED:
            logger.warn(
                f"Run {run_id} already submitted on a previously interrupted tick, skipping"
            )

            check_for_debug_crash(debug_crash_flags, "RUN_SUBMITTED")
            check_for_debug_crash(debug_crash_flags, f"RUN_SUBMITTED_{run_request_index}")

            return existing_run
        else:
            logger.warn(
                f"Run {run_id} already created on a previously interrupted tick, submitting"
            )
            run_to_submit = existing_run
    else:
        run_to_submit = await _create_asset_run(
            run_id,
            run_request,
            run_request_index,
            instance,
            run_request_execution_data_cache,
            workspace_process_context,
            workspace,
            debug_crash_flags,
            logger,
        )

    check_for_debug_crash(debug_crash_flags, "RUN_CREATED")
    check_for_debug_crash(debug_crash_flags, f"RUN_CREATED_{run_request_index}")

    instance.submit_run(run_to_submit.run_id, workspace_process_context.create_request_context())

    check_for_debug_crash(debug_crash_flags, "RUN_SUBMITTED")
    check_for_debug_crash(debug_crash_flags, f"RUN_SUBMITTED_{run_request_index}")

    asset_key_str = ", ".join([key.to_user_string() for key in entity_keys])

    logger.info(
        f"Submitted run {run_to_submit.run_id} for assets/checks {asset_key_str} with tags"
        f" {run_request.tags}"
    )

    return run_to_submit
