import logging
import uuid
import zlib
from abc import abstractmethod
from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from datetime import datetime
from enum import Enum
from typing import Any, Callable, ContextManager, NamedTuple, Optional, Union, cast  # noqa: UP035

import sqlalchemy as db
import sqlalchemy.exc as db_exc
from dagster_shared.serdes import deserialize_values
from dagster_shared.seven import JSONDecodeError
from sqlalchemy.engine import Connection

import dagster._check as check
from dagster._core.errors import (
    DagsterInvariantViolationError,
    DagsterRunAlreadyExists,
    DagsterRunNotFoundError,
    DagsterSnapshotDoesNotExist,
)
from dagster._core.events import (
    EVENT_TYPE_TO_PIPELINE_RUN_STATUS,
    DagsterEvent,
    DagsterEventType,
    RunFailureReason,
)
from dagster._core.execution.backfill import BulkActionsFilter, BulkActionStatus, PartitionBackfill
from dagster._core.remote_origin import RemoteJobOrigin
from dagster._core.snap import ExecutionPlanSnapshot, JobSnap, create_execution_plan_snapshot_id
from dagster._core.storage.dagster_run import (
    DagsterRun,
    DagsterRunStatus,
    JobBucket,
    RunPartitionData,
    RunRecord,
    RunsFilter,
    TagBucket,
)
from dagster._core.storage.runs.base import RunStorage
from dagster._core.storage.runs.migration import (
    BACKFILL_JOB_NAME_AND_TAGS,
    OPTIONAL_DATA_MIGRATIONS,
    REQUIRED_DATA_MIGRATIONS,
    RUN_BACKFILL_ID,
    RUN_PARTITIONS,
    MigrationFn,
)
from dagster._core.storage.runs.schema import (
    BackfillTagsTable,
    BulkActionsTable,
    DaemonHeartbeatsTable,
    InstanceInfo,
    KeyValueStoreTable,
    RunsTable,
    RunTagsTable,
    SecondaryIndexMigrationTable,
    SnapshotsTable,
)
from dagster._core.storage.sql import SqlAlchemyQuery
from dagster._core.storage.sqlalchemy_compat import (
    db_fetch_mappings,
    db_scalar_subquery,
    db_select,
    db_subquery,
)
from dagster._core.storage.tags import (
    BACKFILL_ID_TAG,
    PARTITION_NAME_TAG,
    PARTITION_SET_TAG,
    REPOSITORY_LABEL_TAG,
    ROOT_RUN_ID_TAG,
    RUN_FAILURE_REASON_TAG,
)
from dagster._daemon.types import DaemonHeartbeat
from dagster._serdes import deserialize_value, serialize_value
from dagster._time import datetime_from_timestamp, get_current_datetime, utc_datetime_from_naive
from dagster._utils import PrintFn
from dagster._utils.merger import merge_dicts


class SnapshotType(Enum):
    PIPELINE = "PIPELINE"
    EXECUTION_PLAN = "EXECUTION_PLAN"


class SqlRunStorage(RunStorage):
    """Base class for SQL based run storages."""

    @abstractmethod
    def connect(self) -> ContextManager[Connection]:
        """Context manager yielding a sqlalchemy.engine.Connection."""

    @abstractmethod
    def upgrade(self) -> None:
        """This method should perform any schema or data migrations necessary to bring an
        out-of-date instance of the storage up to date.
        """

    def fetchall(self, query: SqlAlchemyQuery) -> Sequence[Any]:
        with self.connect() as conn:
            return db_fetch_mappings(conn, query)

    def fetchone(self, query: SqlAlchemyQuery) -> Optional[Any]:
        with self.connect() as conn:
            if db.__version__.startswith("2."):
                return conn.execute(query).mappings().first()
            else:
                return conn.execute(query).fetchone()

    def _get_run_insertion_values(
        self, dagster_run: DagsterRun, run_creation_time: Optional[datetime] = None
    ) -> dict[str, Any]:
        check.inst_param(dagster_run, "dagster_run", DagsterRun)

        if dagster_run.job_snapshot_id and not self.has_job_snapshot(dagster_run.job_snapshot_id):
            raise DagsterSnapshotDoesNotExist(
                f"Snapshot {dagster_run.job_snapshot_id} does not exist in run storage"
            )

        has_tags = dagster_run.tags and len(dagster_run.tags) > 0
        partition = dagster_run.tags.get(PARTITION_NAME_TAG) if has_tags else None
        partition_set = dagster_run.tags.get(PARTITION_SET_TAG) if has_tags else None
        values = {
            "run_id": dagster_run.run_id,
            "pipeline_name": dagster_run.job_name,
            "status": dagster_run.status.value,
            "run_body": serialize_value(dagster_run),
            "snapshot_id": dagster_run.job_snapshot_id,
            "partition": partition,
            "partition_set": partition_set,
        }
        if self.has_backfill_id_column():
            values["backfill_id"] = dagster_run.tags.get(BACKFILL_ID_TAG)
        if run_creation_time:
            values["create_timestamp"] = run_creation_time
        return values

    def _core_add_run(self, col_values: dict[str, Any], tags: Mapping[str, str]) -> None:
        run_id = col_values["run_id"]
        runs_insert = RunsTable.insert().values(**col_values)
        with self.connect() as conn:
            try:
                conn.execute(runs_insert)
            except db_exc.IntegrityError as exc:
                raise DagsterRunAlreadyExists from exc

            if tags:
                conn.execute(
                    RunTagsTable.insert(),
                    [dict(run_id=run_id, key=k, value=v) for k, v in tags.items()],
                )

    def add_run(self, dagster_run: DagsterRun) -> DagsterRun:
        self._core_add_run(
            self._get_run_insertion_values(dagster_run, get_current_datetime()),
            dagster_run.tags_for_storage(),
        )
        return dagster_run

    def add_historical_run(
        self, dagster_run: DagsterRun, run_creation_time: datetime
    ) -> DagsterRun:
        self._core_add_run(
            self._get_run_insertion_values(dagster_run, run_creation_time),
            dagster_run.tags_for_storage(),
        )
        return dagster_run

    def handle_run_event(
        self, run_id: str, event: DagsterEvent, update_timestamp: Optional[datetime] = None
    ) -> None:
        from dagster._core.events import JobFailureData

        check.str_param(run_id, "run_id")
        check.inst_param(event, "event", DagsterEvent)

        if event.event_type not in EVENT_TYPE_TO_PIPELINE_RUN_STATUS:
            return

        run = self._get_run_by_id(run_id)
        if not run:
            # TODO log?
            return

        new_job_status = EVENT_TYPE_TO_PIPELINE_RUN_STATUS[event.event_type]

        run_stats_cols_in_index = self.has_run_stats_index_cols()

        kwargs = {}

        # Update timestamp represents the time that the event occurred, not the time at which
        # we're processing the event in the run storage. But we fall back to the current time.
        # This is specific to the open-source implementation.
        update_timestamp = update_timestamp or get_current_datetime()

        if run_stats_cols_in_index and event.event_type == DagsterEventType.PIPELINE_START:
            kwargs["start_time"] = update_timestamp.timestamp()

        if run_stats_cols_in_index and event.event_type in {
            DagsterEventType.PIPELINE_CANCELED,
            DagsterEventType.PIPELINE_FAILURE,
            DagsterEventType.PIPELINE_SUCCESS,
        }:
            kwargs["end_time"] = update_timestamp.timestamp()

        with self.connect() as conn:
            conn.execute(
                RunsTable.update()
                .where(RunsTable.c.run_id == run_id)
                .values(
                    run_body=serialize_value(run.with_status(new_job_status)),
                    status=new_job_status.value,
                    update_timestamp=update_timestamp,
                    **kwargs,
                )
            )

        if event.event_type == DagsterEventType.PIPELINE_FAILURE and isinstance(
            event.event_specific_data, JobFailureData
        ):
            failure_reason = event.event_specific_data.failure_reason

            if failure_reason and failure_reason != RunFailureReason.UNKNOWN:
                self.add_run_tags(run_id, {RUN_FAILURE_REASON_TAG: failure_reason.value})

    def _row_to_run(self, row: dict) -> DagsterRun:
        run = deserialize_value(row["run_body"], DagsterRun)
        status = DagsterRunStatus(row["status"])
        # NOTE: the status column is more trustworthy than the status in the run body, since concurrent
        # writes (e.g.  handle_run_event and add_tags) can cause the status in the body to be out of
        # overriden with an old value.
        return run.with_status(status)

    def _rows_to_runs(self, rows: Iterable[dict]) -> Sequence[DagsterRun]:
        return list(map(self._row_to_run, rows))

    def _add_cursor_limit_to_query(
        self,
        query: SqlAlchemyQuery,
        cursor: Optional[str],
        limit: Optional[int],
        order_by: Optional[str],
        ascending: Optional[bool],
    ) -> SqlAlchemyQuery:
        """Helper function to deal with cursor/limit pagination args."""
        if cursor:
            cursor_query = db_select([RunsTable.c.id]).where(RunsTable.c.run_id == cursor)
            if ascending:
                query = query.where(RunsTable.c.id > db_scalar_subquery(cursor_query))
            else:
                query = query.where(RunsTable.c.id < db_scalar_subquery(cursor_query))

        if limit:
            query = query.limit(limit)

        sorting_column = getattr(RunsTable.c, order_by) if order_by else RunsTable.c.id
        direction = db.asc if ascending else db.desc
        query = query.order_by(direction(sorting_column))

        return query

    def _add_filters_to_table(self, table: db.Table, filters: RunsFilter) -> db.Table:
        if filters.tags:
            table = self._apply_tags_table_filters(table, filters.tags)

        return table

    def _add_filters_to_query(self, query: SqlAlchemyQuery, filters: RunsFilter) -> SqlAlchemyQuery:
        check.inst_param(filters, "filters", RunsFilter)

        if filters.run_ids:
            query = query.where(RunsTable.c.run_id.in_(filters.run_ids))

        if filters.job_name:
            query = query.where(RunsTable.c.pipeline_name == filters.job_name)

        if filters.statuses:
            query = query.where(
                RunsTable.c.status.in_([status.value for status in filters.statuses])
            )

        if filters.snapshot_id:
            query = query.where(RunsTable.c.snapshot_id == filters.snapshot_id)

        if filters.updated_after:
            query = query.where(
                RunsTable.c.update_timestamp > filters.updated_after.replace(tzinfo=None)
            )

        if filters.updated_before:
            query = query.where(
                RunsTable.c.update_timestamp < filters.updated_before.replace(tzinfo=None)
            )

        if filters.created_after:
            query = query.where(
                RunsTable.c.create_timestamp > filters.created_after.replace(tzinfo=None)
            )

        if filters.created_before:
            query = query.where(
                RunsTable.c.create_timestamp < filters.created_before.replace(tzinfo=None)
            )

        if filters.exclude_subruns:
            if self.has_built_index(RUN_BACKFILL_ID):
                query = query.where(RunsTable.c.backfill_id.is_(None))
            else:
                runs_in_backfills = db_select([RunTagsTable.c.run_id]).where(
                    RunTagsTable.c.key == BACKFILL_ID_TAG
                )
                query = query.where(RunsTable.c.run_id.notin_(runs_in_backfills))

        return query

    def _runs_query(
        self,
        filters: Optional[RunsFilter] = None,
        cursor: Optional[str] = None,
        limit: Optional[int] = None,
        columns: Optional[Sequence[str]] = None,
        order_by: Optional[str] = None,
        ascending: bool = False,
        bucket_by: Optional[Union[JobBucket, TagBucket]] = None,
    ) -> SqlAlchemyQuery:
        filters = check.opt_inst_param(filters, "filters", RunsFilter, default=RunsFilter())
        check.opt_str_param(cursor, "cursor")
        check.opt_int_param(limit, "limit")
        check.opt_sequence_param(columns, "columns")
        check.opt_str_param(order_by, "order_by")
        check.opt_bool_param(ascending, "ascending")

        if columns is None:
            columns = ["run_body", "status"]

        table = self._add_filters_to_table(RunsTable, filters)
        base_query = db_select([getattr(RunsTable.c, column) for column in columns]).select_from(
            table
        )
        base_query = self._add_filters_to_query(base_query, filters)
        return self._add_cursor_limit_to_query(base_query, cursor, limit, order_by, ascending)

    def _apply_tags_table_filters(
        self, table: db.Table, tags: Mapping[str, Union[str, Sequence[str]]]
    ) -> SqlAlchemyQuery:
        """Efficient query pattern for filtering by multiple tags."""
        for i, (key, value) in enumerate(tags.items()):
            run_tags_alias = db.alias(RunTagsTable, f"run_tags_filter{i}")

            table = table.join(
                run_tags_alias,
                db.and_(
                    RunsTable.c.run_id == run_tags_alias.c.run_id,
                    run_tags_alias.c.key == key,
                    (run_tags_alias.c.value == value)
                    if isinstance(value, str)
                    else run_tags_alias.c.value.in_(value),
                ),
            )

        return table

    def get_runs(
        self,
        filters: Optional[RunsFilter] = None,
        cursor: Optional[str] = None,
        limit: Optional[int] = None,
        bucket_by: Optional[Union[JobBucket, TagBucket]] = None,
        ascending: bool = False,
    ) -> Sequence[DagsterRun]:
        query = self._runs_query(filters, cursor, limit, bucket_by=bucket_by, ascending=ascending)
        rows = self.fetchall(query)
        return self._rows_to_runs(rows)

    def get_run_ids(
        self,
        filters: Optional[RunsFilter] = None,
        cursor: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> Sequence[str]:
        query = self._runs_query(filters=filters, cursor=cursor, limit=limit, columns=["run_id"])
        rows = self.fetchall(query)
        return [row["run_id"] for row in rows]

    def get_runs_count(self, filters: Optional[RunsFilter] = None) -> int:
        subquery = db_subquery(self._runs_query(filters=filters))
        query = db_select([db.func.count().label("count")]).select_from(subquery)
        row = self.fetchone(query)
        count = row["count"] if row else 0
        return count

    def _get_run_by_id(self, run_id: str) -> Optional[DagsterRun]:
        check.str_param(run_id, "run_id")

        query = db_select([RunsTable.c.run_body, RunsTable.c.status]).where(
            RunsTable.c.run_id == run_id
        )
        rows = self.fetchall(query)
        return self._row_to_run(rows[0]) if rows else None

    def get_run_records(
        self,
        filters: Optional[RunsFilter] = None,
        limit: Optional[int] = None,
        order_by: Optional[str] = None,
        ascending: bool = False,
        cursor: Optional[str] = None,
        bucket_by: Optional[Union[JobBucket, TagBucket]] = None,
    ) -> Sequence[RunRecord]:
        filters = check.opt_inst_param(filters, "filters", RunsFilter, default=RunsFilter())
        check.opt_int_param(limit, "limit")

        columns = ["id", "run_body", "status", "create_timestamp", "update_timestamp"]

        if self.has_run_stats_index_cols():
            columns += ["start_time", "end_time"]
        # only fetch columns we use to build RunRecord
        query = self._runs_query(
            filters=filters,
            limit=limit,
            columns=columns,
            order_by=order_by,
            ascending=ascending,
            cursor=cursor,
            bucket_by=bucket_by,
        )

        rows = self.fetchall(query)
        return [
            RunRecord(
                storage_id=check.int_param(row["id"], "id"),
                dagster_run=self._row_to_run(row),
                create_timestamp=utc_datetime_from_naive(
                    check.inst(row["create_timestamp"], datetime)
                ),
                update_timestamp=utc_datetime_from_naive(
                    check.inst(row["update_timestamp"], datetime)
                ),
                start_time=(
                    check.opt_inst(row["start_time"], float) if "start_time" in row else None
                ),
                end_time=check.opt_inst(row["end_time"], float) if "end_time" in row else None,
            )
            for row in rows
        ]

    def get_run_tags(
        self,
        tag_keys: Sequence[str],
        value_prefix: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> Sequence[tuple[str, set[str]]]:
        result = defaultdict(set)
        query = (
            db_select([RunTagsTable.c.key, RunTagsTable.c.value])
            .distinct()
            .order_by(RunTagsTable.c.key, RunTagsTable.c.value)
            .where(RunTagsTable.c.key.in_(tag_keys))
        )
        if value_prefix:
            query = query.where(RunTagsTable.c.value.startswith(value_prefix))
        if limit:
            query = query.limit(limit)
        rows = self.fetchall(query)
        for r in rows:
            result[r["key"]].add(r["value"])
        return sorted(list([(k, v) for k, v in result.items()]), key=lambda x: x[0])

    def get_run_tag_keys(self) -> Sequence[str]:
        query = db_select([RunTagsTable.c.key]).distinct().order_by(RunTagsTable.c.key)
        rows = self.fetchall(query)
        return sorted([r["key"] for r in rows])

    def add_run_tags(self, run_id: str, new_tags: Mapping[str, str]) -> None:
        check.str_param(run_id, "run_id")
        check.mapping_param(new_tags, "new_tags", key_type=str, value_type=str)

        run = self._get_run_by_id(run_id)
        if not run:
            raise DagsterRunNotFoundError(
                f"Run {run_id} was not found in instance.", invalid_run_id=run_id
            )
        current_tags = run.tags if run.tags else {}

        all_tags = merge_dicts(current_tags, new_tags)
        partition = all_tags.get(PARTITION_NAME_TAG)
        partition_set = all_tags.get(PARTITION_SET_TAG)

        with self.connect() as conn:
            conn.execute(
                RunsTable.update()
                .where(RunsTable.c.run_id == run_id)
                .values(
                    run_body=serialize_value(run.with_tags(merge_dicts(current_tags, new_tags))),
                    partition=partition,
                    partition_set=partition_set,
                    update_timestamp=get_current_datetime(),
                )
            )

            current_tags_set = set(current_tags.keys())
            new_tags_set = set(new_tags.keys())

            existing_tags = current_tags_set & new_tags_set
            added_tags = new_tags_set.difference(existing_tags)

            for tag in existing_tags:
                conn.execute(
                    RunTagsTable.update()
                    .where(db.and_(RunTagsTable.c.run_id == run_id, RunTagsTable.c.key == tag))
                    .values(value=new_tags[tag])
                )

            if added_tags:
                conn.execute(
                    RunTagsTable.insert(),
                    [dict(run_id=run_id, key=tag, value=new_tags[tag]) for tag in added_tags],
                )

    def get_run_group(self, run_id: str) -> tuple[str, Sequence[DagsterRun]]:
        check.str_param(run_id, "run_id")
        dagster_run = self._get_run_by_id(run_id)
        if not dagster_run:
            raise DagsterRunNotFoundError(
                f"Run {run_id} was not found in instance.", invalid_run_id=run_id
            )

        # find root_run
        root_run_id = dagster_run.root_run_id if dagster_run.root_run_id else dagster_run.run_id
        root_run = self._get_run_by_id(root_run_id)
        if not root_run:
            raise DagsterRunNotFoundError(
                f"Run id {root_run_id} set as root run id for run {run_id} was not found in"
                " instance.",
                invalid_run_id=root_run_id,
            )

        # root_run_id to run_id 1:1 mapping
        # https://github.com/dagster-io/dagster/issues/2495
        # Note: we currently use tags to persist the run group info
        root_to_run = db_subquery(
            db_select(
                [RunTagsTable.c.value.label("root_run_id"), RunTagsTable.c.run_id.label("run_id")]
            ).where(
                db.and_(RunTagsTable.c.key == ROOT_RUN_ID_TAG, RunTagsTable.c.value == root_run_id)
            ),
            "root_to_run",
        )
        # get run group
        run_group_query = db_select([RunsTable.c.run_body, RunsTable.c.status]).select_from(
            root_to_run.join(
                RunsTable,
                root_to_run.c.run_id == RunsTable.c.run_id,
                isouter=True,
            )
        )

        res = self.fetchall(run_group_query)
        run_group = self._rows_to_runs(res)

        return (root_run_id, [root_run, *run_group])

    def has_run(self, run_id: str) -> bool:
        check.str_param(run_id, "run_id")
        return bool(self._get_run_by_id(run_id))

    def delete_run(self, run_id: str) -> None:
        check.str_param(run_id, "run_id")
        query = db.delete(RunsTable).where(RunsTable.c.run_id == run_id)
        with self.connect() as conn:
            conn.execute(query)

    def has_job_snapshot(self, job_snapshot_id: str) -> bool:
        check.str_param(job_snapshot_id, "job_snapshot_id")
        return self._has_snapshot_id(job_snapshot_id)

    def add_job_snapshot(self, job_snapshot: JobSnap) -> str:
        check.inst_param(job_snapshot, "job_snapshot", JobSnap)

        snapshot_id = job_snapshot.snapshot_id

        return self._add_snapshot(
            snapshot_id=snapshot_id,
            snapshot_obj=job_snapshot,
            snapshot_type=SnapshotType.PIPELINE,
        )

    def get_job_snapshot(self, job_snapshot_id: str) -> JobSnap:
        check.str_param(job_snapshot_id, "job_snapshot_id")
        return self._get_snapshot(job_snapshot_id)  # type: ignore  # (allowed to return None?)

    def has_execution_plan_snapshot(self, execution_plan_snapshot_id: str) -> bool:
        check.str_param(execution_plan_snapshot_id, "execution_plan_snapshot_id")
        return bool(self.get_execution_plan_snapshot(execution_plan_snapshot_id))

    def add_execution_plan_snapshot(
        self,
        execution_plan_snapshot: ExecutionPlanSnapshot,
    ) -> str:
        check.inst_param(execution_plan_snapshot, "execution_plan_snapshot", ExecutionPlanSnapshot)

        snapshot_id = create_execution_plan_snapshot_id(execution_plan_snapshot)

        return self._add_snapshot(
            snapshot_id=snapshot_id,
            snapshot_obj=execution_plan_snapshot,
            snapshot_type=SnapshotType.EXECUTION_PLAN,
        )

    def get_execution_plan_snapshot(self, execution_plan_snapshot_id: str) -> ExecutionPlanSnapshot:
        check.str_param(execution_plan_snapshot_id, "execution_plan_snapshot_id")
        return self._get_snapshot(execution_plan_snapshot_id)  # type: ignore  # (allowed to return None?)

    def _add_snapshot(self, snapshot_id: str, snapshot_obj, snapshot_type: SnapshotType) -> str:
        check.str_param(snapshot_id, "snapshot_id")
        check.not_none_param(snapshot_obj, "snapshot_obj")
        check.inst_param(snapshot_type, "snapshot_type", SnapshotType)

        with self.connect() as conn:
            snapshot_insert = SnapshotsTable.insert().values(
                snapshot_id=snapshot_id,
                snapshot_body=zlib.compress(serialize_value(snapshot_obj).encode("utf-8")),
                snapshot_type=snapshot_type.value,
            )
            try:
                conn.execute(snapshot_insert)
            except db_exc.IntegrityError:
                # on_conflict_do_nothing equivalent
                pass

            return snapshot_id

    def get_run_storage_id(self) -> str:
        query = db_select([InstanceInfo.c.run_storage_id])
        row = self.fetchone(query)
        if not row:
            run_storage_id = str(uuid.uuid4())
            with self.connect() as conn:
                conn.execute(InstanceInfo.insert().values(run_storage_id=run_storage_id))
            return run_storage_id
        else:
            return row["run_storage_id"]

    def _has_snapshot_id(self, snapshot_id: str) -> bool:
        query = db_select([SnapshotsTable.c.snapshot_id]).where(
            SnapshotsTable.c.snapshot_id == snapshot_id
        )

        row = self.fetchone(query)

        return bool(row)

    def _get_snapshot(self, snapshot_id: str) -> Optional[JobSnap]:
        query = db_select([SnapshotsTable.c.snapshot_body]).where(
            SnapshotsTable.c.snapshot_id == snapshot_id
        )

        row = self.fetchone(query)

        return (
            defensively_unpack_execution_plan_snapshot_query(logging, [row["snapshot_body"]])  # type: ignore
            if row
            else None
        )

    def get_run_partition_data(self, runs_filter: RunsFilter) -> Sequence[RunPartitionData]:
        if self.has_built_index(RUN_PARTITIONS) and self.has_run_stats_index_cols():
            query = self._runs_query(
                filters=runs_filter,
                columns=["run_id", "status", "start_time", "end_time", "partition"],
            )
            rows = self.fetchall(query)

            # dedup by partition
            _partition_data_by_partition = {}
            for row in rows:
                if not row["partition"] or row["partition"] in _partition_data_by_partition:
                    continue

                _partition_data_by_partition[row["partition"]] = RunPartitionData(
                    run_id=row["run_id"],
                    partition=row["partition"],
                    status=DagsterRunStatus[row["status"]],
                    start_time=row["start_time"],
                    end_time=row["end_time"],
                )

            return list(_partition_data_by_partition.values())
        else:
            query = self._runs_query(filters=runs_filter)
            rows = self.fetchall(query)
            _partition_data_by_partition = {}
            for row in rows:
                run = self._row_to_run(row)
                partition = run.tags.get(PARTITION_NAME_TAG)
                if not partition or partition in _partition_data_by_partition:
                    continue

                _partition_data_by_partition[partition] = RunPartitionData(
                    run_id=run.run_id,
                    partition=partition,
                    status=run.status,
                    start_time=None,
                    end_time=None,
                )

            return list(_partition_data_by_partition.values())

    def _get_partition_runs(
        self, partition_set_name: str, partition_name: str
    ) -> Sequence[DagsterRun]:
        # utility method to help test reads off of the partition column
        if not self.has_built_index(RUN_PARTITIONS):
            # query by tags
            return self.get_runs(
                filters=RunsFilter(
                    tags={
                        PARTITION_SET_TAG: partition_set_name,
                        PARTITION_NAME_TAG: partition_name,
                    }
                )
            )
        else:
            query = (
                self._runs_query()
                .where(RunsTable.c.partition == partition_name)
                .where(RunsTable.c.partition_set == partition_set_name)
            )
            rows = self.fetchall(query)
            return self._rows_to_runs(rows)

    # Tracking data migrations over secondary indexes

    def _execute_data_migrations(
        self,
        migrations: Mapping[str, Callable[[], MigrationFn]],
        print_fn: Optional[PrintFn] = None,
        force_rebuild_all: bool = False,
    ) -> None:
        for migration_name, migration_fn in migrations.items():
            if self.has_built_index(migration_name):
                if not force_rebuild_all:
                    if print_fn:
                        print_fn(f"Skipping already applied data migration: {migration_name}")
                    continue
            if print_fn:
                print_fn(f"Starting data migration: {migration_name}")
            migration_fn()(self, print_fn)
            self.mark_index_built(migration_name)
            if print_fn:
                print_fn(f"Finished data migration: {migration_name}")

    def migrate(self, print_fn: Optional[PrintFn] = None, force_rebuild_all: bool = False) -> None:
        self._execute_data_migrations(REQUIRED_DATA_MIGRATIONS, print_fn, force_rebuild_all)

    def optimize(self, print_fn: Optional[PrintFn] = None, force_rebuild_all: bool = False) -> None:
        self._execute_data_migrations(OPTIONAL_DATA_MIGRATIONS, print_fn, force_rebuild_all)

    def has_built_index(self, migration_name: str) -> bool:
        query = (
            db_select([1])
            .where(SecondaryIndexMigrationTable.c.name == migration_name)
            .where(SecondaryIndexMigrationTable.c.migration_completed != None)  # noqa: E711
            .limit(1)
        )
        results = self.fetchall(query)

        return len(results) > 0

    def mark_index_built(self, migration_name: str) -> None:
        query = SecondaryIndexMigrationTable.insert().values(
            name=migration_name,
            migration_completed=datetime.now(),
        )
        with self.connect() as conn:
            try:
                conn.execute(query)
            except db_exc.IntegrityError:
                conn.execute(
                    SecondaryIndexMigrationTable.update()
                    .where(SecondaryIndexMigrationTable.c.name == migration_name)
                    .values(migration_completed=datetime.now())
                )

    # Checking for migrations

    def has_run_stats_index_cols(self) -> bool:
        with self.connect() as conn:
            column_names = [x.get("name") for x in db.inspect(conn).get_columns(RunsTable.name)]
            return "start_time" in column_names and "end_time" in column_names

    def has_bulk_actions_selector_cols(self) -> bool:
        with self.connect() as conn:
            column_names = [
                x.get("name") for x in db.inspect(conn).get_columns(BulkActionsTable.name)
            ]
            return "selector_id" in column_names

    def has_backfill_id_column(self) -> bool:
        with self.connect() as conn:
            column_names = [x.get("name") for x in db.inspect(conn).get_columns(RunsTable.name)]
            return "backfill_id" in column_names

    def has_bulk_action_job_name_column(self) -> bool:
        with self.connect() as conn:
            column_names = [
                x.get("name") for x in db.inspect(conn).get_columns(BulkActionsTable.name)
            ]
            return "job_name" in column_names

    def has_backfill_tags_table(self) -> bool:
        with self.connect() as conn:
            return BackfillTagsTable.name in db.inspect(conn).get_table_names()

    # Daemon heartbeats

    def add_daemon_heartbeat(self, daemon_heartbeat: DaemonHeartbeat) -> None:
        with self.connect() as conn:
            # insert, or update if already present
            try:
                conn.execute(
                    DaemonHeartbeatsTable.insert().values(
                        timestamp=datetime_from_timestamp(daemon_heartbeat.timestamp),
                        daemon_type=daemon_heartbeat.daemon_type,
                        daemon_id=daemon_heartbeat.daemon_id,
                        body=serialize_value(daemon_heartbeat),
                    )
                )
            except db_exc.IntegrityError:
                conn.execute(
                    DaemonHeartbeatsTable.update()
                    .where(DaemonHeartbeatsTable.c.daemon_type == daemon_heartbeat.daemon_type)
                    .values(
                        timestamp=datetime_from_timestamp(daemon_heartbeat.timestamp),
                        daemon_id=daemon_heartbeat.daemon_id,
                        body=serialize_value(daemon_heartbeat),
                    )
                )

    def get_daemon_heartbeats(self) -> Mapping[str, DaemonHeartbeat]:
        rows = self.fetchall(db_select([DaemonHeartbeatsTable.c.body]))
        heartbeats = []
        for row in rows:
            heartbeats.append(deserialize_value(row["body"], DaemonHeartbeat))
        return {heartbeat.daemon_type: heartbeat for heartbeat in heartbeats}

    def wipe(self) -> None:
        """Clears the run storage."""
        with self.connect() as conn:
            # https://stackoverflow.com/a/54386260/324449
            conn.execute(RunsTable.delete())
            conn.execute(RunTagsTable.delete())
            conn.execute(SnapshotsTable.delete())
            conn.execute(DaemonHeartbeatsTable.delete())
            conn.execute(BulkActionsTable.delete())

    def wipe_daemon_heartbeats(self) -> None:
        with self.connect() as conn:
            # https://stackoverflow.com/a/54386260/324449
            conn.execute(DaemonHeartbeatsTable.delete())

    def _add_backfill_filters_to_table(
        self, table: db.Table, filters: Optional[BulkActionsFilter]
    ) -> db.Table:
        if filters and filters.tags and self.has_built_index(BACKFILL_JOB_NAME_AND_TAGS):
            for i, (key, value) in enumerate(filters.tags.items()):
                backfill_tags_alias = db.alias(BackfillTagsTable, f"backfill_tags_filter{i}")

                table = table.join(
                    backfill_tags_alias,
                    db.and_(
                        BulkActionsTable.c.key == backfill_tags_alias.c.backfill_id,
                        backfill_tags_alias.c.key == key,
                        (backfill_tags_alias.c.value == value)
                        if isinstance(value, str)
                        else backfill_tags_alias.c.value.in_(value),
                    ),
                )
            return table
        return table

    def _backfills_query(self, filters: Optional[BulkActionsFilter] = None):
        query = db_select([BulkActionsTable.c.body, BulkActionsTable.c.timestamp])
        if filters and filters.tags:
            if not self.has_built_index(BACKFILL_JOB_NAME_AND_TAGS):
                # if the migration was run, we added the query for tags filtering in _add_backfill_filters_to_table
                # BackfillTags table has not been built. However, all tags that are on a backfill are
                # applied to the runs the backfill launches. So we can query for runs that match the tags and
                # are also part of a backfill to find the backfills that match the tags.

                backfills_with_tags_query = db_select([RunTagsTable.c.value]).where(
                    RunTagsTable.c.key == BACKFILL_ID_TAG
                )

                for i, (key, value) in enumerate(filters.tags.items()):
                    run_tags_alias = db.alias(RunTagsTable, f"run_tags_filter{i}")
                    backfills_with_tags_query = backfills_with_tags_query.where(
                        db.and_(
                            RunTagsTable.c.run_id == run_tags_alias.c.run_id,
                            run_tags_alias.c.key == key,
                            (run_tags_alias.c.value == value)
                            if isinstance(value, str)
                            else run_tags_alias.c.value.in_(value),
                        ),
                    )

                query = query.where(
                    BulkActionsTable.c.key.in_(db_subquery(backfills_with_tags_query))
                )

        if filters and filters.job_name:
            if self.has_built_index(BACKFILL_JOB_NAME_AND_TAGS):
                query = query.where(BulkActionsTable.c.job_name == filters.job_name)
            else:
                run_tags_table = RunTagsTable

                runs_in_backfill_with_job_name = run_tags_table.join(
                    RunsTable,
                    db.and_(
                        RunTagsTable.c.run_id == RunsTable.c.run_id,
                        RunTagsTable.c.key == BACKFILL_ID_TAG,
                        RunsTable.c.pipeline_name == filters.job_name,
                    ),
                )

                backfills_with_job_name_query = db_select([RunTagsTable.c.value]).select_from(
                    runs_in_backfill_with_job_name
                )
                query = query.where(
                    BulkActionsTable.c.key.in_(db_subquery(backfills_with_job_name_query))
                )
        if filters and filters.statuses:
            query = query.where(
                BulkActionsTable.c.status.in_([status.value for status in filters.statuses])
            )
        if filters and filters.created_after:
            query = query.where(BulkActionsTable.c.timestamp > filters.created_after)
        if filters and filters.created_before:
            query = query.where(BulkActionsTable.c.timestamp < filters.created_before)
        if filters and filters.backfill_ids:
            query = query.where(BulkActionsTable.c.key.in_(filters.backfill_ids))
        return query

    def _add_cursor_limit_to_backfills_query(
        self, query, cursor: Optional[str] = None, limit: Optional[int] = None
    ):
        if limit:
            query = query.limit(limit)
        if cursor:
            cursor_query = db_select([BulkActionsTable.c.id]).where(
                BulkActionsTable.c.key == cursor
            )
            query = query.where(BulkActionsTable.c.id < cursor_query)

        return query

    def _apply_backfill_tags_filter_to_results(
        self, backfills: Sequence[PartitionBackfill], tags: Mapping[str, Union[str, Sequence[str]]]
    ) -> Sequence[PartitionBackfill]:
        if not tags:
            return backfills

        def _matches_backfill(
            backfill: PartitionBackfill, tags: Mapping[str, Union[str, Sequence[str]]]
        ) -> bool:
            for key, value in tags.items():
                if isinstance(value, str):
                    if backfill.tags.get(key) != value:
                        return False
                elif backfill.tags.get(key) not in value:
                    return False
            return True

        return [backfill for backfill in backfills if _matches_backfill(backfill, tags)]

    def get_backfills(
        self,
        filters: Optional[BulkActionsFilter] = None,
        cursor: Optional[str] = None,
        limit: Optional[int] = None,
        status: Optional[BulkActionStatus] = None,
    ) -> Sequence[PartitionBackfill]:
        check.opt_inst_param(status, "status", BulkActionStatus)
        query = db_select([BulkActionsTable.c.body, BulkActionsTable.c.timestamp])
        if status and filters:
            raise DagsterInvariantViolationError(
                "Cannot provide status and filters to get_backfills. Please use filters rather than status."
            )

        if status is not None:
            filters = BulkActionsFilter(statuses=[status])

        table = self._add_backfill_filters_to_table(BulkActionsTable, filters)
        query = self._backfills_query(filters=filters).select_from(table)
        query = self._add_cursor_limit_to_backfills_query(query, cursor=cursor, limit=limit)
        query = query.order_by(BulkActionsTable.c.id.desc())
        rows = self.fetchall(query)
        backfill_candidates = deserialize_values((row["body"] for row in rows), PartitionBackfill)

        if filters and filters.tags and not self.has_built_index(BACKFILL_JOB_NAME_AND_TAGS):
            # if we are still using the run tags table to get backfills by tag, we need to do an additional check.
            # runs can have more tags than the backfill that launched them. Since we filtered tags by
            # querying for runs with those tags, we need to do an additional check that the backfills
            # also have the requested tags
            backfill_candidates = self._apply_backfill_tags_filter_to_results(
                backfill_candidates, filters.tags
            )
        return backfill_candidates

    def get_backfills_count(self, filters: Optional[BulkActionsFilter] = None) -> int:
        check.opt_inst_param(filters, "filters", BulkActionsFilter)
        if filters and filters.tags:
            # runs can have more tags than the backfill that launched them. Since we filtered tags by
            # querying for runs with those tags, we need to do an additional check that the backfills
            # also have the requested tags. This requires fetching the backfills from the db and filtering them
            query = self._backfills_query(filters=filters)
            rows = self.fetchall(query)
            backfill_candidates = deserialize_values(
                (row["body"] for row in rows), PartitionBackfill
            )
            return len(
                self._apply_backfill_tags_filter_to_results(backfill_candidates, filters.tags)
            )

        subquery = db_subquery(self._backfills_query(filters=filters))
        query = db_select([db.func.count().label("count")]).select_from(subquery)
        row = self.fetchone(query)
        count = row["count"] if row else 0
        return count

    def get_backfill(self, backfill_id: str) -> Optional[PartitionBackfill]:
        check.str_param(backfill_id, "backfill_id")
        query = db_select([BulkActionsTable.c.body]).where(BulkActionsTable.c.key == backfill_id)
        row = self.fetchone(query)
        return deserialize_value(row["body"], PartitionBackfill) if row else None

    def add_backfill(self, partition_backfill: PartitionBackfill) -> None:
        check.inst_param(partition_backfill, "partition_backfill", PartitionBackfill)
        values: dict[str, Any] = dict(
            key=partition_backfill.backfill_id,
            status=partition_backfill.status.value,
            timestamp=datetime_from_timestamp(partition_backfill.backfill_timestamp),
            body=serialize_value(cast("NamedTuple", partition_backfill)),
        )

        if self.has_bulk_actions_selector_cols():
            values["selector_id"] = partition_backfill.selector_id
            values["action_type"] = partition_backfill.bulk_action_type.value

        if self.has_bulk_action_job_name_column():
            values["job_name"] = partition_backfill.job_name

        with self.connect() as conn:
            conn.execute(BulkActionsTable.insert().values(**values))
            if self.has_backfill_tags_table():
                tags_to_insert = partition_backfill.tags
                if len(tags_to_insert.items()) > 0:
                    conn.execute(
                        BackfillTagsTable.insert(),
                        [
                            dict(
                                backfill_id=partition_backfill.backfill_id,
                                key=k,
                                value=v,
                            )
                            for k, v in tags_to_insert.items()
                        ],
                    )

    def update_backfill(self, partition_backfill: PartitionBackfill) -> None:
        check.inst_param(partition_backfill, "partition_backfill", PartitionBackfill)
        backfill_id = partition_backfill.backfill_id
        if not self.get_backfill(backfill_id):
            raise DagsterInvariantViolationError(
                f"Backfill {backfill_id} is not present in storage"
            )
        with self.connect() as conn:
            conn.execute(
                BulkActionsTable.update()
                .where(BulkActionsTable.c.key == backfill_id)
                .values(
                    status=partition_backfill.status.value,
                    body=serialize_value(partition_backfill),
                )
            )

    def get_cursor_values(self, keys: set[str]) -> Mapping[str, str]:
        check.set_param(keys, "keys", of_type=str)

        rows = self.fetchall(
            db_select([KeyValueStoreTable.c.key, KeyValueStoreTable.c.value]).where(
                KeyValueStoreTable.c.key.in_(keys)
            ),
        )
        return {row["key"]: row["value"] for row in rows}

    def set_cursor_values(self, pairs: Mapping[str, str]) -> None:
        check.mapping_param(pairs, "pairs", key_type=str, value_type=str)
        db_values = [{"key": k, "value": v} for k, v in pairs.items()]

        with self.connect() as conn:
            try:
                conn.execute(KeyValueStoreTable.insert().values(db_values))
            except db_exc.IntegrityError:
                conn.execute(
                    KeyValueStoreTable.update()
                    .where(KeyValueStoreTable.c.key.in_(pairs.keys()))
                    .values(value=db.sql.case(pairs, value=KeyValueStoreTable.c.key))
                )

    # Migrating run history
    def replace_job_origin(self, run: DagsterRun, job_origin: RemoteJobOrigin) -> None:
        new_label = job_origin.repository_origin.get_label()
        with self.connect() as conn:
            conn.execute(
                RunsTable.update()
                .where(RunsTable.c.run_id == run.run_id)
                .values(
                    run_body=serialize_value(
                        run.with_job_origin(job_origin).with_tags(
                            {**run.tags, REPOSITORY_LABEL_TAG: new_label}
                        )
                    ),
                )
            )
            conn.execute(
                RunTagsTable.update()
                .where(RunTagsTable.c.run_id == run.run_id)
                .where(RunTagsTable.c.key == REPOSITORY_LABEL_TAG)
                .values(value=new_label)
            )


GET_PIPELINE_SNAPSHOT_QUERY_ID = "get-pipeline-snapshot"


def defensively_unpack_execution_plan_snapshot_query(
    logger: logging.Logger, row: Sequence[Any]
) -> Optional[Union[ExecutionPlanSnapshot, JobSnap]]:
    # minimal checking here because sqlalchemy returns a different type based on what version of
    # SqlAlchemy you are using

    def _warn(msg: str) -> None:
        logger.warning(f"get-pipeline-snapshot: {msg}")

    if not isinstance(row[0], bytes):
        _warn("First entry in row is not a binary type.")
        return None

    try:
        uncompressed_bytes = zlib.decompress(row[0])
    except zlib.error:
        _warn("Could not decompress bytes stored in snapshot table.")
        return None

    try:
        decoded_str = uncompressed_bytes.decode("utf-8")
    except UnicodeDecodeError:
        _warn("Could not unicode decode decompressed bytes stored in snapshot table.")
        return None

    try:
        return deserialize_value(decoded_str, (ExecutionPlanSnapshot, JobSnap))
    except JSONDecodeError:
        _warn("Could not parse json in snapshot table.")
        return None
