import logging
import time
from collections.abc import Iterable, Mapping, Sequence
from concurrent.futures import ThreadPoolExecutor
from typing import TYPE_CHECKING, Any, Callable, Optional, Union, cast

import dagster._check as check
from dagster._core.definitions.partitions.definition import PartitionsDefinition
from dagster._core.definitions.partitions.partition_key_range import PartitionKeyRange
from dagster._core.definitions.selector import JobSubsetSelector
from dagster._core.errors import DagsterBackfillFailedError, DagsterInvariantViolationError
from dagster._core.execution.backfill import (
    BulkActionStatus,
    PartitionBackfill,
    cancel_backfill_runs_and_cancellation_complete,
)
from dagster._core.execution.plan.resume_retry import ReexecutionStrategy
from dagster._core.execution.plan.state import KnownExecutionState
from dagster._core.instance import DagsterInstance
from dagster._core.remote_representation.code_location import CodeLocation
from dagster._core.remote_representation.external import RemoteJob, RemotePartitionSet
from dagster._core.remote_representation.external_data import PartitionSetExecutionParamSnap
from dagster._core.storage.dagster_run import (
    NOT_FINISHED_STATUSES,
    DagsterRun,
    DagsterRunStatus,
    RunsFilter,
)
from dagster._core.storage.tags import (
    ASSET_PARTITION_RANGE_END_TAG,
    ASSET_PARTITION_RANGE_START_TAG,
    PARENT_RUN_ID_TAG,
    PARTITION_NAME_TAG,
    PARTITION_SET_TAG,
    ROOT_RUN_ID_TAG,
)
from dagster._core.telemetry import BACKFILL_RUN_CREATED, hash_name, log_action
from dagster._core.utils import make_new_run_id
from dagster._core.workspace.context import BaseWorkspaceRequestContext, IWorkspaceProcessContext
from dagster._record import record
from dagster._time import get_current_timestamp
from dagster._utils import check_for_debug_crash
from dagster._utils.error import SerializableErrorInfo
from dagster._utils.merger import merge_dicts

if TYPE_CHECKING:
    from dagster._core.remote_origin import RemotePartitionSetOrigin

# out of abundance of caution, sleep at checkpoints in case we are pinning CPU by submitting lots
# of jobs all at once
CHECKPOINT_INTERVAL = 1
CHECKPOINT_COUNT = 25


@record
class BackfillRunRequest:
    key_or_range: Union[str, PartitionKeyRange]
    run_tags: Mapping[str, str]
    run_config: Mapping[str, Any]


def execute_job_backfill_iteration(
    backfill: PartitionBackfill,
    logger: logging.Logger,
    workspace_process_context: IWorkspaceProcessContext,
    debug_crash_flags: Optional[Mapping[str, int]],
    instance: DagsterInstance,
    submit_threadpool_executor: Optional[ThreadPoolExecutor] = None,
) -> Optional[SerializableErrorInfo]:
    if not backfill.last_submitted_partition_name:
        logger.info(f"Starting job backfill for {backfill.backfill_id}")
    else:
        logger.info(
            f"Resuming job backfill for {backfill.backfill_id} from"
            f" {backfill.last_submitted_partition_name}"
        )

    # refetch in case the backfill status has changed
    backfill = cast("PartitionBackfill", instance.get_backfill(backfill.backfill_id))
    if backfill.status == BulkActionStatus.CANCELING or backfill.status == BulkActionStatus.FAILING:
        status_once_runs_are_complete = (
            BulkActionStatus.CANCELED
            if backfill.status == BulkActionStatus.CANCELING
            else BulkActionStatus.FAILED
        )

        all_runs_canceled = cancel_backfill_runs_and_cancellation_complete(
            instance=instance,
            backfill_id=backfill.backfill_id,
            logger=logger,
        )

        if all_runs_canceled:
            instance.update_backfill(
                backfill.with_status(status_once_runs_are_complete).with_end_timestamp(
                    get_current_timestamp()
                )
            )
        return

    partition_set = _get_partition_set(workspace_process_context, backfill)
    has_more = True
    while has_more:
        if backfill.status != BulkActionStatus.REQUESTED:
            break

        chunk, checkpoint, has_more = _get_partitions_chunk(
            instance,
            logger,
            backfill,
            CHECKPOINT_COUNT,
            partition_set,
        )
        check_for_debug_crash(debug_crash_flags, "BEFORE_SUBMIT")

        if chunk:
            list(
                submit_backfill_runs(
                    instance,
                    lambda: workspace_process_context.create_request_context(),
                    backfill,
                    chunk,
                    submit_threadpool_executor,
                )
            )
            # after each chunk, refetch the backfill job to check for status changes
            backfill = cast("PartitionBackfill", instance.get_backfill(backfill.backfill_id))
            if backfill.status != BulkActionStatus.REQUESTED:
                return

        check_for_debug_crash(debug_crash_flags, "AFTER_SUBMIT")

        if has_more:
            # refetch, in case the backfill was updated in the meantime
            backfill = cast("PartitionBackfill", instance.get_backfill(backfill.backfill_id))
            instance.update_backfill(backfill.with_partition_checkpoint(checkpoint))
            time.sleep(CHECKPOINT_INTERVAL)
        else:
            unfinished_runs = instance.get_runs(
                RunsFilter(
                    tags=DagsterRun.tags_for_backfill_id(backfill.backfill_id),
                    statuses=NOT_FINISHED_STATUSES,
                ),
                limit=1,
            )
            if unfinished_runs:
                logger.info(
                    f"Backfill {backfill.backfill_id} has unfinished runs. Status will be updated when all runs are finished."
                )
                instance.update_backfill(backfill.with_partition_checkpoint(checkpoint))
                return
            partition_names = cast("Sequence[str]", backfill.partition_names)
            logger.info(
                f"Backfill completed for {backfill.backfill_id} for"
                f" {len(partition_names)} partitions"
            )
            if (
                len(
                    instance.get_run_ids(
                        filters=RunsFilter(
                            tags=DagsterRun.tags_for_backfill_id(backfill.backfill_id),
                            statuses=[DagsterRunStatus.FAILURE, DagsterRunStatus.CANCELED],
                        )
                    )
                )
                > 0
            ):
                instance.update_backfill(
                    backfill.with_status(BulkActionStatus.COMPLETED_FAILED).with_end_timestamp(
                        get_current_timestamp()
                    )
                )
            else:
                instance.update_backfill(
                    backfill.with_status(BulkActionStatus.COMPLETED_SUCCESS).with_end_timestamp(
                        get_current_timestamp()
                    )
                )


def _get_partition_set(
    workspace_process_context: IWorkspaceProcessContext, backfill_job: PartitionBackfill
) -> RemotePartitionSet:
    origin = cast("RemotePartitionSetOrigin", backfill_job.partition_set_origin)

    location_name = origin.repository_origin.code_location_origin.location_name

    workspace = workspace_process_context.create_request_context()
    code_location = workspace.get_code_location(location_name)

    repo_name = origin.repository_origin.repository_name
    if not code_location.has_repository(repo_name):
        raise DagsterBackfillFailedError(
            f"Could not find repository {repo_name} in location {code_location.name} to "
            f"run backfill {backfill_job.backfill_id}."
        )

    partition_set_name = origin.partition_set_name
    remote_repo = code_location.get_repository(repo_name)
    if not remote_repo.has_partition_set(partition_set_name):
        raise DagsterBackfillFailedError(
            f"Could not find partition set {partition_set_name} in repository {repo_name}. "
        )
    return remote_repo.get_partition_set(partition_set_name)


def _subdivide_partition_key_range(
    partitions_def: PartitionsDefinition,
    partition_key_range: PartitionKeyRange,
    max_range_size: Optional[int],
) -> Sequence[PartitionKeyRange]:
    """Take a partition key range and subdivide it into smaller ranges of size max_range_size. This
    is done to satisfy backfill policies that limit the maximum number of partitions that can be
    materialized in a run.
    """
    if max_range_size is None:
        return [partition_key_range]
    else:
        keys = partitions_def.get_partition_keys_in_range(partition_key_range)
        chunks = [keys[i : i + max_range_size] for i in range(0, len(keys), max_range_size)]
        return [PartitionKeyRange(start=chunk[0], end=chunk[-1]) for chunk in chunks]


def _get_partitions_chunk(
    instance: DagsterInstance,
    logger: logging.Logger,
    backfill_job: PartitionBackfill,
    chunk_size: int,
    partition_set: RemotePartitionSet,
) -> tuple[Sequence[Union[str, PartitionKeyRange]], str, bool]:
    partition_names = cast("Sequence[str]", backfill_job.partition_names)
    checkpoint = backfill_job.last_submitted_partition_name
    backfill_policy = partition_set.backfill_policy

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
    # fetching the partitions def of a legacy dynamic partitioned op-job will raise an error
    # so guard against it by checking if the partitions def exists first
    partitions_def = (
        partition_set.get_partitions_definition()
        if partition_set.has_partitions_definition()
        else None
    )
    completed_partitions = []
    for run in backfill_runs:
        if (
            run.tags.get(ASSET_PARTITION_RANGE_START_TAG)
            and run.tags.get(ASSET_PARTITION_RANGE_END_TAG)
            and run.tags.get(PARTITION_NAME_TAG) is None
            and partitions_def is not None
        ):
            if partitions_def is None:
                # We should not hit this case, since all PartitionsDefinitions that can be put on
                # assets are fetchable via the ExternalPartitionSet. However, we do this check so that
                # we only fetch the partitions def once before the loop
                raise DagsterInvariantViolationError(
                    f"Cannot access PartitionsDefinition for backfill {backfill_job.backfill_id}. "
                )
            completed_partitions.extend(
                partitions_def.get_partition_keys_in_range(
                    PartitionKeyRange(
                        start=run.tags[ASSET_PARTITION_RANGE_START_TAG],
                        end=run.tags[ASSET_PARTITION_RANGE_END_TAG],
                    ),
                )
            )
        elif run.tags.get(PARTITION_NAME_TAG):
            completed_partitions.append(run.tags[PARTITION_NAME_TAG])

    initial_checkpoint = (
        partition_names.index(checkpoint) + 1 if checkpoint and checkpoint in partition_names else 0
    )
    partition_names = partition_names[initial_checkpoint:]
    if len(partition_names) == 0:
        # no more partitions to submit, return early
        return [], checkpoint or "", False

    if backfill_policy and backfill_policy.max_partitions_per_run != 1:
        to_submit = [
            partition_name
            for partition_name in partition_names
            if partition_name not in completed_partitions
        ]
        partitions_def = partition_set.get_partitions_definition()
        partitions_subset = partitions_def.subset_with_partition_keys(to_submit)
        partition_key_ranges = partitions_subset.get_partition_key_ranges(partitions_def)
        subdivided_ranges = [
            sr
            for r in partition_key_ranges
            for sr in _subdivide_partition_key_range(
                partitions_def, r, backfill_policy.max_partitions_per_run
            )
        ]
        ranges_to_launch = subdivided_ranges[:chunk_size]
        has_more = chunk_size < len(subdivided_ranges)
        next_checkpoint = ranges_to_launch[-1].end if len(ranges_to_launch) > 0 else checkpoint
        to_submit = ranges_to_launch
    else:
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

    return to_submit, next_checkpoint or "", has_more


def submit_backfill_runs(
    instance: DagsterInstance,
    create_workspace: Callable[[], BaseWorkspaceRequestContext],
    backfill_job: PartitionBackfill,
    partition_names_or_ranges: Optional[Sequence[Union[str, PartitionKeyRange]]] = None,
    submit_threadpool_executor: Optional[ThreadPoolExecutor] = None,
) -> Iterable[Optional[str]]:
    """Returns the run IDs of the submitted runs."""
    origin = cast("RemotePartitionSetOrigin", backfill_job.partition_set_origin)

    repository_origin = origin.repository_origin
    repo_name = repository_origin.repository_name
    location_name = repository_origin.code_location_origin.location_name

    if not partition_names_or_ranges:
        partition_names_or_ranges = cast("Sequence[str]", backfill_job.partition_names)

    workspace = create_workspace()
    code_location = workspace.get_code_location(location_name)
    check.invariant(
        code_location.has_repository(repo_name),
        f"Could not find repository {repo_name} in location {code_location.name}",
    )
    remote_repo = code_location.get_repository(repo_name)
    partition_set_name = origin.partition_set_name
    partition_set = remote_repo.get_partition_set(partition_set_name)

    if backfill_job.asset_selection:
        # need to make another call to the user code location to properly subset
        # for an asset selection
        pipeline_selector = JobSubsetSelector(
            location_name=code_location.name,
            repository_name=repo_name,
            job_name=partition_set.job_name,
            op_selection=None,
            asset_selection=backfill_job.asset_selection,
            run_config=backfill_job.run_config,
        )
        remote_job = code_location.get_job(pipeline_selector)
    else:
        remote_job = remote_repo.get_full_job(partition_set.job_name)

    partition_data_target = check.is_list(
        [partition_names_or_ranges[0].start]
        if isinstance(partition_names_or_ranges[0], PartitionKeyRange)
        else partition_names_or_ranges,
        of_type=str,
    )
    partition_set_execution_data = code_location.get_partition_set_execution_params(
        remote_repo.handle,
        partition_set_name,
        partition_data_target,
        instance,
    )
    assert isinstance(partition_set_execution_data, PartitionSetExecutionParamSnap)

    # Partition-scoped run config is prohibited at the definitions level for a jobs that materialize
    # ranges, so we can assume that all partition data will have the same run config and tags as the
    # first partition.
    tags_by_key_or_range: Mapping[Union[str, PartitionKeyRange], Mapping[str, str]]
    run_config_by_key_or_range: Mapping[Union[str, PartitionKeyRange], Mapping[str, Any]]
    if isinstance(partition_names_or_ranges[0], PartitionKeyRange):
        partition_set_run_config = partition_set_execution_data.partition_data[0].run_config

        if partition_set_run_config and backfill_job.run_config:
            raise DagsterInvariantViolationError(
                "Cannot specify both partition-scoped run config and backfill-scoped run config. This can happen "
                "if you explicitly set a PartitionSet on your job and also specify run config when launching a backfill.",
            )

        run_config = partition_set_run_config or backfill_job.run_config or {}

        tags = {
            k: v
            for k, v in partition_set_execution_data.partition_data[0].tags.items()
            if k != PARTITION_NAME_TAG
        }
        run_config_by_key_or_range = {r: run_config for r in partition_names_or_ranges}
        tags_by_key_or_range = {
            r: {
                **tags,
                ASSET_PARTITION_RANGE_START_TAG: r.start,
                ASSET_PARTITION_RANGE_END_TAG: r.end,
            }
            for r in check.is_list(partition_names_or_ranges, of_type=PartitionKeyRange)
        }
    else:
        run_config_by_key_or_range = {
            pd.name: pd.run_config or backfill_job.run_config or {}
            for pd in partition_set_execution_data.partition_data
        }
        tags_by_key_or_range = {
            pd.name: pd.tags for pd in partition_set_execution_data.partition_data
        }

    def create_and_submit_partition_run(backfill_run_request: BackfillRunRequest) -> Optional[str]:
        workspace = create_workspace()
        code_location = workspace.get_code_location(location_name)

        dagster_run = create_backfill_run(
            instance,
            code_location,
            remote_job,
            partition_set,
            backfill_job,
            backfill_run_request.key_or_range,
            backfill_run_request.run_tags,
            backfill_run_request.run_config,
        )

        if dagster_run:
            # we skip runs in certain cases, e.g. we are running a `from_failure` backfill job
            # and the partition has had a successful run since the time the backfill was
            # scheduled
            instance.submit_run(dagster_run.run_id, workspace)
            return dagster_run.run_id

        return None

    batch_run_requests = [
        BackfillRunRequest(
            key_or_range=key_or_range,
            run_tags=tags_by_key_or_range[key_or_range],
            run_config=run_config_by_key_or_range[key_or_range],
        )
        for key_or_range in partition_names_or_ranges
    ]

    if submit_threadpool_executor:
        yield from submit_threadpool_executor.map(
            create_and_submit_partition_run, batch_run_requests
        )
    else:
        yield from map(create_and_submit_partition_run, batch_run_requests)


def create_backfill_run(
    instance: DagsterInstance,
    code_location: CodeLocation,
    remote_job: RemoteJob,
    remote_partition_set: RemotePartitionSet,
    backfill_job: PartitionBackfill,
    partition_key_or_range: Union[str, PartitionKeyRange],
    run_tags: Mapping[str, str],
    run_config: Mapping[str, Any],
) -> Optional[DagsterRun]:
    from dagster._daemon.daemon import get_telemetry_daemon_session_id

    log_action(
        instance,
        BACKFILL_RUN_CREATED,
        metadata={
            "DAEMON_SESSION_ID": get_telemetry_daemon_session_id(),
            "repo_hash": hash_name(code_location.name),
            "pipeline_name_hash": hash_name(remote_job.name),
        },
    )

    tags = merge_dicts(
        remote_job.tags,
        run_tags,
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
        if remote_partition_set.op_selection:
            resolved_op_selection = frozenset(remote_partition_set.op_selection)
            op_selection = remote_partition_set.op_selection

    elif backfill_job.from_failure:
        last_run = _fetch_last_run(instance, remote_partition_set, partition_key_or_range)
        if not last_run or last_run.status != DagsterRunStatus.FAILURE:
            return None
        return instance.create_reexecuted_run(
            parent_run=last_run,
            code_location=code_location,
            remote_job=remote_job,
            strategy=ReexecutionStrategy.FROM_FAILURE,
            extra_tags=tags,
            run_config=run_config,
            use_parent_run_tags=False,  # don't inherit tags from the previous run
        )

    else:  # backfill_job.reexecution_steps
        last_run = _fetch_last_run(instance, remote_partition_set, partition_key_or_range)
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

        if remote_partition_set.op_selection:
            resolved_op_selection = frozenset(remote_partition_set.op_selection)
            op_selection = remote_partition_set.op_selection

    remote_execution_plan = code_location.get_execution_plan(
        remote_job,
        run_config,
        step_keys_to_execute=step_keys_to_execute,
        known_state=known_state,
        instance=instance,
    )

    return instance.create_run(
        job_snapshot=remote_job.job_snapshot,
        execution_plan_snapshot=remote_execution_plan.execution_plan_snapshot,
        parent_job_snapshot=remote_job.parent_job_snapshot,
        job_name=remote_job.name,
        run_id=make_new_run_id(),
        resolved_op_selection=resolved_op_selection,
        run_config=run_config,
        step_keys_to_execute=step_keys_to_execute,
        tags=tags,
        root_run_id=root_run_id,
        parent_run_id=parent_run_id,
        status=DagsterRunStatus.NOT_STARTED,
        remote_job_origin=remote_job.get_remote_origin(),
        job_code_origin=remote_job.get_python_origin(),
        op_selection=op_selection,
        asset_selection=(
            frozenset(backfill_job.asset_selection) if backfill_job.asset_selection else None
        ),
        asset_check_selection=None,
        asset_graph=code_location.get_repository(
            remote_job.repository_handle.repository_name
        ).asset_graph,
    )


def _fetch_last_run(
    instance: DagsterInstance,
    remote_partition_set: RemotePartitionSet,
    partition_key_or_range: Union[str, PartitionKeyRange],
) -> Optional[DagsterRun]:
    check.inst_param(instance, "instance", DagsterInstance)
    check.inst_param(remote_partition_set, "remote_partition_set", RemotePartitionSet)
    check.str_param(partition_key_or_range, "partition_name")

    tags = (
        {
            PARTITION_NAME_TAG: partition_key_or_range,
        }
        if isinstance(partition_key_or_range, str)
        else {
            ASSET_PARTITION_RANGE_START_TAG: partition_key_or_range.start,
            ASSET_PARTITION_RANGE_END_TAG: partition_key_or_range.end,
        }
    )

    runs = instance.get_runs(
        RunsFilter(
            job_name=remote_partition_set.job_name,
            tags={PARTITION_SET_TAG: remote_partition_set.name, **tags},
        ),
        limit=1,
    )

    return runs[0] if runs else None
