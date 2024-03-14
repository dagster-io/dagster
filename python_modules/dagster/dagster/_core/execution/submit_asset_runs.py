import logging
import time
from typing import Dict, Iterator, List, NamedTuple, Optional, Sequence, Tuple, cast

import dagster._check as check
from dagster._core.definitions.assets_job import is_base_asset_job_name
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.partition import PartitionsDefinition
from dagster._core.definitions.remote_asset_graph import RemoteAssetGraph
from dagster._core.definitions.run_request import RunRequest
from dagster._core.definitions.selector import JobSubsetSelector
from dagster._core.errors import (
    DagsterCodeLocationLoadError,
    DagsterInvalidSubsetError,
    DagsterUserCodeUnreachableError,
)
from dagster._core.instance import DagsterInstance
from dagster._core.remote_representation import ExternalExecutionPlan, ExternalJob
from dagster._core.snap import ExecutionPlanSnapshot
from dagster._core.storage.dagster_run import DagsterRun, DagsterRunStatus
from dagster._core.workspace.context import BaseWorkspaceRequestContext, IWorkspaceProcessContext
from dagster._utils import SingleInstigatorDebugCrashFlags, check_for_debug_crash, hash_collection

EXECUTION_PLAN_CREATION_RETRIES = 1


class RunRequestExecutionData(NamedTuple):
    external_job: ExternalJob
    external_execution_plan: ExternalExecutionPlan
    partitions_def: Optional[PartitionsDefinition]


def _get_implicit_job_name_for_assets(
    asset_graph: RemoteAssetGraph, asset_keys: Sequence[AssetKey]
) -> Optional[str]:
    job_names = set(asset_graph.get_materialization_job_names(asset_keys[0]))
    for asset_key in asset_keys[1:]:
        job_names &= set(asset_graph.get_materialization_job_names(asset_key))

    return next(job_name for job_name in job_names if is_base_asset_job_name(job_name))


def _execution_plan_targets_asset_selection(
    execution_plan_snapshot: ExecutionPlanSnapshot, asset_selection: Sequence[AssetKey]
) -> bool:
    output_asset_keys = set()
    for step in execution_plan_snapshot.steps:
        if step.key in execution_plan_snapshot.step_keys_to_execute:
            for output in step.outputs:
                asset_key = check.not_none(output.properties).asset_key
                if asset_key:
                    output_asset_keys.add(asset_key)
    return all(key in output_asset_keys for key in asset_selection)


def _get_job_execution_data_from_run_request(
    asset_graph: RemoteAssetGraph,
    run_request: RunRequest,
    instance: DagsterInstance,
    workspace: BaseWorkspaceRequestContext,
    run_request_execution_data_cache: Dict[int, RunRequestExecutionData],
) -> RunRequestExecutionData:
    repo_handle = asset_graph.get_repository_handle(
        cast(Sequence[AssetKey], run_request.asset_selection)[0]
    )
    location_name = repo_handle.code_location_origin.location_name
    job_name = _get_implicit_job_name_for_assets(
        asset_graph, cast(Sequence[AssetKey], run_request.asset_selection)
    )
    if job_name is None:
        check.failed(
            "Could not find an implicit asset job for the given assets:"
            f" {run_request.asset_selection}"
        )

    if not run_request.asset_selection:
        check.failed("Expected RunRequest to have an asset selection")

    pipeline_selector = JobSubsetSelector(
        location_name=location_name,
        repository_name=repo_handle.repository_name,
        job_name=job_name,
        asset_selection=run_request.asset_selection,
        op_selection=None,
    )

    selector_id = hash_collection(pipeline_selector)

    if selector_id not in run_request_execution_data_cache:
        code_location = workspace.get_code_location(repo_handle.code_location_origin.location_name)
        external_job = code_location.get_external_job(pipeline_selector)

        external_execution_plan = code_location.get_external_execution_plan(
            external_job,
            {},
            step_keys_to_execute=None,
            known_state=None,
            instance=instance,
        )

        partitions_def = code_location.get_asset_job_partitions_def(external_job)

        run_request_execution_data_cache[selector_id] = RunRequestExecutionData(
            external_job,
            external_execution_plan,
            partitions_def,
        )

    return run_request_execution_data_cache[selector_id]


def _create_asset_run(
    run_id: Optional[str],
    run_request: RunRequest,
    run_request_index: int,
    instance: DagsterInstance,
    run_request_execution_data_cache: Dict[int, RunRequestExecutionData],
    asset_graph: RemoteAssetGraph,
    workspace_process_context: IWorkspaceProcessContext,
    debug_crash_flags: SingleInstigatorDebugCrashFlags,
    logger: logging.Logger,
) -> DagsterRun:
    """Creates a run on the instance for the given run request. Ensures that the created run results
    in an ExecutionPlan that targets the given asset selection. If it does not, attempts to create
    a valid ExecutionPlan by reloading the workspace.
    """
    from dagster._daemon.controller import RELOAD_WORKSPACE_INTERVAL

    if not run_request.asset_selection:
        check.failed("Expected RunRequest to have an asset selection")

    for _ in range(EXECUTION_PLAN_CREATION_RETRIES + 1):
        try:
            # create a new request context for each run in case the code location server
            # is swapped out in the middle of the submission process
            workspace = workspace_process_context.create_request_context()
            execution_data = _get_job_execution_data_from_run_request(
                asset_graph,
                run_request,
                instance,
                workspace=workspace,
                run_request_execution_data_cache=run_request_execution_data_cache,
            )
            check_for_debug_crash(debug_crash_flags, "EXECUTION_PLAN_CREATED")
            check_for_debug_crash(debug_crash_flags, f"EXECUTION_PLAN_CREATED_{run_request_index}")

            # retry until the execution plan targets the asset selection
            if _execution_plan_targets_asset_selection(
                execution_data.external_execution_plan.execution_plan_snapshot,
                check.not_none(run_request.asset_selection),
            ):
                external_job = execution_data.external_job
                external_execution_plan = execution_data.external_execution_plan
                partitions_def = execution_data.partitions_def

                run = instance.create_run(
                    job_snapshot=external_job.job_snapshot,
                    execution_plan_snapshot=external_execution_plan.execution_plan_snapshot,
                    parent_job_snapshot=external_job.parent_job_snapshot,
                    job_name=external_job.name,
                    run_id=run_id,
                    resolved_op_selection=None,
                    op_selection=None,
                    run_config={},
                    step_keys_to_execute=None,
                    tags=run_request.tags,
                    root_run_id=None,
                    parent_run_id=None,
                    status=DagsterRunStatus.NOT_STARTED,
                    external_job_origin=external_job.get_external_origin(),
                    job_code_origin=external_job.get_python_origin(),
                    asset_selection=frozenset(run_request.asset_selection),
                    asset_check_selection=None,
                    asset_job_partitions_def=partitions_def,
                )

                return run
        except DagsterInvalidSubsetError:
            pass

        logger.warning(
            "Execution plan is out of sync with the workspace. Pausing run submission for "
            f"{RELOAD_WORKSPACE_INTERVAL} to allow the execution plan to rebuild with the updated workspace."
        )
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


def submit_asset_run(
    run_id: Optional[str],
    run_request: RunRequest,
    run_request_index: int,
    instance: DagsterInstance,
    workspace_process_context: IWorkspaceProcessContext,
    asset_graph: RemoteAssetGraph,
    run_request_execution_data_cache: Dict[int, RunRequestExecutionData],
    debug_crash_flags: SingleInstigatorDebugCrashFlags,
    logger: logging.Logger,
) -> DagsterRun:
    """Submits a run for a run request that targets an asset selection. If the run already exists,
    submits the existing run. If the run does not exist, creates a new run and submits it, ensuring
    that the created run targets the given asset selection.
    """
    check.invariant(not run_request.run_config, "Asset run requests have no custom run config")
    asset_keys = check.not_none(run_request.asset_selection)

    check.invariant(len(asset_keys) > 0)

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
        run_to_submit = _create_asset_run(
            run_id,
            run_request,
            run_request_index,
            instance,
            run_request_execution_data_cache,
            asset_graph,
            workspace_process_context,
            debug_crash_flags,
            logger,
        )

    check_for_debug_crash(debug_crash_flags, "RUN_CREATED")
    check_for_debug_crash(debug_crash_flags, f"RUN_CREATED_{run_request_index}")

    instance.submit_run(run_to_submit.run_id, workspace_process_context.create_request_context())

    check_for_debug_crash(debug_crash_flags, "RUN_SUBMITTED")
    check_for_debug_crash(debug_crash_flags, f"RUN_SUBMITTED_{run_request_index}")

    asset_key_str = ", ".join([asset_key.to_user_string() for asset_key in asset_keys])

    logger.info(
        f"Submitted run {run_to_submit.run_id} for assets {asset_key_str} with tags"
        f" {run_request.tags}"
    )

    return run_to_submit


class SubmitRunRequestChunkResult(NamedTuple):
    chunk_submitted_runs: Sequence[Tuple[RunRequest, DagsterRun]]
    retryable_error_raised: bool


def submit_asset_runs_in_chunks(
    run_requests: Sequence[RunRequest],
    reserved_run_ids: Optional[Sequence[str]],
    chunk_size: int,
    instance: DagsterInstance,
    workspace_process_context: IWorkspaceProcessContext,
    asset_graph: RemoteAssetGraph,
    debug_crash_flags: SingleInstigatorDebugCrashFlags,
    logger: logging.Logger,
    backfill_id: Optional[str] = None,
) -> Iterator[Optional[SubmitRunRequestChunkResult]]:
    """Submits runs for a sequence of run requests that target asset selections in chunks. Yields
    None after each run is submitted to allow the daemon to heartbeat, and yields a list of tuples
    of the run request and the submitted run after each chunk is submitted to allow the caller to
    interrupt this process if needed.
    """
    if reserved_run_ids is not None:
        check.invariant(len(run_requests) == len(reserved_run_ids))

    run_request_execution_data_cache = {}
    for chunk_start in range(0, len(run_requests), chunk_size):
        run_request_chunk = run_requests[chunk_start : chunk_start + chunk_size]
        chunk_submitted_runs: List[Tuple[RunRequest, DagsterRun]] = []
        retryable_error_raised = False

        logger.debug(f"{chunk_size}, {chunk_start}, {len(run_request_chunk)}")

        # submit each run in the chunk
        for chunk_idx, run_request in enumerate(run_request_chunk):
            run_request_idx = chunk_start + chunk_idx
            run_id = reserved_run_ids[run_request_idx] if reserved_run_ids else None
            try:
                submitted_run = submit_asset_run(
                    run_id,
                    run_request,
                    run_request_idx,
                    instance,
                    workspace_process_context,
                    asset_graph,
                    run_request_execution_data_cache,
                    debug_crash_flags,
                    logger,
                )
                chunk_submitted_runs.append((run_request, submitted_run))
                # allow the daemon to heartbeat while runs are submitted
                yield None
            except (DagsterUserCodeUnreachableError, DagsterCodeLocationLoadError) as e:
                logger.warning(
                    f"Unable to reach the user code server for assets {run_request.asset_selection}."
                    f" Backfill {backfill_id} will resume execution once the server is available."
                    f"User code server error: {e}"
                )
                retryable_error_raised = True
                # Stop submitting runs if the user code server is unreachable for any
                # given run request
                break

        yield SubmitRunRequestChunkResult(chunk_submitted_runs, retryable_error_raised)
