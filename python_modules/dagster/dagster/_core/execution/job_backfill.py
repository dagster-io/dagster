import logging
import os
import time
from typing import Callable, Iterable, Mapping, Optional, Sequence, Tuple, cast

import dagster._check as check
from dagster._core.definitions.selector import JobSubsetSelector
from dagster._core.errors import DagsterBackfillFailedError
from dagster._core.execution.plan.resume_retry import ReexecutionStrategy
from dagster._core.execution.plan.state import KnownExecutionState
from dagster._core.host_representation import (
    CodeLocation,
    ExternalJob,
    ExternalPartitionSet,
)
from dagster._core.host_representation.external_data import (
    ExternalPartitionExecutionParamData,
    ExternalPartitionSetExecutionParamData,
)
from dagster._core.host_representation.origin import ExternalPartitionSetOrigin
from dagster._core.instance import DagsterInstance
from dagster._core.storage.dagster_run import DagsterRun, DagsterRunStatus, RunsFilter
from dagster._core.storage.tags import (
    PARENT_RUN_ID_TAG,
    PARTITION_NAME_TAG,
    PARTITION_SET_TAG,
    ROOT_RUN_ID_TAG,
)
from dagster._core.telemetry import BACKFILL_RUN_CREATED, hash_name, log_action
from dagster._core.utils import make_new_run_id
from dagster._core.workspace.context import (
    BaseWorkspaceRequestContext,
    IWorkspaceProcessContext,
)
from dagster._utils.error import SerializableErrorInfo
from dagster._utils.merger import merge_dicts

from .backfill import BulkActionStatus, PartitionBackfill

# out of abundance of caution, sleep at checkpoints in case we are pinning CPU by submitting lots
# of jobs all at once
CHECKPOINT_INTERVAL = 1
CHECKPOINT_COUNT = 25


def execute_job_backfill_iteration(
    backfill: PartitionBackfill,
    logger: logging.Logger,
    workspace_process_context: IWorkspaceProcessContext,
    debug_crash_flags: Optional[Mapping[str, int]],
    instance: DagsterInstance,
) -> Iterable[Optional[SerializableErrorInfo]]:
    if not backfill.last_submitted_partition_name:
        logger.info(f"Starting backfill for {backfill.backfill_id}")
    else:
        logger.info(
            f"Resuming backfill for {backfill.backfill_id} from"
            f" {backfill.last_submitted_partition_name}"
        )

    _check_repo_has_partition_set(workspace_process_context, backfill)

    has_more = True
    while has_more:
        if backfill.status != BulkActionStatus.REQUESTED:
            break

        chunk, checkpoint, has_more = _get_partitions_chunk(
            instance, logger, backfill, CHECKPOINT_COUNT
        )
        _check_for_debug_crash(debug_crash_flags, "BEFORE_SUBMIT")

        if chunk:
            for _run_id in submit_backfill_runs(
                instance,
                lambda: workspace_process_context.create_request_context(),
                backfill,
                chunk,
            ):
                yield None
                # before submitting, refetch the backfill job to check for status changes
                backfill = cast(PartitionBackfill, instance.get_backfill(backfill.backfill_id))
                if backfill.status != BulkActionStatus.REQUESTED:
                    return

        _check_for_debug_crash(debug_crash_flags, "AFTER_SUBMIT")

        if has_more:
            # refetch, in case the backfill was updated in the meantime
            backfill = cast(PartitionBackfill, instance.get_backfill(backfill.backfill_id))
            instance.update_backfill(backfill.with_partition_checkpoint(checkpoint))
            yield None
            time.sleep(CHECKPOINT_INTERVAL)
        else:
            partition_names = cast(Sequence[str], backfill.partition_names)
            logger.info(
                f"Backfill completed for {backfill.backfill_id} for"
                f" {len(partition_names)} partitions"
            )
            instance.update_backfill(backfill.with_status(BulkActionStatus.COMPLETED))
            yield None


def _check_repo_has_partition_set(
    workspace_process_context: IWorkspaceProcessContext, backfill_job: PartitionBackfill
) -> None:
    origin = cast(ExternalPartitionSetOrigin, backfill_job.partition_set_origin)

    location_name = origin.external_repository_origin.code_location_origin.location_name

    workspace = workspace_process_context.create_request_context()
    code_location = workspace.get_code_location(location_name)

    repo_name = origin.external_repository_origin.repository_name
    if not code_location.has_repository(repo_name):
        raise DagsterBackfillFailedError(
            f"Could not find repository {repo_name} in location {code_location.name} to "
            f"run backfill {backfill_job.backfill_id}."
        )

    partition_set_name = origin.partition_set_name
    external_repo = code_location.get_repository(repo_name)
    if not external_repo.has_external_partition_set(partition_set_name):
        raise DagsterBackfillFailedError(
            f"Could not find partition set {partition_set_name} in repository {repo_name}. "
        )


def _get_partitions_chunk(
    instance: DagsterInstance,
    logger: logging.Logger,
    backfill_job: PartitionBackfill,
    chunk_size: int,
) -> Tuple[Sequence[str], str, bool]:
    partition_names = cast(Sequence[str], backfill_job.partition_names)
    checkpoint = backfill_job.last_submitted_partition_name

    if (
        backfill_job.last_submitted_partition_name
        and backfill_job.last_submitted_partition_name in partition_names
    ):
        index = partition_names.index(backfill_job.last_submitted_partition_name)
        partition_names = partition_names[index + 1 :]

    # for idempotence, fetch all runs with the current backfill id
    backfill_runs = instance.get_runs(
        RunsFilter(tags=DagsterRun.tags_for_backfill_id(backfill_job.backfill_id))
    )
    completed_partitions = set([run.tags.get(PARTITION_NAME_TAG) for run in backfill_runs])
    initial_checkpoint = (
        partition_names.index(checkpoint) + 1 if checkpoint and checkpoint in partition_names else 0
    )
    partition_names = partition_names[initial_checkpoint:]
    has_more = chunk_size < len(partition_names)
    partitions_chunk = partition_names[:chunk_size]
    next_checkpoint = partitions_chunk[-1]

    to_skip = set(partitions_chunk).intersection(completed_partitions)
    if to_skip:
        logger.info(
            f"Found {len(to_skip)} existing runs for backfill {backfill_job.backfill_id}, skipping"
        )
    to_submit = [
        partition_name
        for partition_name in partitions_chunk
        if partition_name not in completed_partitions
    ]
    return to_submit, next_checkpoint, has_more


def submit_backfill_runs(
    instance: DagsterInstance,
    create_workspace: Callable[[], BaseWorkspaceRequestContext],
    backfill_job: PartitionBackfill,
    partition_names: Optional[Sequence[str]] = None,
) -> Iterable[Optional[str]]:
    """Returns the run IDs of the submitted runs."""
    origin = cast(ExternalPartitionSetOrigin, backfill_job.partition_set_origin)

    repository_origin = origin.external_repository_origin
    repo_name = repository_origin.repository_name
    location_name = repository_origin.code_location_origin.location_name

    if not partition_names:
        partition_names = cast(Sequence[str], backfill_job.partition_names)

    workspace = create_workspace()
    code_location = workspace.get_code_location(location_name)

    check.invariant(
        code_location.has_repository(repo_name),
        f"Could not find repository {repo_name} in location {code_location.name}",
    )
    external_repo = code_location.get_repository(repo_name)
    partition_set_name = origin.partition_set_name
    external_partition_set = external_repo.get_external_partition_set(partition_set_name)
    result = code_location.get_external_partition_set_execution_param_data(
        external_repo.handle, partition_set_name, partition_names, instance
    )

    assert isinstance(result, ExternalPartitionSetExecutionParamData)
    if backfill_job.asset_selection:
        # need to make another call to the user code location to properly subset
        # for an asset selection
        pipeline_selector = JobSubsetSelector(
            location_name=code_location.name,
            repository_name=repo_name,
            job_name=external_partition_set.job_name,
            op_selection=None,
            asset_selection=backfill_job.asset_selection,
        )
        external_job = code_location.get_external_job(pipeline_selector)
    else:
        external_job = external_repo.get_full_external_job(external_partition_set.job_name)
    for partition_data in result.partition_data:
        # Refresh the code location in case the workspace has reloaded mid-backfill
        workspace = create_workspace()
        code_location = workspace.get_code_location(location_name)

        dagster_run = create_backfill_run(
            instance,
            code_location,
            external_job,
            external_partition_set,
            backfill_job,
            partition_data,
        )
        if dagster_run:
            # we skip runs in certain cases, e.g. we are running a `from_failure` backfill job
            # and the partition has had a successful run since the time the backfill was
            # scheduled
            instance.submit_run(dagster_run.run_id, workspace)
            yield dagster_run.run_id
        yield None


def create_backfill_run(
    instance: DagsterInstance,
    code_location: CodeLocation,
    external_pipeline: ExternalJob,
    external_partition_set: ExternalPartitionSet,
    backfill_job: PartitionBackfill,
    partition_data: ExternalPartitionExecutionParamData,
) -> Optional[DagsterRun]:
    from dagster._daemon.daemon import get_telemetry_daemon_session_id

    log_action(
        instance,
        BACKFILL_RUN_CREATED,
        metadata={
            "DAEMON_SESSION_ID": get_telemetry_daemon_session_id(),
            "repo_hash": hash_name(code_location.name),
            "pipeline_name_hash": hash_name(external_pipeline.name),
        },
    )

    tags = merge_dicts(
        external_pipeline.tags,
        partition_data.tags,
        DagsterRun.tags_for_backfill_id(backfill_job.backfill_id),
        backfill_job.tags,
    )

    resolved_op_selection = None
    op_selection = None
    if not backfill_job.from_failure and not backfill_job.reexecution_steps:
        step_keys_to_execute = None
        parent_run_id = None
        root_run_id = None
        known_state = None
        if external_partition_set.op_selection:
            resolved_op_selection = frozenset(external_partition_set.op_selection)
            op_selection = external_partition_set.op_selection

    elif backfill_job.from_failure:
        last_run = _fetch_last_run(instance, external_partition_set, partition_data.name)
        if not last_run or last_run.status != DagsterRunStatus.FAILURE:
            return None
        return instance.create_reexecuted_run(
            parent_run=last_run,
            code_location=code_location,
            external_job=external_pipeline,
            strategy=ReexecutionStrategy.FROM_FAILURE,
            extra_tags=tags,
            run_config=partition_data.run_config,
            use_parent_run_tags=False,  # don't inherit tags from the previous run
        )

    else:  # backfill_job.reexecution_steps
        last_run = _fetch_last_run(instance, external_partition_set, partition_data.name)
        parent_run_id = last_run.run_id if last_run else None
        root_run_id = (last_run.root_run_id or last_run.run_id) if last_run else None
        if parent_run_id and root_run_id:
            tags = merge_dicts(
                tags, {PARENT_RUN_ID_TAG: parent_run_id, ROOT_RUN_ID_TAG: root_run_id}
            )
        step_keys_to_execute = backfill_job.reexecution_steps
        if last_run and last_run.status == DagsterRunStatus.SUCCESS:
            known_state = KnownExecutionState.build_for_reexecution(
                instance,
                last_run,
            ).update_for_step_selection(step_keys_to_execute)
        else:
            known_state = None

        if external_partition_set.op_selection:
            resolved_op_selection = frozenset(external_partition_set.op_selection)
            op_selection = external_partition_set.op_selection

    external_execution_plan = code_location.get_external_execution_plan(
        external_pipeline,
        partition_data.run_config,
        step_keys_to_execute=step_keys_to_execute,
        known_state=known_state,
        instance=instance,
    )

    return instance.create_run(
        job_snapshot=external_pipeline.job_snapshot,
        execution_plan_snapshot=external_execution_plan.execution_plan_snapshot,
        parent_job_snapshot=external_pipeline.parent_job_snapshot,
        job_name=external_pipeline.name,
        run_id=make_new_run_id(),
        resolved_op_selection=resolved_op_selection,
        run_config=partition_data.run_config,
        step_keys_to_execute=step_keys_to_execute,
        tags=tags,
        root_run_id=root_run_id,
        parent_run_id=parent_run_id,
        status=DagsterRunStatus.NOT_STARTED,
        external_job_origin=external_pipeline.get_external_origin(),
        job_code_origin=external_pipeline.get_python_origin(),
        op_selection=op_selection,
        asset_selection=(
            frozenset(backfill_job.asset_selection) if backfill_job.asset_selection else None
        ),
        asset_check_selection=None,
    )


def _fetch_last_run(
    instance: DagsterInstance, external_partition_set: ExternalPartitionSet, partition_name: str
) -> Optional[DagsterRun]:
    check.inst_param(instance, "instance", DagsterInstance)
    check.inst_param(external_partition_set, "external_partition_set", ExternalPartitionSet)
    check.str_param(partition_name, "partition_name")

    runs = instance.get_runs(
        RunsFilter(
            job_name=external_partition_set.job_name,
            tags={
                PARTITION_SET_TAG: external_partition_set.name,
                PARTITION_NAME_TAG: partition_name,
            },
        ),
        limit=1,
    )

    return runs[0] if runs else None


def _check_for_debug_crash(debug_crash_flags: Optional[Mapping[str, int]], key) -> None:
    if not debug_crash_flags:
        return

    kill_signal = debug_crash_flags.get(key)
    if not kill_signal:
        return

    os.kill(os.getpid(), kill_signal)
    time.sleep(10)
    raise Exception("Process didn't terminate after sending crash signal")
