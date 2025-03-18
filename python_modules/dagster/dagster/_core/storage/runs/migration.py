from collections.abc import Iterator, Mapping
from contextlib import ExitStack
from typing import AbstractSet, Any, Callable, Final, Optional, cast  # noqa: UP035

import sqlalchemy as db
import sqlalchemy.exc as db_exc
from sqlalchemy.engine import Connection
from tqdm import tqdm
from typing_extensions import TypeAlias

import dagster._check as check
from dagster._core.execution.backfill import BULK_ACTION_TERMINAL_STATUSES, PartitionBackfill
from dagster._core.storage.dagster_run import DagsterRun, DagsterRunStatus, RunRecord, RunsFilter
from dagster._core.storage.runs.base import RunStorage
from dagster._core.storage.runs.schema import (
    BackfillTagsTable,
    BulkActionsTable,
    RunsTable,
    RunTagsTable,
)
from dagster._core.storage.sqlalchemy_compat import db_select
from dagster._core.storage.tags import (
    BACKFILL_ID_TAG,
    PARTITION_NAME_TAG,
    PARTITION_SET_TAG,
    REPOSITORY_LABEL_TAG,
)
from dagster._serdes import deserialize_value

RUN_PARTITIONS = "run_partitions"
RUN_START_END = (  # was run_start_end, but renamed to overwrite bad timestamps written
    "run_start_end_overwritten"
)
RUN_REPO_LABEL_TAGS = "run_repo_label_tags"
BULK_ACTION_TYPES = "bulk_action_types"
RUN_BACKFILL_ID = "run_backfill_id"
BACKFILL_JOB_NAME_AND_TAGS = "backfill_job_name_and_tags"
BACKFILL_END_TIMESTAMP = "backfill_end_timestamp"

PrintFn: TypeAlias = Callable[[Any], None]
MigrationFn: TypeAlias = Callable[[RunStorage, Optional[PrintFn]], None]

# for `dagster instance migrate`, paired with schema changes
REQUIRED_DATA_MIGRATIONS: Final[Mapping[str, Callable[[], MigrationFn]]] = {
    RUN_PARTITIONS: lambda: migrate_run_partition,
    RUN_REPO_LABEL_TAGS: lambda: migrate_run_repo_tags,
    BULK_ACTION_TYPES: lambda: migrate_bulk_actions,
    RUN_BACKFILL_ID: lambda: migrate_run_backfill_id,
    BACKFILL_JOB_NAME_AND_TAGS: lambda: migrate_backfill_job_name_and_tags,
    BACKFILL_END_TIMESTAMP: lambda: migrate_backfill_end_timestamp,
}
# for `dagster instance reindex`, optionally run for better read performance
OPTIONAL_DATA_MIGRATIONS: Final[Mapping[str, Callable[[], MigrationFn]]] = {
    RUN_START_END: lambda: migrate_run_start_end,
}

CHUNK_SIZE = 100

UNSTARTED_RUN_STATUSES: Final[AbstractSet[DagsterRunStatus]] = {
    DagsterRunStatus.QUEUED,
    DagsterRunStatus.NOT_STARTED,
    DagsterRunStatus.MANAGED,
    DagsterRunStatus.STARTING,
}


def chunked_run_iterator(
    storage: RunStorage, print_fn: Optional[PrintFn] = None, chunk_size: int = CHUNK_SIZE
) -> Iterator[DagsterRun]:
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
                progress.update(len(chunk))


def chunked_run_records_iterator(
    storage: RunStorage, print_fn: Optional[PrintFn] = None, chunk_size: int = CHUNK_SIZE
) -> Iterator[RunRecord]:
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
                cursor = run.dagster_run.run_id
                yield run

            if progress:
                progress.update(len(chunk))


def chunked_backfill_iterator(
    storage: RunStorage, print_fn: Optional[PrintFn] = None, chunk_size: int = CHUNK_SIZE
) -> Iterator[PartitionBackfill]:
    with ExitStack() as stack:
        if print_fn:
            backfill_count = storage.get_backfills_count()
            progress = stack.enter_context(tqdm(total=backfill_count))
        else:
            progress = None

        cursor = None
        has_more = True

        while has_more:
            chunk = storage.get_backfills(cursor=cursor, limit=chunk_size)
            has_more = chunk_size and len(chunk) >= chunk_size

            for backfill in chunk:
                cursor = backfill.backfill_id
                yield backfill

            if progress:
                progress.update(len(chunk))


def migrate_run_partition(storage: RunStorage, print_fn: Optional[PrintFn] = None) -> None:
    """Utility method to build an asset key index from the data in existing event log records.
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


def migrate_run_start_end(storage: RunStorage, print_fn: Optional[PrintFn] = None) -> None:
    """Utility method that updates the start and end times of historical runs using the completed event log."""
    if print_fn:
        print_fn("Querying run and event log storage.")

    for run_record in chunked_run_records_iterator(storage, print_fn):
        if run_record.dagster_run.status in UNSTARTED_RUN_STATUSES:
            continue

        # commented out here to ensure that previously written timestamps that may not have
        # standardized to UTC would get overwritten
        # if run_record.start_time:
        #     continue

        add_run_stats(storage, run_record.dagster_run.run_id)


def add_run_stats(run_storage: RunStorage, run_id: str) -> None:
    from dagster._core.instance import DagsterInstance
    from dagster._core.storage.runs.sql_run_storage import SqlRunStorage

    check.str_param(run_id, "run_id")
    check.inst_param(run_storage, "run_storage", RunStorage)

    if not isinstance(run_storage, SqlRunStorage):
        return

    instance = check.inst_param(run_storage._instance, "instance", DagsterInstance)  # noqa: SLF001
    run_stats = instance.get_run_stats(run_id)

    with run_storage.connect() as conn:
        conn.execute(
            RunsTable.update()
            .where(RunsTable.c.run_id == run_id)
            .values(
                start_time=run_stats.start_time,
                end_time=run_stats.end_time,
            )
        )


def migrate_run_repo_tags(run_storage: RunStorage, print_fn: Optional[PrintFn] = None) -> None:
    from dagster._core.storage.runs.sql_run_storage import SqlRunStorage

    if not isinstance(run_storage, SqlRunStorage):
        return

    if print_fn:
        print_fn("Querying run storage.")

    subquery = (
        db_select([RunTagsTable.c.run_id.label("tags_run_id")])
        .where(RunTagsTable.c.key == REPOSITORY_LABEL_TAG)
        .alias("tag_subquery")
    )
    base_query = (
        db_select([RunsTable.c.run_body, RunsTable.c.id])
        .select_from(
            RunsTable.join(subquery, RunsTable.c.run_id == subquery.c.tags_run_id, isouter=True)
        )
        .where(subquery.c.tags_run_id.is_(None))
        .order_by(db.asc(RunsTable.c.id))
        .limit(CHUNK_SIZE)
    )

    cursor = None
    has_more = True
    while has_more:
        if cursor:
            query = base_query.where(RunsTable.c.id > cursor)
        else:
            query = base_query

        with run_storage.connect() as conn:
            result_proxy = conn.execute(query)
            rows = result_proxy.fetchall()
            result_proxy.close()

            has_more = len(rows) >= CHUNK_SIZE
            for row in rows:
                run = deserialize_value(cast("str", row[0]), DagsterRun)
                cursor = row[1]
                write_repo_tag(conn, run)


def write_repo_tag(conn: Connection, run: DagsterRun) -> None:
    if not run.remote_job_origin:
        # nothing to do
        return

    repository_label = run.remote_job_origin.repository_origin.get_label()
    try:
        conn.execute(
            RunTagsTable.insert().values(
                run_id=run.run_id,
                key=REPOSITORY_LABEL_TAG,
                value=repository_label,
            )
        )
    except db_exc.IntegrityError:
        # tag already exists, swallow
        pass


def migrate_bulk_actions(run_storage: RunStorage, print_fn: Optional[PrintFn] = None) -> None:
    from dagster._core.storage.runs.sql_run_storage import SqlRunStorage

    if not isinstance(run_storage, SqlRunStorage):
        return

    if print_fn:
        print_fn("Querying run storage.")

    base_query = (
        db_select([BulkActionsTable.c.body, BulkActionsTable.c.id])
        .where(BulkActionsTable.c.action_type.is_(None))
        .order_by(db.asc(BulkActionsTable.c.id))
        .limit(CHUNK_SIZE)
    )

    cursor = None
    has_more = True
    while has_more:
        if cursor:
            query = base_query.where(BulkActionsTable.c.id > cursor)
        else:
            query = base_query

        with run_storage.connect() as conn:
            result_proxy = conn.execute(query)
            rows = result_proxy.fetchall()
            result_proxy.close()

            has_more = len(rows) >= CHUNK_SIZE
            for row in rows:
                backfill = deserialize_value(row[0], PartitionBackfill)  # type: ignore  # (pyright bug)
                storage_id = row[1]
                conn.execute(
                    BulkActionsTable.update()
                    .values(
                        selector_id=backfill.selector_id,
                        action_type=backfill.bulk_action_type.value,
                    )
                    .where(BulkActionsTable.c.id == storage_id)
                )
                cursor = storage_id


def migrate_run_backfill_id(storage: RunStorage, print_fn: Optional[PrintFn] = None) -> None:
    """Utility method to add a backfill_id column to the runs table and populate it with the backfill_id of the run."""
    from dagster._core.storage.runs.sql_run_storage import SqlRunStorage

    if print_fn:
        print_fn("Querying run storage.")

    check.inst_param(storage, "run_storage", RunStorage)

    if not isinstance(storage, SqlRunStorage):
        return

    with storage.connect() as conn:
        cursor = None
        has_more = True
        base_query = (
            db_select([RunTagsTable.c.id, RunTagsTable.c.run_id, RunTagsTable.c.value])
            .where(RunTagsTable.c.key == BACKFILL_ID_TAG)
            .limit(CHUNK_SIZE)
            .order_by(RunTagsTable.c.id)
        )

        while has_more:
            if cursor:
                query = base_query.where(RunTagsTable.c.id > cursor)
            else:
                query = base_query
            res = storage.fetchall(query)
            has_more = len(res) >= CHUNK_SIZE
            for row in res:
                cursor = row["id"]
                run_id = row["run_id"]
                backfill_id = row["value"]

                add_backfill_id(conn, run_id=run_id, backfill_id=backfill_id)


def add_backfill_id(conn, run_id: str, backfill_id: str) -> None:
    check.str_param(run_id, "run_id")
    check.str_param(backfill_id, "backfill_id")
    conn.execute(
        RunsTable.update()
        .where(RunsTable.c.run_id == run_id)
        .where(RunsTable.c.backfill_id.is_(None))
        .values(
            backfill_id=backfill_id,
        )
    )


def migrate_backfill_job_name_and_tags(
    storage: RunStorage, print_fn: Optional[PrintFn] = None
) -> None:
    """Utility method to add a backfill's job_name to the bulk_actions table and tags to the backfill_tags table."""
    if print_fn:
        print_fn("Querying run storage.")

    for backfill in chunked_backfill_iterator(storage, print_fn):
        if backfill.tags:
            add_backfill_tags(
                run_storage=storage, backfill_id=backfill.backfill_id, tags=backfill.tags
            )

        if backfill.job_name is not None:
            add_backfill_job_name(
                run_storage=storage, backfill_id=backfill.backfill_id, job_name=backfill.job_name
            )


def add_backfill_tags(run_storage: RunStorage, backfill_id: str, tags: Mapping[str, str]):
    from dagster._core.storage.runs.sql_run_storage import SqlRunStorage

    check.str_param(backfill_id, "run_id")
    check.dict_param(tags, "tags", key_type=str, value_type=str)
    check.inst_param(run_storage, "run_storage", RunStorage)

    if not isinstance(run_storage, SqlRunStorage):
        return

    with run_storage.connect() as conn:
        conn.execute(
            BackfillTagsTable.insert(),
            [
                dict(
                    backfill_id=backfill_id,
                    key=k,
                    value=v,
                )
                for k, v in tags.items()
            ],
        )


def add_backfill_job_name(run_storage: RunStorage, backfill_id: str, job_name: str):
    from dagster._core.storage.runs.sql_run_storage import SqlRunStorage

    check.str_param(backfill_id, "run_id")
    check.str_param(job_name, "job_name")
    check.inst_param(run_storage, "run_storage", RunStorage)

    if not isinstance(run_storage, SqlRunStorage):
        return

    with run_storage.connect() as conn:
        conn.execute(
            BulkActionsTable.update()
            .values(
                job_name=job_name,
            )
            .where(BulkActionsTable.c.key == backfill_id)
        )


def migrate_backfill_end_timestamp(storage: RunStorage, print_fn: Optional[PrintFn] = None) -> None:
    """Utility method to add a backfill's end timestamp to the serialized backfill stored in the bulk actions table."""
    if print_fn:
        print_fn("Querying run storage.")

    for backfill in chunked_backfill_iterator(storage, print_fn):
        if backfill.status not in BULK_ACTION_TERMINAL_STATUSES:
            # we don't want to mutate a backfill that is still in progress. Additionally, it won't
            # have an end timestamp until it moves to a terminal state
            continue
        if backfill.backfill_end_timestamp is None:
            end_time = get_end_timestamp_for_backfill(storage, backfill)
            updated_backfill = backfill.with_end_timestamp(end_time)
            storage.update_backfill(updated_backfill)


def get_end_timestamp_for_backfill(run_storage: RunStorage, backfill: PartitionBackfill) -> float:
    assert backfill.status in BULK_ACTION_TERMINAL_STATUSES
    filters = RunsFilter.for_backfill(backfill.backfill_id)
    run_records = run_storage.get_run_records(filters=filters)
    if len(run_records) == 0:
        # backfill was moved to a terminal state before any runs were launched. We cannot
        # reconstruct the time the backfill actually moved to a terminal state, so use the start
        # time as an estimation
        return backfill.backfill_timestamp
    return max([record.end_time or 0.0 for record in run_records])
