import os
import time

from dagster import check
from dagster.core.errors import DagsterBackfillFailedError
from dagster.core.execution.backfill import (
    BulkActionStatus,
    PartitionBackfill,
    submit_backfill_runs,
)
from dagster.core.instance import DagsterInstance
from dagster.core.storage.pipeline_run import PipelineRun, PipelineRunsFilter
from dagster.core.storage.tags import PARTITION_NAME_TAG
from dagster.utils.error import SerializableErrorInfo

# out of abundance of caution, sleep at checkpoints in case we are pinning CPU by submitting lots
# of jobs all at once
CHECKPOINT_INTERVAL = 1
CHECKPOINT_COUNT = 25


def _check_for_debug_crash(debug_crash_flags, key):
    if not debug_crash_flags:
        return

    kill_signal = debug_crash_flags.get(key)
    if not kill_signal:
        return

    os.kill(os.getpid(), kill_signal)
    time.sleep(10)
    raise Exception("Process didn't terminate after sending crash signal")


def execute_backfill_iteration(instance, logger, debug_crash_flags=None):
    check.inst_param(instance, "instance", DagsterInstance)

    if not instance.has_bulk_actions_table():
        message = (
            "A schema migration is required before daemon-based backfills can be supported. "
            "Try running `dagster instance migrate` to migrate your instance and try again."
        )
        logger.error(message)
        yield SerializableErrorInfo(
            message=message,
            stack=[],
            cls_name="",
        )
        return

    backfill_jobs = instance.get_backfills(status=BulkActionStatus.REQUESTED)

    if not backfill_jobs:
        logger.error("No backfill jobs requested.")
        yield
        return

    for backfill_job in backfill_jobs:
        backfill_id = backfill_job.backfill_id

        if not backfill_job.last_submitted_partition_name:
            logger.info(f"Starting backfill for {backfill_id}")
        else:
            logger.info(
                f"Resuming backfill for {backfill_id} from {backfill_job.last_submitted_partition_name}"
            )

        origin = (
            backfill_job.partition_set_origin.external_repository_origin.repository_location_origin
        )

        try:
            with origin.create_handle() as repo_location_handle:
                repo_location = repo_location_handle.create_location()
                has_more = True
                while has_more:
                    chunk, checkpoint, has_more = _get_partitions_chunk(
                        instance, logger, backfill_job, CHECKPOINT_COUNT
                    )
                    _check_for_debug_crash(debug_crash_flags, "BEFORE_SUBMIT")

                    if chunk:
                        submit_backfill_runs(instance, repo_location, backfill_job, chunk)

                    _check_for_debug_crash(debug_crash_flags, "AFTER_SUBMIT")

                    if has_more:
                        instance.update_backfill(backfill_job.with_partition_checkpoint(checkpoint))
                        yield None
                        time.sleep(CHECKPOINT_INTERVAL)
                    else:
                        logger.info(
                            f"Backfill completed for {backfill_id} for {len(backfill_job.partition_names)} partitions"
                        )
                        instance.update_backfill(
                            backfill_job.with_status(BulkActionStatus.COMPLETED)
                        )
                        yield None
        except DagsterBackfillFailedError as e:
            error_info = e.serializable_error_info
            instance.update_backfill(
                backfill_job.with_status(BulkActionStatus.FAILED).with_error(error_info)
            )
            if error_info:
                logger.error(f"Backfill failed for {backfill_id}: {error_info.to_string()}")
                yield error_info


def _get_partitions_chunk(instance, logger, backfill_job, chunk_size):
    check.inst_param(backfill_job, "backfill_job", PartitionBackfill)
    partition_names = backfill_job.partition_names

    if (
        backfill_job.last_submitted_partition_name
        and backfill_job.last_submitted_partition_name in partition_names
    ):
        index = partition_names.index(backfill_job.last_submitted_partition_name)
        partition_names = partition_names[index + 1 :]

    # for idempotence, fetch all runs with the current backfill id
    backfill_runs = instance.get_runs(
        PipelineRunsFilter(tags=PipelineRun.tags_for_backfill_id(backfill_job.backfill_id))
    )
    completed_partitions = set([run.tags.get(PARTITION_NAME_TAG) for run in backfill_runs])
    has_more = chunk_size < len(partition_names)
    partitions_chunk = partition_names[:chunk_size]
    checkpoint = partitions_chunk[-1]

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
    return to_submit, checkpoint, has_more
