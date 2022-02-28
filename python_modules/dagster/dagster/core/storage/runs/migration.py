from contextlib import ExitStack

from tqdm import tqdm

from dagster import check

from ..pipeline_run import PipelineRunStatus
from ..runs.base import RunStorage
from ..runs.schema import RunsTable
from ..tags import PARTITION_NAME_TAG, PARTITION_SET_TAG

RUN_PARTITIONS = "run_partitions"
RUN_START_END = "run_start_end_overwritten"  # was run_start_end, but renamed to overwrite bad timestamps written

# for `dagster instance migrate`, paired with schema changes
REQUIRED_DATA_MIGRATIONS = {
    RUN_PARTITIONS: lambda: migrate_run_partition,
}
# for `dagster instance reindex`, optionally run for better read performance
OPTIONAL_DATA_MIGRATIONS = {
    RUN_START_END: lambda: migrate_run_start_end,
}

RUN_CHUNK_SIZE = 100

UNSTARTED_RUN_STATUSES = {
    PipelineRunStatus.QUEUED,
    PipelineRunStatus.NOT_STARTED,
    PipelineRunStatus.MANAGED,
    PipelineRunStatus.STARTING,
}


def chunked_run_iterator(storage, print_fn=None, chunk_size=RUN_CHUNK_SIZE):
    with ExitStack() as stack:
        if print_fn:
            run_count = storage.get_runs_count()
            progress = stack.enter_context(tqdm(total=run_count))
        else:
            progress = None

        cursor = None
        has_more = True

        while has_more:
            chunk = storage.get_runs(cursor=cursor, limit=chunk_size)
            has_more = chunk_size and len(chunk) >= chunk_size

            for run in chunk:
                cursor = run.run_id
                yield run

            if progress:
                progress.update(len(chunk))  # pylint: disable=no-member


def chunked_run_records_iterator(storage, print_fn=None, chunk_size=RUN_CHUNK_SIZE):
    with ExitStack() as stack:
        if print_fn:
            run_count = storage.get_runs_count()
            progress = stack.enter_context(tqdm(total=run_count))
        else:
            progress = None

        cursor = None
        has_more = True

        while has_more:
            chunk = storage.get_run_records(cursor=cursor, limit=chunk_size)
            has_more = chunk_size and len(chunk) >= chunk_size

            for run in chunk:
                cursor = run.pipeline_run.run_id
                yield run

            if progress:
                progress.update(len(chunk))  # pylint: disable=no-member


def migrate_run_partition(storage, print_fn=None):
    """
    Utility method to build an asset key index from the data in existing event log records.
    Takes in event_log_storage, and a print_fn to keep track of progress.
    """
    if print_fn:
        print_fn("Querying run storage.")

    for run in chunked_run_iterator(storage, print_fn):
        if PARTITION_NAME_TAG not in run.tags:
            continue
        if PARTITION_SET_TAG not in run.tags:
            continue

        storage.add_run_tags(run.run_id, run.tags)


def migrate_run_start_end(storage, print_fn=None):
    """
    Utility method that updates the start and end times of historical runs using the completed event log.
    """

    if print_fn:
        print_fn("Querying run and event log storage.")

    for run_record in chunked_run_records_iterator(storage, print_fn):
        if run_record.pipeline_run.status in UNSTARTED_RUN_STATUSES:
            continue

        # commented out here to ensure that previously written timestamps that may not have
        # standardized to UTC would get overwritten
        # if run_record.start_time:
        #     continue

        add_run_stats(storage, run_record.pipeline_run.run_id)


def add_run_stats(run_storage: RunStorage, run_id: str) -> None:
    from dagster.core.instance import DagsterInstance
    from dagster.core.storage.runs.sql_run_storage import SqlRunStorage

    check.str_param(run_id, "run_id")
    check.inst_param(run_storage, "run_storage", RunStorage)

    if not isinstance(run_storage, SqlRunStorage):
        return

    instance = check.inst_param(
        run_storage._instance, "instance", DagsterInstance  # pylint: disable=protected-access
    )
    run_stats = instance.get_run_stats(run_id)

    with run_storage.connect() as conn:
        conn.execute(
            RunsTable.update()  # pylint: disable=no-value-for-parameter
            .where(RunsTable.c.run_id == run_id)
            .values(
                start_time=run_stats.start_time,
                end_time=run_stats.end_time,
            )
        )
