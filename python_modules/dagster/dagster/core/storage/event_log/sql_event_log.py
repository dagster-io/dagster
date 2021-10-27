import logging
from abc import abstractmethod
from collections import defaultdict
from datetime import datetime
from typing import Iterable, Optional, Sequence

import pendulum
import sqlalchemy as db
from dagster import check, seven
from dagster.core.assets import AssetDetails
from dagster.core.definitions.events import AssetKey, AssetMaterialization
from dagster.core.errors import DagsterEventLogInvalidForRun
from dagster.core.events import DagsterEventType
from dagster.core.events.log import EventLogEntry
from dagster.core.execution.stats import build_run_step_stats_from_events
from dagster.serdes import deserialize_json_to_dagster_namedtuple, serialize_dagster_namedtuple
from dagster.serdes.errors import DeserializationError
from dagster.utils import datetime_as_float, utc_datetime_from_naive, utc_datetime_from_timestamp

from ..pipeline_run import PipelineRunStatsSnapshot
from .base import (
    EventLogRecord,
    EventLogStorage,
    EventRecordsFilter,
    RunShardedEventsCursor,
    extract_asset_events_cursor,
)
from .migration import ASSET_DATA_MIGRATIONS, ASSET_KEY_INDEX_COLS, EVENT_LOG_DATA_MIGRATIONS
from .schema import AssetKeyTable, SecondaryIndexMigrationTable, SqlEventLogStorageTable


class SqlEventLogStorage(EventLogStorage):
    """Base class for SQL backed event log storages.

    Distinguishes between run-based connections and index connections in order to support run-level
    sharding, while maintaining the ability to do cross-run queries
    """

    @abstractmethod
    def run_connection(self, run_id):
        """Context manager yielding a connection to access the event logs for a specific run.

        Args:
            run_id (Optional[str]): Enables those storages which shard based on run_id, e.g.,
                SqliteEventLogStorage, to connect appropriately.
        """

    @abstractmethod
    def index_connection(self):
        """Context manager yielding a connection to access cross-run indexed tables.

        Args:
            run_id (Optional[str]): Enables those storages which shard based on run_id, e.g.,
                SqliteEventLogStorage, to connect appropriately.
        """

    @abstractmethod
    def upgrade(self):
        """This method should perform any schema migrations necessary to bring an
        out-of-date instance of the storage up to date.
        """

    def prepare_insert_event(self, event):
        """Helper method for preparing the event log SQL insertion statement.  Abstracted away to
        have a single place for the logical table representation of the event, while having a way
        for SQL backends to implement different execution implementations for `store_event`. See
        the `dagster-postgres` implementation which overrides the generic SQL implementation of
        `store_event`.
        """

        dagster_event_type = None
        asset_key_str = None
        partition = None
        step_key = event.step_key

        if event.is_dagster_event:
            dagster_event_type = event.dagster_event.event_type_value
            step_key = event.dagster_event.step_key
            if event.dagster_event.asset_key:
                check.inst_param(event.dagster_event.asset_key, "asset_key", AssetKey)
                asset_key_str = event.dagster_event.asset_key.to_string()
            if event.dagster_event.partition:
                partition = event.dagster_event.partition

        # https://stackoverflow.com/a/54386260/324449
        return SqlEventLogStorageTable.insert().values(  # pylint: disable=no-value-for-parameter
            run_id=event.run_id,
            event=serialize_dagster_namedtuple(event),
            dagster_event_type=dagster_event_type,
            # Postgres requires a datetime that is in UTC but has no timezone info set
            # in order to be stored correctly
            timestamp=datetime.utcfromtimestamp(event.timestamp),
            step_key=step_key,
            asset_key=asset_key_str,
            partition=partition,
        )

    def store_asset(self, event):
        check.inst_param(event, "event", EventLogEntry)
        if not event.is_dagster_event or not event.dagster_event.asset_key:
            return

        materialization = event.dagster_event.step_materialization_data.materialization
        # We switched to storing the entire event record of the last materialization instead of just
        # the AssetMaterialization object, so that we have access to metadata like timestamp,
        # pipeline, run_id, etc.
        #
        # This should make certain asset queries way more performant, without having to do extra
        # queries against the event log.
        #
        # This should be accompanied by a schema change in 0.12.0, renaming `last_materialization`
        # to `last_materialization_event`, for clarity.  For now, we should do some back-compat.
        #
        # https://github.com/dagster-io/dagster/issues/3945
        if self.has_secondary_index(ASSET_KEY_INDEX_COLS):
            insert_statement = (
                AssetKeyTable.insert().values(  # pylint: disable=no-value-for-parameter
                    asset_key=event.dagster_event.asset_key.to_string(),
                    last_materialization=serialize_dagster_namedtuple(event),
                    last_materialization_timestamp=utc_datetime_from_timestamp(event.timestamp),
                    last_run_id=event.run_id,
                    tags=seven.json.dumps(materialization.tags) if materialization.tags else None,
                )
            )
            update_statement = (
                AssetKeyTable.update()
                .values(  # pylint: disable=no-value-for-parameter
                    last_materialization=serialize_dagster_namedtuple(event),
                    last_materialization_timestamp=utc_datetime_from_timestamp(event.timestamp),
                    last_run_id=event.run_id,
                    tags=seven.json.dumps(materialization.tags) if materialization.tags else None,
                )
                .where(
                    AssetKeyTable.c.asset_key == event.dagster_event.asset_key.to_string(),
                )
            )
        else:
            insert_statement = (
                AssetKeyTable.insert().values(  # pylint: disable=no-value-for-parameter
                    asset_key=event.dagster_event.asset_key.to_string(),
                    last_materialization=serialize_dagster_namedtuple(event),
                    last_run_id=event.run_id,
                )
            )
            update_statement = (
                AssetKeyTable.update()
                .values(  # pylint: disable=no-value-for-parameter
                    last_materialization=serialize_dagster_namedtuple(event),
                    last_run_id=event.run_id,
                )
                .where(
                    AssetKeyTable.c.asset_key == event.dagster_event.asset_key.to_string(),
                )
            )

        with self.index_connection() as conn:
            try:
                conn.execute(insert_statement)
            except db.exc.IntegrityError:
                conn.execute(update_statement)

    def store_event(self, event):
        """Store an event corresponding to a pipeline run.

        Args:
            event (EventLogEntry): The event to store.
        """
        check.inst_param(event, "event", EventLogEntry)
        insert_event_statement = self.prepare_insert_event(event)
        run_id = event.run_id

        with self.run_connection(run_id) as conn:
            conn.execute(insert_event_statement)

        if event.is_dagster_event and event.dagster_event.asset_key:
            self.store_asset(event)

    def get_logs_for_run_by_log_id(
        self,
        run_id,
        cursor=-1,
        dagster_event_type=None,
        limit=None,
    ):
        check.str_param(run_id, "run_id")
        check.int_param(cursor, "cursor")
        check.invariant(
            cursor >= -1,
            "Don't know what to do with negative cursor {cursor}".format(cursor=cursor),
        )
        check.opt_inst_param(dagster_event_type, "dagster_event_type", DagsterEventType)

        query = (
            db.select([SqlEventLogStorageTable.c.id, SqlEventLogStorageTable.c.event])
            .where(SqlEventLogStorageTable.c.run_id == run_id)
            .order_by(SqlEventLogStorageTable.c.id.asc())
        )
        if dagster_event_type:
            query = query.where(
                SqlEventLogStorageTable.c.dagster_event_type == dagster_event_type.value
            )

        # adjust 0 based index cursor to SQL offset
        query = query.offset(cursor + 1)

        if limit:
            query = query.limit(limit)

        with self.run_connection(run_id) as conn:
            results = conn.execute(query).fetchall()

        events = {}
        try:
            for (
                record_id,
                json_str,
            ) in results:
                events[record_id] = check.inst_param(
                    deserialize_json_to_dagster_namedtuple(json_str), "event", EventLogEntry
                )
        except (seven.JSONDecodeError, DeserializationError) as err:
            raise DagsterEventLogInvalidForRun(run_id=run_id) from err

        return events

    def get_logs_for_run(
        self,
        run_id,
        cursor=-1,
        of_type=None,
        limit=None,
    ):
        """Get all of the logs corresponding to a run.

        Args:
            run_id (str): The id of the run for which to fetch logs.
            cursor (Optional[int]): Zero-indexed logs will be returned starting from cursor + 1,
                i.e., if cursor is -1, all logs will be returned. (default: -1)
            of_type (Optional[DagsterEventType]): the dagster event type to filter the logs.
            limit (Optional[int]): the maximum number of events to fetch
        """
        check.str_param(run_id, "run_id")
        check.int_param(cursor, "cursor")
        check.invariant(
            cursor >= -1,
            "Don't know what to do with negative cursor {cursor}".format(cursor=cursor),
        )
        check.opt_inst_param(of_type, "of_type", DagsterEventType)

        events_by_id = self.get_logs_for_run_by_log_id(run_id, cursor, of_type, limit)
        return [event for id, event in sorted(events_by_id.items(), key=lambda x: x[0])]

    def get_stats_for_run(self, run_id):
        check.str_param(run_id, "run_id")

        query = (
            db.select(
                [
                    SqlEventLogStorageTable.c.dagster_event_type,
                    db.func.count().label("n_events_of_type"),
                    db.func.max(SqlEventLogStorageTable.c.timestamp).label("last_event_timestamp"),
                ]
            )
            .where(SqlEventLogStorageTable.c.run_id == run_id)
            .group_by("dagster_event_type")
        )

        with self.run_connection(run_id) as conn:
            results = conn.execute(query).fetchall()

        try:
            counts = {}
            times = {}
            for result in results:
                (dagster_event_type, n_events_of_type, last_event_timestamp) = result
                if dagster_event_type:
                    counts[dagster_event_type] = n_events_of_type
                    times[dagster_event_type] = last_event_timestamp

            enqueued_time = times.get(DagsterEventType.PIPELINE_ENQUEUED.value, None)
            launch_time = times.get(DagsterEventType.PIPELINE_STARTING.value, None)
            start_time = times.get(DagsterEventType.PIPELINE_START.value, None)
            end_time = times.get(
                DagsterEventType.PIPELINE_SUCCESS.value,
                times.get(
                    DagsterEventType.PIPELINE_FAILURE.value,
                    times.get(DagsterEventType.PIPELINE_CANCELED.value, None),
                ),
            )

            return PipelineRunStatsSnapshot(
                run_id=run_id,
                steps_succeeded=counts.get(DagsterEventType.STEP_SUCCESS.value, 0),
                steps_failed=counts.get(DagsterEventType.STEP_FAILURE.value, 0),
                materializations=counts.get(DagsterEventType.ASSET_MATERIALIZATION.value, 0),
                expectations=counts.get(DagsterEventType.STEP_EXPECTATION_RESULT.value, 0),
                enqueued_time=datetime_as_float(enqueued_time) if enqueued_time else None,
                launch_time=datetime_as_float(launch_time) if launch_time else None,
                start_time=datetime_as_float(start_time) if start_time else None,
                end_time=datetime_as_float(end_time) if end_time else None,
            )
        except (seven.JSONDecodeError, DeserializationError) as err:
            raise DagsterEventLogInvalidForRun(run_id=run_id) from err

    def get_step_stats_for_run(self, run_id, step_keys=None):
        check.str_param(run_id, "run_id")
        check.opt_list_param(step_keys, "step_keys", of_type=str)

        # Originally, this was two different queries:
        # 1) one query which aggregated top-level step stats by grouping by event type / step_key in
        #    a single query, using pure SQL (e.g. start_time, end_time, status, attempt counts).
        # 2) one query which fetched all the raw events for a specific event type and then inspected
        #    the deserialized event object to aggregate stats derived from sequences of events.
        #    (e.g. marker events, materializations, expectations resuls, attempts timing, etc.)
        #
        # For simplicity, we now just do the second type of query and derive the stats in Python
        # from the raw events.  This has the benefit of being easier to read and also the benefit of
        # being able to share code with the in-memory event log storage implementation.  We may
        # choose to revisit this in the future, especially if we are able to do JSON-column queries
        # in SQL as a way of bypassing the serdes layer in all cases.
        raw_event_query = (
            db.select([SqlEventLogStorageTable.c.event])
            .where(SqlEventLogStorageTable.c.run_id == run_id)
            .where(SqlEventLogStorageTable.c.step_key != None)
            .where(
                SqlEventLogStorageTable.c.dagster_event_type.in_(
                    [
                        DagsterEventType.STEP_START.value,
                        DagsterEventType.STEP_SUCCESS.value,
                        DagsterEventType.STEP_SKIPPED.value,
                        DagsterEventType.STEP_FAILURE.value,
                        DagsterEventType.STEP_RESTARTED.value,
                        DagsterEventType.ASSET_MATERIALIZATION.value,
                        DagsterEventType.STEP_EXPECTATION_RESULT.value,
                        DagsterEventType.STEP_RESTARTED.value,
                        DagsterEventType.STEP_UP_FOR_RETRY.value,
                        DagsterEventType.ENGINE_EVENT.value,
                    ]
                )
            )
            .order_by(SqlEventLogStorageTable.c.id.asc())
        )
        if step_keys:
            raw_event_query = raw_event_query.where(
                SqlEventLogStorageTable.c.step_key.in_(step_keys)
            )

        with self.run_connection(run_id) as conn:
            results = conn.execute(raw_event_query).fetchall()

        try:
            records = [
                check.inst_param(
                    deserialize_json_to_dagster_namedtuple(json_str), "event", EventLogEntry
                )
                for (json_str,) in results
            ]
            return build_run_step_stats_from_events(run_id, records)
        except (seven.JSONDecodeError, DeserializationError) as err:
            raise DagsterEventLogInvalidForRun(run_id=run_id) from err

    def _apply_migration(self, migration_name, migration_fn, print_fn, force):
        if self.has_secondary_index(migration_name):
            if not force:
                if print_fn:
                    print_fn("Skipping already reindexed summary: {}".format(migration_name))
                return
        if print_fn:
            print_fn("Starting reindex: {}".format(migration_name))
        migration_fn()(self, print_fn)
        self.enable_secondary_index(migration_name)
        if print_fn:
            print_fn("Finished reindexing: {}".format(migration_name))

    def reindex_events(self, print_fn=None, force=False):
        """Call this method to run any data migrations across the event_log table"""
        for migration_name, migration_fn in EVENT_LOG_DATA_MIGRATIONS.items():
            self._apply_migration(migration_name, migration_fn, print_fn, force)

    def reindex_assets(self, print_fn=None, force=False):
        """Call this method to run any data migrations across the asset_keys table"""
        for migration_name, migration_fn in ASSET_DATA_MIGRATIONS.items():
            self._apply_migration(migration_name, migration_fn, print_fn, force)

    def wipe(self):
        """Clears the event log storage."""
        # Should be overridden by SqliteEventLogStorage and other storages that shard based on
        # run_id

        # https://stackoverflow.com/a/54386260/324449
        with self.run_connection(run_id=None) as conn:
            conn.execute(SqlEventLogStorageTable.delete())  # pylint: disable=no-value-for-parameter
            conn.execute(AssetKeyTable.delete())  # pylint: disable=no-value-for-parameter

        with self.index_connection() as conn:
            conn.execute(SqlEventLogStorageTable.delete())  # pylint: disable=no-value-for-parameter
            conn.execute(AssetKeyTable.delete())  # pylint: disable=no-value-for-parameter

    def delete_events(self, run_id):
        with self.run_connection(run_id) as conn:
            self.delete_events_for_run(conn, run_id)

    def delete_events_for_run(self, conn, run_id):
        check.str_param(run_id, "run_id")

        delete_statement = (
            SqlEventLogStorageTable.delete().where(  # pylint: disable=no-value-for-parameter
                SqlEventLogStorageTable.c.run_id == run_id
            )
        )
        removed_asset_key_query = (
            db.select([SqlEventLogStorageTable.c.asset_key])
            .where(SqlEventLogStorageTable.c.run_id == run_id)
            .where(SqlEventLogStorageTable.c.asset_key != None)
            .group_by(SqlEventLogStorageTable.c.asset_key)
        )

        removed_asset_keys = [
            AssetKey.from_db_string(row[0])
            for row in conn.execute(removed_asset_key_query).fetchall()
        ]
        conn.execute(delete_statement)
        if len(removed_asset_keys) > 0:
            keys_to_check = []
            keys_to_check.extend([key.to_string() for key in removed_asset_keys])
            keys_to_check.extend([key.to_string(legacy=True) for key in removed_asset_keys])
            remaining_asset_keys = [
                AssetKey.from_db_string(row[0])
                for row in conn.execute(
                    db.select([SqlEventLogStorageTable.c.asset_key])
                    .where(SqlEventLogStorageTable.c.asset_key.in_(keys_to_check))
                    .group_by(SqlEventLogStorageTable.c.asset_key)
                )
            ]
            to_remove = set(removed_asset_keys) - set(remaining_asset_keys)
            if to_remove:
                keys_to_remove = []
                keys_to_remove.extend([key.to_string() for key in to_remove])
                keys_to_remove.extend([key.to_string(legacy=True) for key in to_remove])
                conn.execute(
                    AssetKeyTable.delete().where(  # pylint: disable=no-value-for-parameter
                        AssetKeyTable.c.asset_key.in_(keys_to_remove)
                    )
                )

    @property
    def is_persistent(self):
        return True

    def update_event_log_record(self, record_id, event):
        """Utility method for migration scripts to update SQL representation of event records."""
        check.int_param(record_id, "record_id")
        check.inst_param(event, "event", EventLogEntry)
        dagster_event_type = None
        asset_key_str = None
        if event.is_dagster_event:
            dagster_event_type = event.dagster_event.event_type_value
            if event.dagster_event.asset_key:
                check.inst_param(event.dagster_event.asset_key, "asset_key", AssetKey)
                asset_key_str = event.dagster_event.asset_key.to_string()

        with self.run_connection(run_id=event.run_id) as conn:
            conn.execute(
                SqlEventLogStorageTable.update()  # pylint: disable=no-value-for-parameter
                .where(SqlEventLogStorageTable.c.id == record_id)
                .values(
                    event=serialize_dagster_namedtuple(event),
                    dagster_event_type=dagster_event_type,
                    timestamp=datetime.utcfromtimestamp(event.timestamp),
                    step_key=event.step_key,
                    asset_key=asset_key_str,
                )
            )

    def get_event_log_table_data(self, run_id, record_id):
        """Utility method to test representation of the record in the SQL table.  Returns all of
        the columns stored in the event log storage (as opposed to the deserialized `EventLogEntry`).
        This allows checking that certain fields are extracted to support performant lookups (e.g.
        extracting `step_key` for fast filtering)"""
        with self.run_connection(run_id=run_id) as conn:
            query = (
                db.select([SqlEventLogStorageTable])
                .where(SqlEventLogStorageTable.c.id == record_id)
                .order_by(SqlEventLogStorageTable.c.id.asc())
            )
            return conn.execute(query).fetchone()

    def has_secondary_index(self, name):
        """This method uses a checkpoint migration table to see if summary data has been constructed
        in a secondary index table.  Can be used to checkpoint event_log data migrations.
        """
        query = (
            db.select([1])
            .where(SecondaryIndexMigrationTable.c.name == name)
            .where(SecondaryIndexMigrationTable.c.migration_completed != None)
            .limit(1)
        )
        with self.index_connection() as conn:
            results = conn.execute(query).fetchall()

        return len(results) > 0

    def enable_secondary_index(self, name):
        """This method marks an event_log data migration as complete, to indicate that a summary
        data migration is complete.
        """
        query = (
            SecondaryIndexMigrationTable.insert().values(  # pylint: disable=no-value-for-parameter
                name=name,
                migration_completed=datetime.now(),
            )
        )
        with self.index_connection() as conn:
            try:
                conn.execute(query)
            except db.exc.IntegrityError:
                conn.execute(
                    SecondaryIndexMigrationTable.update()  # pylint: disable=no-value-for-parameter
                    .where(SecondaryIndexMigrationTable.c.name == name)
                    .values(migration_completed=datetime.now())
                )

    def _apply_filter_to_query(
        self,
        query,
        event_records_filter=None,
        asset_details=None,
        apply_cursor_filters=True,
    ):
        if not event_records_filter:
            return query

        if event_records_filter.event_type:
            query = query.where(
                SqlEventLogStorageTable.c.dagster_event_type
                == event_records_filter.event_type.value
            )

        if event_records_filter.asset_key:
            query = query.where(
                db.or_(
                    SqlEventLogStorageTable.c.asset_key
                    == event_records_filter.asset_key.to_string(),
                    SqlEventLogStorageTable.c.asset_key
                    == event_records_filter.asset_key.to_string(legacy=True),
                )
            )

        if event_records_filter.asset_partitions:
            query = query.where(
                SqlEventLogStorageTable.c.partition.in_(event_records_filter.asset_partitions)
            )

        if asset_details and asset_details.last_wipe_timestamp:
            query = query.where(
                SqlEventLogStorageTable.c.timestamp
                > datetime.utcfromtimestamp(asset_details.last_wipe_timestamp)
            )

        if apply_cursor_filters:
            # allow the run-sharded sqlite implementation to disable this cursor filtering so that
            # it can implement its own custom cursor logic, as cursor ids are not unique across run
            # shards
            if event_records_filter.before_cursor is not None:
                before_cursor_id = (
                    event_records_filter.before_cursor.id
                    if isinstance(event_records_filter.before_cursor, RunShardedEventsCursor)
                    else event_records_filter.before_cursor
                )
                before_query = db.select([SqlEventLogStorageTable.c.id]).where(
                    SqlEventLogStorageTable.c.id == before_cursor_id
                )
                query = query.where(SqlEventLogStorageTable.c.id < before_query)

            if event_records_filter.after_cursor is not None:
                after_cursor_id = (
                    event_records_filter.after_cursor.id
                    if isinstance(event_records_filter.after_cursor, RunShardedEventsCursor)
                    else event_records_filter.after_cursor
                )
                query = query.where(SqlEventLogStorageTable.c.id > after_cursor_id)

        if event_records_filter.before_timestamp:
            query = query.where(
                SqlEventLogStorageTable.c.timestamp
                < datetime.utcfromtimestamp(event_records_filter.before_timestamp)
            )

        if event_records_filter.after_timestamp:
            query = query.where(
                SqlEventLogStorageTable.c.timestamp
                > datetime.utcfromtimestamp(event_records_filter.after_timestamp)
            )

        return query

    def get_event_records(
        self,
        event_records_filter: Optional[EventRecordsFilter] = None,
        limit: Optional[int] = None,
        ascending: bool = False,
    ) -> Iterable[EventLogRecord]:
        """Returns a list of (record_id, record)."""
        check.opt_inst_param(event_records_filter, "event_records_filter", EventRecordsFilter)
        check.opt_int_param(limit, "limit")
        check.bool_param(ascending, "ascending")

        query = db.select([SqlEventLogStorageTable.c.id, SqlEventLogStorageTable.c.event])
        if event_records_filter and event_records_filter.asset_key:
            asset_details = self._get_asset_details(event_records_filter.asset_key)
        else:
            asset_details = None

        query = self._apply_filter_to_query(
            query=query,
            event_records_filter=event_records_filter,
            asset_details=asset_details,
        )
        if limit:
            query = query.limit(limit)

        if ascending:
            query = query.order_by(
                SqlEventLogStorageTable.c.timestamp.asc(), SqlEventLogStorageTable.c.id.asc()
            )
        else:
            query = query.order_by(
                SqlEventLogStorageTable.c.timestamp.desc(), SqlEventLogStorageTable.c.id.desc()
            )

        with self.index_connection() as conn:
            results = conn.execute(query).fetchall()

        event_records = []
        for row_id, json_str in results:
            try:
                event_record = deserialize_json_to_dagster_namedtuple(json_str)
                if not isinstance(event_record, EventLogEntry):
                    logging.warning(
                        "Could not resolve event record as EventLogEntry for id `{}`.".format(
                            row_id
                        )
                    )
                    continue
                else:
                    event_records.append(
                        EventLogRecord(storage_id=row_id, event_log_entry=event_record)
                    )
            except seven.JSONDecodeError:
                logging.warning("Could not parse event record id `{}`.".format(row_id))

        return event_records

    def has_asset_key(self, asset_key: AssetKey) -> bool:
        check.inst_param(asset_key, "asset_key", AssetKey)
        if self.has_secondary_index(ASSET_KEY_INDEX_COLS):
            query = (
                db.select([AssetKeyTable.c.asset_key])
                .where(
                    db.or_(
                        AssetKeyTable.c.asset_key == asset_key.to_string(),
                        AssetKeyTable.c.asset_key == asset_key.to_string(legacy=True),
                    )
                )
                .where(
                    db.or_(
                        AssetKeyTable.c.wipe_timestamp == None,
                        AssetKeyTable.c.last_materialization_timestamp
                        > AssetKeyTable.c.wipe_timestamp,
                    )
                )
                .limit(1)
            )
            with self.index_connection() as conn:
                row = conn.execute(query).fetchone()
                return bool(row)

        # has not migrated, need to pull asset_details to get wipe status
        query = (
            db.select([AssetKeyTable.c.asset_key, AssetKeyTable.c.asset_details])
            .where(
                db.or_(
                    AssetKeyTable.c.asset_key == asset_key.to_string(),
                    AssetKeyTable.c.asset_key == asset_key.to_string(legacy=True),
                )
            )
            .limit(1)
        )

        with self.index_connection() as conn:
            row = conn.execute(query).fetchone()
            if not row:
                return False

            asset_details: Optional[AssetDetails] = AssetDetails.from_db_string(row[1])
            if not asset_details or not asset_details.last_wipe_timestamp:
                return True

            materialization_row = conn.execute(
                db.select([SqlEventLogStorageTable.c.timestamp])
                .where(
                    db.or_(
                        AssetKeyTable.c.asset_key == asset_key.to_string(),
                        AssetKeyTable.c.asset_key == asset_key.to_string(legacy=True),
                    )
                )
                .order_by(SqlEventLogStorageTable.c.timestamp.desc())
                .limit(1)
            ).fetchone()
            if not materialization_row:
                return False

            return utc_datetime_from_naive(materialization_row[0]) > utc_datetime_from_timestamp(
                asset_details.last_wipe_timestamp
            )

    def all_asset_keys(self):
        if self.has_secondary_index(ASSET_KEY_INDEX_COLS):
            with self.index_connection() as conn:
                results = conn.execute(
                    db.select([AssetKeyTable.c.asset_key]).where(
                        db.or_(
                            AssetKeyTable.c.wipe_timestamp == None,
                            AssetKeyTable.c.last_materialization_timestamp
                            > AssetKeyTable.c.wipe_timestamp,
                        )
                    )
                ).fetchall()
                return list(set([AssetKey.from_db_string(result[0]) for result in results]))

        # has not migrated, need to fetch the wipe_timestamp from asset_details
        with self.index_connection() as conn:
            results = conn.execute(
                db.select([AssetKeyTable.c.asset_key, AssetKeyTable.c.asset_details])
            ).fetchall()

            asset_keys = set()
            wiped = set()
            wiped_timestamps = {}
            for result in results:
                asset_key = AssetKey.from_db_string(result[0])
                asset_details: Optional[AssetDetails] = AssetDetails.from_db_string(result[1])
                asset_keys.add(asset_key)
                if asset_details and asset_details.last_wipe_timestamp:
                    wiped_timestamps[asset_key] = asset_details.last_wipe_timestamp

            if wiped_timestamps:
                materialized_timestamps = {}

                # fetch the last materialization timestamp per asset key
                materialization_results = conn.execute(
                    db.select(
                        [
                            SqlEventLogStorageTable.c.asset_key,
                            db.func.max(SqlEventLogStorageTable.c.timestamp),
                        ]
                    )
                    .where(
                        SqlEventLogStorageTable.c.asset_key.in_(
                            [asset_key.to_string() for asset_key in wiped_timestamps.keys()]
                        )
                    )
                    .group_by(SqlEventLogStorageTable.c.asset_key)
                    .order_by(db.func.max(SqlEventLogStorageTable.c.timestamp).asc())
                ).fetchall()

                for result in materialization_results:
                    asset_key = AssetKey.from_db_string(result[0])
                    last_materialized_timestamp = result[1]
                    materialized_timestamps[asset_key] = last_materialized_timestamp

                # calculate the set of wiped asset keys that have not had a materialization since
                # the wipe timestamp
                wiped = set(
                    [
                        asset_key
                        for asset_key in wiped_timestamps.keys()
                        if not materialized_timestamps.get(asset_key)
                        or utc_datetime_from_naive(materialized_timestamps.get(asset_key))
                        < utc_datetime_from_timestamp(wiped_timestamps[asset_key])
                    ]
                )

        return list(asset_keys.difference(wiped))

    def get_asset_keys(
        self,
        prefix: Optional[Sequence[str]] = None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> Sequence[AssetKey]:
        query = (
            db.select([AssetKeyTable.c.asset_key])
            .where(
                db.or_(
                    AssetKeyTable.c.wipe_timestamp == None,
                    AssetKeyTable.c.last_materialization_timestamp > AssetKeyTable.c.wipe_timestamp,
                )
            )
            .order_by(AssetKeyTable.c.asset_key.asc())
        )

        if prefix:
            prefix_str = seven.dumps(prefix)[:-1]
            query = query.where(AssetKeyTable.c.asset_key.startswith(prefix_str))

        if cursor:
            query = query.where(AssetKeyTable.c.asset_key > cursor)

        if limit:
            query = query.limit(limit)

        asset_keys = []
        with self.index_connection() as conn:
            results = conn.execute(query).fetchall()
            for result in results:
                asset_key = AssetKey.from_db_string(result[0])
                if asset_key:
                    asset_keys.append(asset_key)

        return asset_keys

    def _get_asset_details(self, asset_key):
        check.inst_param(asset_key, "asset_key", AssetKey)
        row = None
        with self.index_connection() as conn:
            row = conn.execute(
                db.select([AssetKeyTable.c.asset_details]).where(
                    AssetKeyTable.c.asset_key == asset_key.to_string()
                )
            ).fetchone()
            if not row or not row[0]:
                return None
            return deserialize_json_to_dagster_namedtuple(row[0])

    def _add_asset_wipe_filter_to_query(self, query, asset_details):
        if not asset_details or not asset_details.last_wipe_timestamp:
            return query

        return query.where(
            SqlEventLogStorageTable.c.timestamp
            > datetime.utcfromtimestamp(asset_details.last_wipe_timestamp)
        )

    def get_asset_events(
        self,
        asset_key,
        partitions=None,
        before_cursor=None,
        after_cursor=None,
        limit=None,
        ascending=False,
        include_cursor=False,  # deprecated
        before_timestamp=None,
        cursor=None,  # deprecated
    ):
        check.inst_param(asset_key, "asset_key", AssetKey)
        check.opt_list_param(partitions, "partitions", of_type=str)
        before_cursor, after_cursor = extract_asset_events_cursor(
            cursor, before_cursor, after_cursor, ascending
        )
        event_records = self.get_event_records(
            EventRecordsFilter(
                event_type=DagsterEventType.ASSET_MATERIALIZATION,
                asset_key=asset_key,
                asset_partitions=partitions,
                before_cursor=before_cursor,
                after_cursor=after_cursor,
                before_timestamp=before_timestamp,
            ),
            limit=limit,
            ascending=ascending,
        )
        if include_cursor:
            return [tuple([record.storage_id, record.event_log_entry]) for record in event_records]
        else:
            return [record.event_log_entry for record in event_records]

    def get_asset_run_ids(self, asset_key):
        check.inst_param(asset_key, "asset_key", AssetKey)
        query = (
            db.select(
                [SqlEventLogStorageTable.c.run_id, db.func.max(SqlEventLogStorageTable.c.timestamp)]
            )
            .where(
                db.or_(
                    SqlEventLogStorageTable.c.asset_key == asset_key.to_string(),
                    SqlEventLogStorageTable.c.asset_key == asset_key.to_string(legacy=True),
                )
            )
            .group_by(
                SqlEventLogStorageTable.c.run_id,
            )
            .order_by(db.func.max(SqlEventLogStorageTable.c.timestamp).desc())
        )

        asset_details = self._get_asset_details(asset_key)
        query = self._add_asset_wipe_filter_to_query(query, asset_details)

        with self.index_connection() as conn:
            results = conn.execute(query).fetchall()

        return [run_id for (run_id, _timestamp) in results]

    def _asset_materialization_from_json_column(self, json_str):
        if not json_str:
            return None

        # We switched to storing the entire event record of the last materialization instead of just
        # the AssetMaterialization object, so that we have access to metadata like timestamp,
        # pipeline, run_id, etc.
        #
        # This should make certain asset queries way more performant, without having to do extra
        # queries against the event log.
        #
        # This should be accompanied by a schema change in 0.12.0, renaming `last_materialization`
        # to `last_materialization_event`, for clarity.  For now, we should do some back-compat.
        #
        # https://github.com/dagster-io/dagster/issues/3945

        event_or_materialization = deserialize_json_to_dagster_namedtuple(json_str)
        if isinstance(event_or_materialization, AssetMaterialization):
            return event_or_materialization

        if (
            not isinstance(event_or_materialization, EventLogEntry)
            or not event_or_materialization.is_dagster_event
            or not event_or_materialization.dagster_event.asset_key
        ):
            return None

        return event_or_materialization.dagster_event.step_materialization_data.materialization

    def all_asset_tags(self):
        tags_by_asset_key = defaultdict(dict)
        if self.has_secondary_index(ASSET_KEY_INDEX_COLS):
            query = (
                db.select([AssetKeyTable.c.asset_key, AssetKeyTable.c.tags])
                .where(AssetKeyTable.c.tags != None)
                .where(
                    db.or_(
                        AssetKeyTable.c.wipe_timestamp == None,
                        AssetKeyTable.c.last_materialization_timestamp
                        > AssetKeyTable.c.wipe_timestamp,
                    )
                )
            )
            with self.index_connection() as conn:
                rows = conn.execute(query).fetchall()
                for asset_key, tags_json in rows:
                    tags = seven.json.loads(tags_json)
                    if tags:
                        tags_by_asset_key[AssetKey.from_db_string(asset_key)] = tags

        else:
            query = db.select([AssetKeyTable.c.asset_key, AssetKeyTable.c.last_materialization])
            with self.index_connection() as conn:
                rows = conn.execute(query).fetchall()
                for asset_key, json_str in rows:
                    materialization = self._asset_materialization_from_json_column(json_str)
                    if materialization and materialization.tags:
                        tags_by_asset_key[AssetKey.from_db_string(asset_key)] = {
                            k: v for k, v in materialization.tags.items()
                        }

        return tags_by_asset_key

    def get_asset_tags(self, asset_key):
        check.inst_param(asset_key, "asset_key", AssetKey)
        if self.has_secondary_index(ASSET_KEY_INDEX_COLS):
            query = (
                db.select([AssetKeyTable.c.tags])
                .where(AssetKeyTable.c.asset_key == asset_key.to_string())
                .where(
                    db.or_(
                        AssetKeyTable.c.wipe_timestamp == None,
                        AssetKeyTable.c.last_materialization_timestamp
                        > AssetKeyTable.c.wipe_timestamp,
                    )
                )
            )
            with self.index_connection() as conn:
                rows = conn.execute(query).fetchall()
                if not rows or not rows[0] or not rows[0][0]:
                    return {}

                return seven.json.loads(rows[0][0])
        else:
            query = db.select([AssetKeyTable.c.last_materialization]).where(
                AssetKeyTable.c.asset_key == asset_key.to_string()
            )
            with self.index_connection() as conn:
                rows = conn.execute(query).fetchall()
                if not rows or not rows[0] or not rows[0][0]:
                    return {}

                materialization = self._asset_materialization_from_json_column(rows[0][0])
                return materialization.tags if materialization and materialization.tags else {}

    def wipe_asset(self, asset_key):
        check.inst_param(asset_key, "asset_key", AssetKey)

        wipe_timestamp = pendulum.now("UTC").timestamp()

        if self.has_secondary_index(ASSET_KEY_INDEX_COLS):
            with self.index_connection() as conn:
                conn.execute(
                    AssetKeyTable.update()  # pylint: disable=no-value-for-parameter
                    .where(
                        db.or_(
                            AssetKeyTable.c.asset_key == asset_key.to_string(),
                            AssetKeyTable.c.asset_key == asset_key.to_string(legacy=True),
                        )
                    )
                    .values(
                        last_materialization=None,
                        last_run_id=None,
                        last_materialization_timestamp=None,
                        tags=None,
                        asset_details=serialize_dagster_namedtuple(
                            AssetDetails(last_wipe_timestamp=wipe_timestamp)
                        ),
                        wipe_timestamp=utc_datetime_from_timestamp(wipe_timestamp),
                    )
                )

        else:
            with self.index_connection() as conn:
                conn.execute(
                    AssetKeyTable.update()  # pylint: disable=no-value-for-parameter
                    .where(
                        db.or_(
                            AssetKeyTable.c.asset_key == asset_key.to_string(),
                            AssetKeyTable.c.asset_key == asset_key.to_string(legacy=True),
                        )
                    )
                    .values(
                        last_materialization=None,
                        last_run_id=None,
                        asset_details=serialize_dagster_namedtuple(
                            AssetDetails(last_wipe_timestamp=wipe_timestamp)
                        ),
                    )
                )
