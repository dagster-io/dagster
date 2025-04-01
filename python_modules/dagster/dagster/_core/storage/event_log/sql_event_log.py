import logging
import os
from abc import abstractmethod
from collections import OrderedDict, defaultdict
from collections.abc import Iterable, Iterator, Mapping, Sequence
from contextlib import contextmanager
from datetime import datetime, timezone
from functools import cached_property
from typing import (  # noqa: UP035
    TYPE_CHECKING,
    AbstractSet,
    Any,
    ContextManager,
    NamedTuple,
    Optional,
    Union,
    cast,
)

import dagster_shared.seven as seven
import sqlalchemy as db
import sqlalchemy.exc as db_exc
from dagster_shared.serdes import deserialize_values
from dagster_shared.serdes.errors import DeserializationError
from sqlalchemy.engine import Connection
from typing_extensions import TypeAlias

import dagster._check as check
from dagster._core.assets import AssetDetails
from dagster._core.definitions.asset_check_evaluation import (
    AssetCheckEvaluation,
    AssetCheckEvaluationPlanned,
)
from dagster._core.definitions.asset_check_spec import AssetCheckKey
from dagster._core.definitions.data_version import DATA_VERSION_TAG
from dagster._core.definitions.events import AssetKey, AssetMaterialization
from dagster._core.errors import (
    DagsterEventLogInvalidForRun,
    DagsterInvalidInvocationError,
    DagsterInvariantViolationError,
)
from dagster._core.event_api import (
    EventRecordsResult,
    RunShardedEventsCursor,
    RunStatusChangeRecordsFilter,
)
from dagster._core.events import (
    ASSET_CHECK_EVENTS,
    ASSET_EVENTS,
    EVENT_TYPE_TO_PIPELINE_RUN_STATUS,
    DagsterEventType,
)
from dagster._core.events.log import EventLogEntry
from dagster._core.execution.stats import (
    RUN_STATS_EVENT_TYPES,
    STEP_STATS_EVENT_TYPES,
    RunStepKeyStatsSnapshot,
    build_run_step_stats_from_events,
)
from dagster._core.storage.asset_check_execution_record import (
    COMPLETED_ASSET_CHECK_EXECUTION_RECORD_STATUSES,
    AssetCheckExecutionRecord,
    AssetCheckExecutionRecordStatus,
)
from dagster._core.storage.dagster_run import DagsterRunStatsSnapshot
from dagster._core.storage.event_log.base import (
    AssetCheckSummaryRecord,
    AssetEntry,
    AssetRecord,
    AssetRecordsFilter,
    EventLogConnection,
    EventLogCursor,
    EventLogRecord,
    EventLogStorage,
    EventRecordsFilter,
    PlannedMaterializationInfo,
    PoolLimit,
)
from dagster._core.storage.event_log.migration import (
    ASSET_DATA_MIGRATIONS,
    ASSET_KEY_INDEX_COLS,
    EVENT_LOG_DATA_MIGRATIONS,
)
from dagster._core.storage.event_log.schema import (
    AssetCheckExecutionsTable,
    AssetEventTagsTable,
    AssetKeyTable,
    ConcurrencyLimitsTable,
    ConcurrencySlotsTable,
    DynamicPartitionsTable,
    PendingStepsTable,
    SecondaryIndexMigrationTable,
    SqlEventLogStorageTable,
)
from dagster._core.storage.sql import SqlAlchemyQuery, SqlAlchemyRow
from dagster._core.storage.sqlalchemy_compat import (
    db_case,
    db_fetch_mappings,
    db_select,
    db_subquery,
)
from dagster._serdes import deserialize_value, serialize_value
from dagster._time import datetime_from_timestamp, get_current_timestamp, utc_datetime_from_naive
from dagster._utils import PrintFn
from dagster._utils.concurrency import (
    ClaimedSlotInfo,
    ConcurrencyClaimStatus,
    ConcurrencyKeyInfo,
    ConcurrencySlotStatus,
    PendingStepInfo,
    get_max_concurrency_limit_value,
)
from dagster._utils.warnings import deprecation_warning

if TYPE_CHECKING:
    from dagster._core.storage.partition_status_cache import AssetStatusCacheValue

MIN_ASSET_ROWS = 25
DEFAULT_MAX_LIMIT_EVENT_RECORDS = 10000


def get_max_event_records_limit() -> int:
    max_value = os.getenv("MAX_LIMIT_GET_EVENT_RECORDS")
    if not max_value:
        return DEFAULT_MAX_LIMIT_EVENT_RECORDS
    try:
        return int(max_value)
    except ValueError:
        return DEFAULT_MAX_LIMIT_EVENT_RECORDS


def enforce_max_records_limit(limit: int):
    max_limit = get_max_event_records_limit()
    if limit > max_limit:
        raise DagsterInvariantViolationError(
            f"Cannot fetch more than {max_limit} event records at a time. Requested {limit}."
        )


# We are using third-party library objects for DB connections-- at this time, these libraries are
# untyped. When/if we upgrade to typed variants, the `Any` here can be replaced or the alias as a
# whole can be dropped.
SqlDbConnection: TypeAlias = Any


class SqlEventLogStorage(EventLogStorage):
    """Base class for SQL backed event log storages.

    Distinguishes between run-based connections and index connections in order to support run-level
    sharding, while maintaining the ability to do cross-run queries
    """

    @abstractmethod
    def run_connection(self, run_id: Optional[str]) -> ContextManager[Connection]:
        """Context manager yielding a connection to access the event logs for a specific run.

        Args:
            run_id (Optional[str]): Enables those storages which shard based on run_id, e.g.,
                SqliteEventLogStorage, to connect appropriately.
        """

    @abstractmethod
    def index_connection(self) -> ContextManager[Connection]:
        """Context manager yielding a connection to access cross-run indexed tables."""

    @contextmanager
    def index_transaction(self) -> Iterator[Connection]:
        """Context manager yielding a connection to the index shard that has begun a transaction."""
        with self.index_connection() as conn:
            if conn.in_transaction():
                yield conn
            else:
                with conn.begin():
                    yield conn

    @abstractmethod
    def upgrade(self) -> None:
        """This method should perform any schema migrations necessary to bring an
        out-of-date instance of the storage up to date.
        """

    @abstractmethod
    def has_table(self, table_name: str) -> bool:
        """This method checks if a table exists in the database."""

    def prepare_insert_event(self, event: EventLogEntry) -> Any:
        """Helper method for preparing the event log SQL insertion statement.  Abstracted away to
        have a single place for the logical table representation of the event, while having a way
        for SQL backends to implement different execution implementations for `store_event`. See
        the `dagster-postgres` implementation which overrides the generic SQL implementation of
        `store_event`.
        """
        # https://stackoverflow.com/a/54386260/324449
        return SqlEventLogStorageTable.insert().values(**self._event_to_row(event))

    def prepare_insert_event_batch(self, events: Sequence[EventLogEntry]) -> Any:
        # https://stackoverflow.com/a/54386260/324449
        return SqlEventLogStorageTable.insert().values(
            [self._event_to_row(event) for event in events]
        )

    def _event_to_row(self, event: EventLogEntry) -> dict[str, Any]:
        dagster_event_type = None
        asset_key_str = None
        partition = None
        step_key = event.step_key
        if event.is_dagster_event:
            dagster_event = event.get_dagster_event()
            dagster_event_type = dagster_event.event_type_value
            step_key = dagster_event.step_key
            if dagster_event.asset_key:
                check.inst_param(dagster_event.asset_key, "asset_key", AssetKey)
                asset_key_str = dagster_event.asset_key.to_string()
            if dagster_event.partition:
                partition = dagster_event.partition

        return {
            "run_id": event.run_id,
            "event": serialize_value(event),
            "dagster_event_type": dagster_event_type,
            "timestamp": self._event_insert_timestamp(event),
            "step_key": step_key,
            "asset_key": asset_key_str,
            "partition": partition,
        }

    def has_asset_key_col(self, column_name: str) -> bool:
        with self.index_connection() as conn:
            column_names = [x.get("name") for x in db.inspect(conn).get_columns(AssetKeyTable.name)]
            return column_name in column_names

    def has_asset_key_index_cols(self) -> bool:
        return self.has_asset_key_col("last_materialization_timestamp")

    def store_asset_event(self, event: EventLogEntry, event_id: int):
        check.inst_param(event, "event", EventLogEntry)

        if not (event.dagster_event and event.dagster_event.asset_key):
            return

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

        values = self._get_asset_entry_values(event, event_id, self.has_asset_key_index_cols())
        if not values:
            return
        insert_statement = AssetKeyTable.insert().values(
            asset_key=event.dagster_event.asset_key.to_string(), **values
        )
        update_statement = (
            AssetKeyTable.update()
            .values(**values)
            .where(
                AssetKeyTable.c.asset_key == event.dagster_event.asset_key.to_string(),
            )
        )

        with self.index_connection() as conn:
            try:
                conn.execute(insert_statement)
            except db_exc.IntegrityError:
                conn.execute(update_statement)

    def _get_asset_entry_values(
        self, event: EventLogEntry, event_id: int, has_asset_key_index_cols: bool
    ) -> dict[str, Any]:
        # The AssetKeyTable contains a `last_materialization_timestamp` column that is exclusively
        # used to determine if an asset exists (last materialization timestamp > wipe timestamp).
        # This column is used nowhere else, and as of AssetObservation/AssetMaterializationPlanned
        # event creation, we want to extend this functionality to ensure that assets with any event
        # (observation, materialization, or materialization planned) yielded with timestamp
        # > wipe timestamp display in the Dagster UI.

        # As of the following PRs, we update last_materialization_timestamp to store the timestamp
        # of the latest asset observation, materialization, or materialization_planned that has occurred.
        # https://github.com/dagster-io/dagster/pull/6885
        # https://github.com/dagster-io/dagster/pull/7319

        entry_values: dict[str, Any] = {}
        dagster_event = check.not_none(event.dagster_event)
        if dagster_event.is_step_materialization:
            entry_values.update(
                {
                    "last_materialization": serialize_value(
                        EventLogRecord(
                            storage_id=event_id,
                            event_log_entry=event,
                        )
                    ),
                    "last_run_id": event.run_id,
                }
            )
            if has_asset_key_index_cols:
                entry_values.update(
                    {
                        "last_materialization_timestamp": datetime_from_timestamp(event.timestamp),
                    }
                )
        elif dagster_event.is_asset_materialization_planned:
            # The AssetKeyTable also contains a `last_run_id` column that is updated upon asset
            # materialization. This column was not being used until the below PR. This new change
            # writes to the column upon `ASSET_MATERIALIZATION_PLANNED` events to fetch the last
            # run id for a set of assets in one roundtrip call to event log storage.
            # https://github.com/dagster-io/dagster/pull/7319
            entry_values.update({"last_run_id": event.run_id})
            if has_asset_key_index_cols:
                entry_values.update(
                    {
                        "last_materialization_timestamp": datetime_from_timestamp(event.timestamp),
                    }
                )
        elif dagster_event.is_asset_observation:
            if has_asset_key_index_cols:
                entry_values.update(
                    {
                        "last_materialization_timestamp": datetime_from_timestamp(event.timestamp),
                    }
                )

        return entry_values

    def store_asset_event_tags(
        self, events: Sequence[EventLogEntry], event_ids: Sequence[int]
    ) -> None:
        check.sequence_param(events, "events", EventLogEntry)
        check.sequence_param(event_ids, "event_ids", int)

        all_values = [
            dict(
                event_id=event_id,
                asset_key=check.not_none(event.get_dagster_event().asset_key).to_string(),
                key=key,
                value=value,
                event_timestamp=self._event_insert_timestamp(event),
            )
            for event_id, event in zip(event_ids, events)
            for key, value in self._tags_for_asset_event(event).items()
        ]

        # Only execute if tags table exists. This is to support OSS users who have not yet run the
        # migration to create the table. On read, we will throw an error if the table does not
        # exist.
        if len(all_values) > 0 and self.has_table(AssetEventTagsTable.name):
            with self.index_connection() as conn:
                conn.execute(AssetEventTagsTable.insert(), all_values)

    def _tags_for_asset_event(self, event: EventLogEntry) -> Mapping[str, str]:
        tags = {}
        if event.dagster_event and event.dagster_event.asset_key:
            if event.dagster_event.is_step_materialization:
                tags = (
                    event.get_dagster_event().step_materialization_data.materialization.tags or {}
                )
            elif event.dagster_event.is_asset_observation:
                tags = event.get_dagster_event().asset_observation_data.asset_observation.tags
        keys_to_index = self.get_asset_tags_to_index(set(tags.keys()))
        return {k: v for k, v in tags.items() if k in keys_to_index}

    def store_event(self, event: EventLogEntry) -> None:
        """Store an event corresponding to a pipeline run.

        Args:
            event (EventLogEntry): The event to store.
        """
        check.inst_param(event, "event", EventLogEntry)
        insert_event_statement = self.prepare_insert_event(event)
        run_id = event.run_id

        event_id = None

        with self.run_connection(run_id) as conn:
            result = conn.execute(insert_event_statement)
            event_id = result.inserted_primary_key[0]

        if (
            event.is_dagster_event
            and event.dagster_event_type in ASSET_EVENTS
            and event.dagster_event.asset_key  # type: ignore
        ):
            self.store_asset_event(event, event_id)

            if event_id is None:
                raise DagsterInvariantViolationError(
                    "Cannot store asset event tags for null event id."
                )

            self.store_asset_event_tags([event], [event_id])

        if event.is_dagster_event and event.dagster_event_type in ASSET_CHECK_EVENTS:
            self.store_asset_check_event(event, event_id)

    def get_records_for_run(
        self,
        run_id,
        cursor: Optional[str] = None,
        of_type: Optional[Union[DagsterEventType, set[DagsterEventType]]] = None,
        limit: Optional[int] = None,
        ascending: bool = True,
    ) -> EventLogConnection:
        """Get all of the logs corresponding to a run.

        Args:
            run_id (str): The id of the run for which to fetch logs.
            cursor (Optional[int]): Zero-indexed logs will be returned starting from cursor + 1,
                i.e., if cursor is -1, all logs will be returned. (default: -1)
            of_type (Optional[DagsterEventType]): the dagster event type to filter the logs.
            limit (Optional[int]): the maximum number of events to fetch
        """
        check.str_param(run_id, "run_id")
        check.opt_str_param(cursor, "cursor")

        check.invariant(not of_type or isinstance(of_type, (DagsterEventType, frozenset, set)))

        dagster_event_types = (
            {of_type}
            if isinstance(of_type, DagsterEventType)
            else check.opt_set_param(of_type, "dagster_event_type", of_type=DagsterEventType)
        )

        query = (
            db_select([SqlEventLogStorageTable.c.id, SqlEventLogStorageTable.c.event])
            .where(SqlEventLogStorageTable.c.run_id == run_id)
            .order_by(
                SqlEventLogStorageTable.c.id.asc()
                if ascending
                else SqlEventLogStorageTable.c.id.desc()
            )
        )
        if dagster_event_types:
            query = query.where(
                SqlEventLogStorageTable.c.dagster_event_type.in_(
                    [dagster_event_type.value for dagster_event_type in dagster_event_types]
                )
            )

        # adjust 0 based index cursor to SQL offset
        if cursor is not None:
            cursor_obj = EventLogCursor.parse(cursor)
            if cursor_obj.is_offset_cursor():
                query = query.offset(cursor_obj.offset())
            elif cursor_obj.is_id_cursor():
                if ascending:
                    query = query.where(SqlEventLogStorageTable.c.id > cursor_obj.storage_id())
                else:
                    query = query.where(SqlEventLogStorageTable.c.id < cursor_obj.storage_id())

        if limit:
            query = query.limit(limit)

        with self.run_connection(run_id) as conn:
            results = conn.execute(query).fetchall()

        last_record_id = None
        try:
            records = []
            for (
                record_id,
                json_str,
            ) in results:
                records.append(
                    EventLogRecord(
                        storage_id=record_id,
                        event_log_entry=deserialize_value(json_str, EventLogEntry),
                    )
                )
                last_record_id = record_id
        except (seven.JSONDecodeError, DeserializationError) as err:
            raise DagsterEventLogInvalidForRun(run_id=run_id) from err

        if last_record_id is not None:
            next_cursor = EventLogCursor.from_storage_id(last_record_id).to_string()
        elif cursor:
            # record fetch returned no new logs, return the same cursor
            next_cursor = cursor
        else:
            # rely on the fact that all storage ids will be positive integers
            next_cursor = EventLogCursor.from_storage_id(-1).to_string()

        return EventLogConnection(
            records=records,
            cursor=next_cursor,
            has_more=bool(limit and len(results) == limit),
        )

    def get_stats_for_run(self, run_id: str) -> DagsterRunStatsSnapshot:
        check.str_param(run_id, "run_id")

        query = (
            db_select(
                [
                    SqlEventLogStorageTable.c.dagster_event_type,
                    db.func.count().label("n_events_of_type"),
                    db.func.max(SqlEventLogStorageTable.c.timestamp).label("last_event_timestamp"),
                ]
            )
            .where(
                db.and_(
                    SqlEventLogStorageTable.c.run_id == run_id,
                    SqlEventLogStorageTable.c.dagster_event_type.in_(
                        [event_type.value for event_type in RUN_STATS_EVENT_TYPES]
                    ),
                )
            )
            .group_by("dagster_event_type")
        )

        with self.run_connection(run_id) as conn:
            results = conn.execute(query).fetchall()

        try:
            counts = {}
            times = {}
            for result in results:
                (dagster_event_type, n_events_of_type, last_event_timestamp) = result
                check.invariant(dagster_event_type is not None)
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

            return DagsterRunStatsSnapshot(
                run_id=run_id,
                steps_succeeded=counts.get(DagsterEventType.STEP_SUCCESS.value, 0),
                steps_failed=counts.get(DagsterEventType.STEP_FAILURE.value, 0),
                materializations=counts.get(DagsterEventType.ASSET_MATERIALIZATION.value, 0),
                expectations=counts.get(DagsterEventType.STEP_EXPECTATION_RESULT.value, 0),
                enqueued_time=(
                    utc_datetime_from_naive(enqueued_time).timestamp() if enqueued_time else None
                ),
                launch_time=(
                    utc_datetime_from_naive(launch_time).timestamp() if launch_time else None
                ),
                start_time=(
                    utc_datetime_from_naive(start_time).timestamp() if start_time else None
                ),
                end_time=(utc_datetime_from_naive(end_time).timestamp() if end_time else None),
            )
        except (seven.JSONDecodeError, DeserializationError) as err:
            raise DagsterEventLogInvalidForRun(run_id=run_id) from err

    def get_step_stats_for_run(
        self, run_id: str, step_keys: Optional[Sequence[str]] = None
    ) -> Sequence[RunStepKeyStatsSnapshot]:
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
            db_select([SqlEventLogStorageTable.c.event])
            .where(SqlEventLogStorageTable.c.run_id == run_id)
            .where(SqlEventLogStorageTable.c.step_key != None)  # noqa: E711
            .where(
                SqlEventLogStorageTable.c.dagster_event_type.in_(
                    [event_type.value for event_type in STEP_STATS_EVENT_TYPES]
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
            records = deserialize_values((json_str for (json_str,) in results), EventLogEntry)
            return build_run_step_stats_from_events(run_id, records)
        except (seven.JSONDecodeError, DeserializationError) as err:
            raise DagsterEventLogInvalidForRun(run_id=run_id) from err

    def _apply_migration(self, migration_name, migration_fn, print_fn, force):
        if self.has_secondary_index(migration_name):
            if not force:
                if print_fn:
                    print_fn(f"Skipping already applied data migration: {migration_name}")
                return
        if print_fn:
            print_fn(f"Starting data migration: {migration_name}")
        migration_fn()(self, print_fn)
        self.enable_secondary_index(migration_name)
        if print_fn:
            print_fn(f"Finished data migration: {migration_name}")

    def reindex_events(self, print_fn: Optional[PrintFn] = None, force: bool = False) -> None:
        """Call this method to run any data migrations across the event_log table."""
        for migration_name, migration_fn in EVENT_LOG_DATA_MIGRATIONS.items():
            self._apply_migration(migration_name, migration_fn, print_fn, force)

    def reindex_assets(self, print_fn: Optional[PrintFn] = None, force: bool = False) -> None:
        """Call this method to run any data migrations across the asset_keys table."""
        for migration_name, migration_fn in ASSET_DATA_MIGRATIONS.items():
            self._apply_migration(migration_name, migration_fn, print_fn, force)

    def wipe(self) -> None:
        """Clears the event log storage."""
        # Should be overridden by SqliteEventLogStorage and other storages that shard based on
        # run_id

        # https://stackoverflow.com/a/54386260/324449
        with self.run_connection(run_id=None) as conn:
            conn.execute(SqlEventLogStorageTable.delete())
            conn.execute(AssetKeyTable.delete())

            if self.has_table("asset_event_tags"):
                conn.execute(AssetEventTagsTable.delete())

            if self.has_table("dynamic_partitions"):
                conn.execute(DynamicPartitionsTable.delete())

            if self.has_table("concurrency_limits"):
                conn.execute(ConcurrencyLimitsTable.delete())

            if self.has_table("concurrency_slots"):
                conn.execute(ConcurrencySlotsTable.delete())

            if self.has_table("pending_steps"):
                conn.execute(PendingStepsTable.delete())

            if self.has_table("asset_check_executions"):
                conn.execute(AssetCheckExecutionsTable.delete())

        self._wipe_index()

    def _wipe_index(self):
        with self.index_connection() as conn:
            conn.execute(SqlEventLogStorageTable.delete())
            conn.execute(AssetKeyTable.delete())

            if self.has_table("asset_event_tags"):
                conn.execute(AssetEventTagsTable.delete())

            if self.has_table("dynamic_partitions"):
                conn.execute(DynamicPartitionsTable.delete())

            if self.has_table("concurrency_slots"):
                conn.execute(ConcurrencySlotsTable.delete())

            if self.has_table("pending_steps"):
                conn.execute(PendingStepsTable.delete())

            if self.has_table("asset_check_executions"):
                conn.execute(AssetCheckExecutionsTable.delete())

    def delete_events(self, run_id: str) -> None:
        with self.run_connection(run_id) as conn:
            self.delete_events_for_run(conn, run_id)
        with self.index_connection() as conn:
            self.delete_events_for_run(conn, run_id)
        if self.supports_global_concurrency_limits:
            self.free_concurrency_slots_for_run(run_id)

    def delete_events_for_run(self, conn: Connection, run_id: str) -> None:
        check.str_param(run_id, "run_id")
        records = conn.execute(
            db_select([SqlEventLogStorageTable.c.id]).where(
                db.and_(
                    SqlEventLogStorageTable.c.run_id == run_id,
                    db.or_(
                        SqlEventLogStorageTable.c.dagster_event_type
                        == DagsterEventType.ASSET_MATERIALIZATION.value,
                        SqlEventLogStorageTable.c.dagster_event_type
                        == DagsterEventType.ASSET_OBSERVATION.value,
                    ),
                )
            )
        ).fetchall()
        asset_event_ids = [record[0] for record in records]
        conn.execute(
            SqlEventLogStorageTable.delete().where(SqlEventLogStorageTable.c.run_id == run_id)
        )
        if asset_event_ids:
            conn.execute(
                AssetEventTagsTable.delete().where(
                    AssetEventTagsTable.c.event_id.in_(asset_event_ids)
                )
            )

    @property
    def is_persistent(self) -> bool:
        return True

    def update_event_log_record(self, record_id: int, event: EventLogEntry) -> None:
        """Utility method for migration scripts to update SQL representation of event records."""
        check.int_param(record_id, "record_id")
        check.inst_param(event, "event", EventLogEntry)
        dagster_event_type = None
        asset_key_str = None
        if event.is_dagster_event:
            dagster_event_type = event.dagster_event.event_type_value  # type: ignore
            if event.dagster_event.asset_key:  # type: ignore
                check.inst_param(event.dagster_event.asset_key, "asset_key", AssetKey)  # type: ignore
                asset_key_str = event.dagster_event.asset_key.to_string()  # type: ignore

        with self.run_connection(run_id=event.run_id) as conn:
            conn.execute(
                SqlEventLogStorageTable.update()
                .where(SqlEventLogStorageTable.c.id == record_id)
                .values(
                    event=serialize_value(event),
                    dagster_event_type=dagster_event_type,
                    timestamp=self._event_insert_timestamp(event),
                    step_key=event.step_key,
                    asset_key=asset_key_str,
                )
            )

    def get_event_log_table_data(self, run_id: str, record_id: int) -> Optional[SqlAlchemyRow]:
        """Utility method to test representation of the record in the SQL table.  Returns all of
        the columns stored in the event log storage (as opposed to the deserialized `EventLogEntry`).
        This allows checking that certain fields are extracted to support performant lookups (e.g.
        extracting `step_key` for fast filtering).
        """
        with self.run_connection(run_id=run_id) as conn:
            query = (
                db_select([SqlEventLogStorageTable])
                .where(SqlEventLogStorageTable.c.id == record_id)
                .order_by(SqlEventLogStorageTable.c.id.asc())
            )
            return conn.execute(query).fetchone()

    def has_secondary_index(self, name: str) -> bool:
        """This method uses a checkpoint migration table to see if summary data has been constructed
        in a secondary index table.  Can be used to checkpoint event_log data migrations.
        """
        query = (
            db_select([1])
            .where(SecondaryIndexMigrationTable.c.name == name)
            .where(SecondaryIndexMigrationTable.c.migration_completed != None)  # noqa: E711
            .limit(1)
        )
        with self.index_connection() as conn:
            results = conn.execute(query).fetchall()

        return len(results) > 0

    def enable_secondary_index(self, name: str) -> None:
        """This method marks an event_log data migration as complete, to indicate that a summary
        data migration is complete.
        """
        query = SecondaryIndexMigrationTable.insert().values(
            name=name,
            migration_completed=datetime.now(),
        )
        with self.index_connection() as conn:
            try:
                conn.execute(query)
            except db_exc.IntegrityError:
                conn.execute(
                    SecondaryIndexMigrationTable.update()
                    .where(SecondaryIndexMigrationTable.c.name == name)
                    .values(migration_completed=datetime.now())
                )

    def _apply_filter_to_query(
        self,
        query: SqlAlchemyQuery,
        event_records_filter: EventRecordsFilter,
        asset_details: Optional[AssetDetails] = None,
        apply_cursor_filters: bool = True,
    ) -> SqlAlchemyQuery:
        query = query.where(
            SqlEventLogStorageTable.c.dagster_event_type == event_records_filter.event_type.value
        )

        if event_records_filter.asset_key:
            query = query.where(
                SqlEventLogStorageTable.c.asset_key == event_records_filter.asset_key.to_string(),
            )

        if event_records_filter.asset_partitions:
            query = query.where(
                SqlEventLogStorageTable.c.partition.in_(event_records_filter.asset_partitions)
            )

        if asset_details and asset_details.last_wipe_timestamp:
            query = query.where(
                SqlEventLogStorageTable.c.timestamp
                > datetime.fromtimestamp(asset_details.last_wipe_timestamp, timezone.utc).replace(
                    tzinfo=None
                )
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
                query = query.where(SqlEventLogStorageTable.c.id < before_cursor_id)

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
                < datetime.fromtimestamp(
                    event_records_filter.before_timestamp, timezone.utc
                ).replace(tzinfo=None)
            )

        if event_records_filter.after_timestamp:
            query = query.where(
                SqlEventLogStorageTable.c.timestamp
                > datetime.fromtimestamp(
                    event_records_filter.after_timestamp, timezone.utc
                ).replace(tzinfo=None)
            )

        if event_records_filter.storage_ids:
            query = query.where(SqlEventLogStorageTable.c.id.in_(event_records_filter.storage_ids))

        return query

    def _apply_tags_table_joins(
        self,
        table: db.Table,
        tags: Mapping[str, Union[str, Sequence[str]]],
        asset_key: Optional[AssetKey],
    ) -> db.Table:
        event_id_col = table.c.id if table == SqlEventLogStorageTable else table.c.event_id
        i = 0
        for key, value in tags.items():
            i += 1
            tags_table = db_subquery(
                db_select([AssetEventTagsTable]), f"asset_event_tags_subquery_{i}"
            )
            table = table.join(
                tags_table,
                db.and_(
                    event_id_col == tags_table.c.event_id,
                    not asset_key or tags_table.c.asset_key == asset_key.to_string(),
                    tags_table.c.key == key,
                    (
                        tags_table.c.value == value
                        if isinstance(value, str)
                        else tags_table.c.value.in_(value)
                    ),
                ),
            )
        return table

    def get_event_records(
        self,
        event_records_filter: EventRecordsFilter,
        limit: Optional[int] = None,
        ascending: bool = False,
    ) -> Sequence[EventLogRecord]:
        return self._get_event_records(
            event_records_filter=event_records_filter, limit=limit, ascending=ascending
        )

    def _get_event_records(
        self,
        event_records_filter: EventRecordsFilter,
        limit: Optional[int] = None,
        ascending: bool = False,
    ) -> Sequence[EventLogRecord]:
        """Returns a list of (record_id, record)."""
        check.inst_param(event_records_filter, "event_records_filter", EventRecordsFilter)
        check.opt_int_param(limit, "limit")
        check.bool_param(ascending, "ascending")

        if event_records_filter.asset_key:
            asset_details = next(iter(self._get_assets_details([event_records_filter.asset_key])))
        else:
            asset_details = None

        query = db_select(
            [SqlEventLogStorageTable.c.id, SqlEventLogStorageTable.c.event]
        ).select_from(SqlEventLogStorageTable)

        query = self._apply_filter_to_query(
            query=query,
            event_records_filter=event_records_filter,
            asset_details=asset_details,
        )
        if limit:
            query = query.limit(limit)

        if ascending:
            query = query.order_by(SqlEventLogStorageTable.c.id.asc())
        else:
            query = query.order_by(SqlEventLogStorageTable.c.id.desc())

        with self.index_connection() as conn:
            results = conn.execute(query).fetchall()

        event_records = []
        for row_id, json_str in results:
            try:
                event_record = deserialize_value(json_str, NamedTuple)
                if not isinstance(event_record, EventLogEntry):
                    logging.warning(
                        "Could not resolve event record as EventLogEntry for id `%s`.", row_id
                    )
                    continue

                event_records.append(
                    EventLogRecord(storage_id=row_id, event_log_entry=event_record)
                )
            except seven.JSONDecodeError:
                logging.warning("Could not parse event record id `%s`.", row_id)

        return event_records

    def _get_event_records_result(
        self,
        event_records_filter: EventRecordsFilter,
        limit: int,
        cursor: Optional[str],
        ascending: bool,
    ):
        records = self._get_event_records(
            event_records_filter=event_records_filter,
            limit=limit,
            ascending=ascending,
        )
        if records:
            new_cursor = EventLogCursor.from_storage_id(records[-1].storage_id).to_string()
        elif cursor:
            new_cursor = cursor
        else:
            new_cursor = EventLogCursor.from_storage_id(-1).to_string()
        has_more = len(records) == limit
        return EventRecordsResult(records, cursor=new_cursor, has_more=has_more)

    def fetch_materializations(
        self,
        records_filter: Union[AssetKey, AssetRecordsFilter],
        limit: int,
        cursor: Optional[str] = None,
        ascending: bool = False,
    ) -> EventRecordsResult:
        enforce_max_records_limit(limit)
        if isinstance(records_filter, AssetRecordsFilter):
            event_records_filter = records_filter.to_event_records_filter(
                event_type=DagsterEventType.ASSET_MATERIALIZATION,
                cursor=cursor,
                ascending=ascending,
            )
        else:
            before_cursor, after_cursor = EventRecordsFilter.get_cursor_params(cursor, ascending)
            asset_key = records_filter
            event_records_filter = EventRecordsFilter(
                event_type=DagsterEventType.ASSET_MATERIALIZATION,
                asset_key=asset_key,
                before_cursor=before_cursor,
                after_cursor=after_cursor,
            )

        return self._get_event_records_result(event_records_filter, limit, cursor, ascending)

    def fetch_failed_materializations(
        self,
        records_filter: Union[AssetKey, AssetRecordsFilter],
        limit: int,
        cursor: Optional[str] = None,
        ascending: bool = False,
    ) -> EventRecordsResult:
        return EventRecordsResult(records=[], cursor=cursor or "", has_more=False)

    def fetch_observations(
        self,
        records_filter: Union[AssetKey, AssetRecordsFilter],
        limit: int,
        cursor: Optional[str] = None,
        ascending: bool = False,
    ) -> EventRecordsResult:
        enforce_max_records_limit(limit)
        if isinstance(records_filter, AssetRecordsFilter):
            event_records_filter = records_filter.to_event_records_filter(
                event_type=DagsterEventType.ASSET_OBSERVATION,
                cursor=cursor,
                ascending=ascending,
            )
        else:
            before_cursor, after_cursor = EventRecordsFilter.get_cursor_params(cursor, ascending)
            asset_key = records_filter
            event_records_filter = EventRecordsFilter(
                event_type=DagsterEventType.ASSET_OBSERVATION,
                asset_key=asset_key,
                before_cursor=before_cursor,
                after_cursor=after_cursor,
            )

        return self._get_event_records_result(event_records_filter, limit, cursor, ascending)

    def fetch_run_status_changes(
        self,
        records_filter: Union[DagsterEventType, RunStatusChangeRecordsFilter],
        limit: int,
        cursor: Optional[str] = None,
        ascending: bool = False,
    ) -> EventRecordsResult:
        enforce_max_records_limit(limit)
        event_type = (
            records_filter
            if isinstance(records_filter, DagsterEventType)
            else records_filter.event_type
        )
        if event_type not in EVENT_TYPE_TO_PIPELINE_RUN_STATUS:
            expected = ", ".join(EVENT_TYPE_TO_PIPELINE_RUN_STATUS.keys())
            check.failed(f"Expected one of {expected}, received {event_type.value}")

        before_cursor, after_cursor = EventRecordsFilter.get_cursor_params(cursor, ascending)
        event_records_filter = (
            records_filter.to_event_records_filter_without_job_names(cursor, ascending)
            if isinstance(records_filter, RunStatusChangeRecordsFilter)
            else EventRecordsFilter(
                event_type, before_cursor=before_cursor, after_cursor=after_cursor
            )
        )
        has_job_name_filter = (
            isinstance(records_filter, RunStatusChangeRecordsFilter) and records_filter.job_names
        )
        if has_job_name_filter and not self.supports_run_status_change_job_name_filter:
            check.failed(
                "Called fetch_run_status_changes with selectors, which are not supported with this storage."
            )
        return self._get_event_records_result(event_records_filter, limit, cursor, ascending)

    def get_logs_for_all_runs_by_log_id(
        self,
        after_cursor: int = -1,
        dagster_event_type: Optional[Union[DagsterEventType, set[DagsterEventType]]] = None,
        limit: Optional[int] = None,
    ) -> Mapping[int, EventLogEntry]:
        check.int_param(after_cursor, "after_cursor")
        check.invariant(
            after_cursor >= -1,
            f"Don't know what to do with negative cursor {after_cursor}",
        )

        if isinstance(dagster_event_type, set) and len(dagster_event_type) > 1:
            deprecation_warning(
                "Support for multiple event types to get_logs_for_all_runs_by_log_id",
                "1.8.0",
                "You should break up your query into multiple calls, one for each event type.",
            )

        dagster_event_types = (
            {dagster_event_type}
            if isinstance(dagster_event_type, DagsterEventType)
            else check.opt_set_param(
                dagster_event_type, "dagster_event_type", of_type=DagsterEventType
            )
        )

        query = (
            db_select([SqlEventLogStorageTable.c.id, SqlEventLogStorageTable.c.event])
            .where(SqlEventLogStorageTable.c.id > after_cursor)
            .order_by(SqlEventLogStorageTable.c.id.asc())
        )

        if dagster_event_types:
            query = query.where(
                SqlEventLogStorageTable.c.dagster_event_type.in_(
                    [dagster_event_type.value for dagster_event_type in dagster_event_types]
                )
            )

        if limit:
            query = query.limit(limit)

        with self.index_connection() as conn:
            results = conn.execute(query).fetchall()

        events = {}
        record_id = None
        try:
            for (
                record_id,
                json_str,
            ) in results:
                events[record_id] = deserialize_value(json_str, EventLogEntry)
        except (seven.JSONDecodeError, DeserializationError):
            logging.warning("Could not parse event record id `%s`.", record_id)

        return events

    def get_maximum_record_id(self) -> Optional[int]:
        with self.index_connection() as conn:
            result = conn.execute(db_select([db.func.max(SqlEventLogStorageTable.c.id)])).fetchone()
            return result[0]  # type: ignore

    def _construct_asset_record_from_row(
        self,
        row,
        last_materialization_record: Optional[EventLogRecord],
        can_read_asset_status_cache: bool,
    ) -> AssetRecord:
        from dagster._core.storage.partition_status_cache import AssetStatusCacheValue

        asset_key = AssetKey.from_db_string(row["asset_key"])
        if asset_key:
            return AssetRecord(
                storage_id=row["id"],
                asset_entry=AssetEntry(
                    asset_key=asset_key,
                    last_materialization_record=last_materialization_record,
                    last_run_id=row["last_run_id"],
                    asset_details=AssetDetails.from_db_string(row["asset_details"]),
                    cached_status=(
                        AssetStatusCacheValue.from_db_string(row["cached_status_data"])
                        if can_read_asset_status_cache
                        else None
                    ),
                    last_planned_materialization_storage_id=None,
                ),
            )
        else:
            check.failed("Row did not contain asset key.")

    def _get_latest_materialization_records(
        self, raw_asset_rows
    ) -> Mapping[AssetKey, Optional[EventLogRecord]]:
        # Given a list of raw asset rows, returns a mapping of asset key to latest asset materialization
        # event log entry. Fetches backcompat EventLogEntry records when the last_materialization
        # in the raw asset row is an AssetMaterialization.
        to_backcompat_fetch = set()
        results: dict[AssetKey, Optional[EventLogRecord]] = {}
        for row in raw_asset_rows:
            asset_key = AssetKey.from_db_string(row["asset_key"])
            if not asset_key:
                continue
            event_or_materialization = (
                deserialize_value(row["last_materialization"], NamedTuple)
                if row["last_materialization"]
                else None
            )
            if isinstance(event_or_materialization, EventLogRecord):
                results[asset_key] = event_or_materialization
            else:
                to_backcompat_fetch.add(asset_key)

        latest_event_subquery = db_subquery(
            db_select(
                [
                    SqlEventLogStorageTable.c.asset_key,
                    db.func.max(SqlEventLogStorageTable.c.id).label("id"),
                ]
            )
            .where(
                db.and_(
                    SqlEventLogStorageTable.c.asset_key.in_(
                        [asset_key.to_string() for asset_key in to_backcompat_fetch]
                    ),
                    SqlEventLogStorageTable.c.dagster_event_type
                    == DagsterEventType.ASSET_MATERIALIZATION.value,
                )
            )
            .group_by(SqlEventLogStorageTable.c.asset_key),
            "latest_event_subquery",
        )
        backcompat_query = db_select(
            [
                SqlEventLogStorageTable.c.asset_key,
                SqlEventLogStorageTable.c.id,
                SqlEventLogStorageTable.c.event,
            ]
        ).select_from(
            latest_event_subquery.join(
                SqlEventLogStorageTable,
                db.and_(
                    SqlEventLogStorageTable.c.asset_key == latest_event_subquery.c.asset_key,
                    SqlEventLogStorageTable.c.id == latest_event_subquery.c.id,
                ),
            )
        )
        with self.index_connection() as conn:
            event_rows = db_fetch_mappings(conn, backcompat_query)

        for row in event_rows:
            asset_key = AssetKey.from_db_string(cast(Optional[str], row["asset_key"]))
            if asset_key:
                results[asset_key] = EventLogRecord(
                    storage_id=cast(int, row["id"]),
                    event_log_entry=deserialize_value(cast(str, row["event"]), EventLogEntry),
                )
        return results

    def can_read_asset_status_cache(self) -> bool:
        return self.has_asset_key_col("cached_status_data")

    def can_write_asset_status_cache(self) -> bool:
        return self.has_asset_key_col("cached_status_data")

    def wipe_asset_cached_status(self, asset_key: AssetKey) -> None:
        if self.can_read_asset_status_cache():
            check.inst_param(asset_key, "asset_key", AssetKey)
            with self.index_connection() as conn:
                conn.execute(
                    AssetKeyTable.update()
                    .values(dict(cached_status_data=None))
                    .where(
                        AssetKeyTable.c.asset_key == asset_key.to_string(),
                    )
                )

    def get_asset_records(
        self, asset_keys: Optional[Sequence[AssetKey]] = None
    ) -> Sequence[AssetRecord]:
        rows = self._fetch_asset_rows(asset_keys=asset_keys)
        latest_materialization_records = self._get_latest_materialization_records(rows)
        can_read_asset_status_cache = self.can_read_asset_status_cache()

        asset_records: list[AssetRecord] = []
        for row in rows:
            asset_key = AssetKey.from_db_string(row["asset_key"])
            if asset_key:
                asset_records.append(
                    self._construct_asset_record_from_row(
                        row,
                        latest_materialization_records.get(asset_key),
                        can_read_asset_status_cache,
                    )
                )

        return asset_records

    def get_asset_check_summary_records(
        self, asset_check_keys: Sequence[AssetCheckKey]
    ) -> Mapping[AssetCheckKey, AssetCheckSummaryRecord]:
        states = {}
        for asset_check_key in asset_check_keys:
            last_execution_record = self.get_asset_check_execution_history(asset_check_key, limit=1)
            last_completed_execution_record = (
                last_execution_record
                # If the check has never been executed or the latest record is a completed record,
                # Avoid refetching the last completed record
                if (
                    not last_execution_record
                    or last_execution_record[0].status
                    in COMPLETED_ASSET_CHECK_EXECUTION_RECORD_STATUSES
                )
                else self.get_asset_check_execution_history(
                    asset_check_key, limit=1, status=COMPLETED_ASSET_CHECK_EXECUTION_RECORD_STATUSES
                )
            )
            states[asset_check_key] = AssetCheckSummaryRecord(
                asset_check_key=asset_check_key,
                last_check_execution_record=last_execution_record[0]
                if last_execution_record
                else None,
                last_run_id=last_execution_record[0].run_id if last_execution_record else None,
                last_completed_check_execution_record=last_completed_execution_record[0]
                if last_completed_execution_record
                else None,
            )
        return states

    def has_asset_key(self, asset_key: AssetKey) -> bool:
        check.inst_param(asset_key, "asset_key", AssetKey)
        rows = self._fetch_asset_rows(asset_keys=[asset_key])
        return bool(rows)

    def all_asset_keys(self):
        rows = self._fetch_asset_rows()
        asset_keys = [
            AssetKey.from_db_string(row["asset_key"])
            for row in sorted(rows, key=lambda x: x["asset_key"])
        ]
        return [asset_key for asset_key in asset_keys if asset_key]

    def get_asset_keys(
        self,
        prefix: Optional[Sequence[str]] = None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> Sequence[AssetKey]:
        rows = self._fetch_asset_rows(prefix=prefix, limit=limit, cursor=cursor)
        asset_keys = [
            AssetKey.from_db_string(row["asset_key"])
            for row in sorted(rows, key=lambda x: x["asset_key"])
        ]
        return [asset_key for asset_key in asset_keys if asset_key]

    def get_latest_materialization_events(
        self, asset_keys: Iterable[AssetKey]
    ) -> Mapping[AssetKey, Optional[EventLogEntry]]:
        check.iterable_param(asset_keys, "asset_keys", AssetKey)
        rows = self._fetch_asset_rows(asset_keys=asset_keys)
        return {
            asset_key: event_log_record.event_log_entry if event_log_record is not None else None
            for asset_key, event_log_record in self._get_latest_materialization_records(
                rows
            ).items()
        }

    def _fetch_asset_rows(
        self,
        asset_keys=None,
        prefix: Optional[Sequence[str]] = None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> Sequence[SqlAlchemyRow]:
        # fetches rows containing asset_key, last_materialization, and asset_details from the DB,
        # applying the filters specified in the arguments.
        #
        # Differs from _fetch_raw_asset_rows, in that it loops through to make sure enough rows are
        # returned to satisfy the limit.
        #
        # returns a list of rows where each row is a tuple of serialized asset_key, materialization,
        # and asset_details
        should_query = True
        current_cursor = cursor
        if self.has_secondary_index(ASSET_KEY_INDEX_COLS):
            # if we have migrated, we can limit using SQL
            fetch_limit = limit
        else:
            # if we haven't migrated, overfetch in case the first N results are wiped
            fetch_limit = max(limit, MIN_ASSET_ROWS) if limit else None
        result = []

        while should_query:
            rows, has_more, current_cursor = self._fetch_raw_asset_rows(
                asset_keys=asset_keys, prefix=prefix, limit=fetch_limit, cursor=current_cursor
            )
            result.extend(rows)
            should_query = bool(has_more) and bool(limit) and len(result) < cast(int, limit)

        is_partial_query = asset_keys is not None or bool(prefix) or bool(limit) or bool(cursor)
        if not is_partial_query and self._can_mark_assets_as_migrated(rows):  # pyright: ignore[reportPossiblyUnboundVariable]
            self.enable_secondary_index(ASSET_KEY_INDEX_COLS)

        return result[:limit] if limit else result

    def _fetch_raw_asset_rows(
        self,
        asset_keys: Optional[Sequence[AssetKey]] = None,
        prefix: Optional[Sequence[str]] = None,
        limit: Optional[int] = None,
        cursor=None,
    ) -> tuple[Iterable[SqlAlchemyRow], bool, Optional[str]]:
        # fetches rows containing asset_key, last_materialization, and asset_details from the DB,
        # applying the filters specified in the arguments.  Does not guarantee that the number of
        # rows returned will match the limit specified.  This helper function is used to fetch a
        # chunk of asset key rows, which may or may not be wiped.
        #
        # Returns a tuple of (rows, has_more, cursor), where each row is a tuple of serialized
        # asset_key, materialization, and asset_details
        # TODO update comment

        columns = [
            AssetKeyTable.c.id,
            AssetKeyTable.c.asset_key,
            AssetKeyTable.c.last_materialization,
            AssetKeyTable.c.last_run_id,
            AssetKeyTable.c.asset_details,
        ]
        if self.can_read_asset_status_cache():
            columns.extend([AssetKeyTable.c.cached_status_data])

        is_partial_query = asset_keys is not None or bool(prefix) or bool(limit) or bool(cursor)
        if self.has_asset_key_index_cols() and not is_partial_query:
            # if the schema has been migrated, fetch the last_materialization_timestamp to see if
            # we can lazily migrate the data table
            columns.append(AssetKeyTable.c.last_materialization_timestamp)
            columns.append(AssetKeyTable.c.wipe_timestamp)

        query = db_select(columns).order_by(AssetKeyTable.c.asset_key.asc())
        query = self._apply_asset_filter_to_query(query, asset_keys, prefix, limit, cursor)

        if self.has_secondary_index(ASSET_KEY_INDEX_COLS):
            query = query.where(
                db.or_(
                    AssetKeyTable.c.wipe_timestamp.is_(None),
                    AssetKeyTable.c.last_materialization_timestamp > AssetKeyTable.c.wipe_timestamp,
                )
            )
            with self.index_connection() as conn:
                rows = db_fetch_mappings(conn, query)

            return rows, False, None

        with self.index_connection() as conn:
            rows = db_fetch_mappings(conn, query)

        wiped_timestamps_by_asset_key: dict[AssetKey, float] = {}
        row_by_asset_key: dict[AssetKey, SqlAlchemyRow] = OrderedDict()

        for row in rows:
            asset_key = AssetKey.from_db_string(cast(str, row["asset_key"]))
            if not asset_key:
                continue
            asset_details = AssetDetails.from_db_string(row["asset_details"])
            if not asset_details or not asset_details.last_wipe_timestamp:
                row_by_asset_key[asset_key] = row
                continue
            materialization_or_event_or_record = (
                deserialize_value(cast(str, row["last_materialization"]), NamedTuple)
                if row["last_materialization"]
                else None
            )
            if isinstance(materialization_or_event_or_record, (EventLogRecord, EventLogEntry)):
                if isinstance(materialization_or_event_or_record, EventLogRecord):
                    event_timestamp = materialization_or_event_or_record.event_log_entry.timestamp
                else:
                    event_timestamp = materialization_or_event_or_record.timestamp

                if asset_details.last_wipe_timestamp > event_timestamp:
                    # this asset has not been materialized since being wiped, skip
                    continue
                else:
                    # add the key
                    row_by_asset_key[asset_key] = row
            else:
                row_by_asset_key[asset_key] = row
                wiped_timestamps_by_asset_key[asset_key] = asset_details.last_wipe_timestamp

        if wiped_timestamps_by_asset_key:
            materialization_times = self._fetch_backcompat_materialization_times(
                wiped_timestamps_by_asset_key.keys()  # type: ignore
            )
            for asset_key, wiped_timestamp in wiped_timestamps_by_asset_key.items():
                materialization_time = materialization_times.get(asset_key)
                if not materialization_time or utc_datetime_from_naive(
                    materialization_time
                ) < datetime_from_timestamp(wiped_timestamp):
                    # remove rows that have not been materialized since being wiped
                    row_by_asset_key.pop(asset_key)

        has_more = limit and len(rows) == limit
        new_cursor = rows[-1]["id"] if rows else None

        return row_by_asset_key.values(), has_more, new_cursor  # type: ignore

    def update_asset_cached_status_data(
        self, asset_key: AssetKey, cache_values: "AssetStatusCacheValue"
    ) -> None:
        if self.can_read_asset_status_cache():
            with self.index_connection() as conn:
                conn.execute(
                    AssetKeyTable.update()
                    .where(
                        AssetKeyTable.c.asset_key == asset_key.to_string(),
                    )
                    .values(cached_status_data=serialize_value(cache_values))
                )

    def _fetch_backcompat_materialization_times(
        self, asset_keys: Sequence[AssetKey]
    ) -> Mapping[AssetKey, datetime]:
        # fetches the latest materialization timestamp for the given asset_keys.  Uses the (slower)
        # raw event log table.
        backcompat_query = (
            db_select(
                [
                    SqlEventLogStorageTable.c.asset_key,
                    db.func.max(SqlEventLogStorageTable.c.timestamp).label("timestamp"),
                ]
            )
            .where(
                SqlEventLogStorageTable.c.asset_key.in_(
                    [asset_key.to_string() for asset_key in asset_keys]
                )
            )
            .group_by(SqlEventLogStorageTable.c.asset_key)
            .order_by(db.func.max(SqlEventLogStorageTable.c.timestamp).asc())
        )
        with self.index_connection() as conn:
            backcompat_rows = db_fetch_mappings(conn, backcompat_query)
        return {
            AssetKey.from_db_string(row["asset_key"]): row["timestamp"] for row in backcompat_rows
        }  # type: ignore

    def _can_mark_assets_as_migrated(self, rows):
        if not self.has_asset_key_index_cols():
            return False

        if self.has_secondary_index(ASSET_KEY_INDEX_COLS):
            # we have already migrated
            return False

        for row in rows:
            if not _get_from_row(row, "last_materialization_timestamp"):
                return False

            if _get_from_row(row, "asset_details") and not _get_from_row(row, "wipe_timestamp"):
                return False

        return True

    def _apply_asset_filter_to_query(
        self,
        query: SqlAlchemyQuery,
        asset_keys: Optional[Sequence[AssetKey]] = None,
        prefix=None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> SqlAlchemyQuery:
        if asset_keys is not None:
            query = query.where(
                AssetKeyTable.c.asset_key.in_([asset_key.to_string() for asset_key in asset_keys])
            )

        if prefix:
            prefix_str = seven.dumps(prefix)[:-1]
            query = query.where(AssetKeyTable.c.asset_key.startswith(prefix_str))

        if cursor:
            query = query.where(AssetKeyTable.c.asset_key > cursor)

        if limit:
            query = query.limit(limit)
        return query

    def _get_assets_details(
        self, asset_keys: Sequence[AssetKey]
    ) -> Sequence[Optional[AssetDetails]]:
        check.sequence_param(asset_keys, "asset_key", AssetKey)
        rows = None
        with self.index_connection() as conn:
            rows = db_fetch_mappings(
                conn,
                db_select([AssetKeyTable.c.asset_key, AssetKeyTable.c.asset_details]).where(
                    AssetKeyTable.c.asset_key.in_(
                        [asset_key.to_string() for asset_key in asset_keys]
                    ),
                ),
            )

            asset_key_to_details = {
                cast(str, row["asset_key"]): (
                    deserialize_value(cast(str, row["asset_details"]), AssetDetails)
                    if row["asset_details"]
                    else None
                )
                for row in rows
            }

            # returns a list of the corresponding asset_details to provided asset_keys
            return [
                asset_key_to_details.get(asset_key.to_string(), None) for asset_key in asset_keys
            ]

    def _add_assets_wipe_filter_to_query(
        self,
        query: SqlAlchemyQuery,
        assets_details: Sequence[Optional[AssetDetails]],
        asset_keys: Sequence[AssetKey],
    ) -> SqlAlchemyQuery:
        check.invariant(
            len(assets_details) == len(asset_keys),
            "asset_details and asset_keys must be the same length",
        )
        for i in range(len(assets_details)):
            asset_key, asset_details = asset_keys[i], assets_details[i]
            if asset_details and asset_details.last_wipe_timestamp:
                asset_key_in_row = SqlEventLogStorageTable.c.asset_key == asset_key.to_string()
                # If asset key is in row, keep the row if the timestamp > wipe timestamp, else remove the row.
                # If asset key is not in row, keep the row.
                query = query.where(
                    db.or_(
                        db.and_(
                            asset_key_in_row,
                            SqlEventLogStorageTable.c.timestamp
                            > datetime.fromtimestamp(
                                asset_details.last_wipe_timestamp, timezone.utc
                            ).replace(tzinfo=None),
                        ),
                        db.not_(asset_key_in_row),
                    )
                )

        return query

    def get_event_tags_for_asset(
        self,
        asset_key: AssetKey,
        filter_tags: Optional[Mapping[str, str]] = None,
        filter_event_id: Optional[int] = None,
    ) -> Sequence[Mapping[str, str]]:
        """Fetches asset event tags for the given asset key.

        If filter_tags is provided, searches for events containing all of the filter tags. Then,
        returns all tags for those events. This enables searching for multipartitioned asset
        partition tags with a fixed dimension value, e.g. all of the tags for events where
        "country" == "US".

        If filter_event_id is provided, fetches only tags applied to the given event.

        Returns a list of dicts, where each dict is a mapping of tag key to tag value for a
        single event.
        """
        asset_key = check.inst_param(asset_key, "asset_key", AssetKey)
        filter_tags = check.opt_mapping_param(
            filter_tags, "filter_tags", key_type=str, value_type=str
        )
        filter_event_id = check.opt_int_param(filter_event_id, "filter_event_id")

        if not self.has_table(AssetEventTagsTable.name):
            raise DagsterInvalidInvocationError(
                "In order to search for asset event tags, you must run "
                "`dagster instance migrate` to create the AssetEventTags table."
            )

        asset_details = self._get_assets_details([asset_key])[0]
        if not filter_tags:
            tags_query = db_select(
                [
                    AssetEventTagsTable.c.key,
                    AssetEventTagsTable.c.value,
                    AssetEventTagsTable.c.event_id,
                ]
            ).where(AssetEventTagsTable.c.asset_key == asset_key.to_string())
            if asset_details and asset_details.last_wipe_timestamp:
                tags_query = tags_query.where(
                    AssetEventTagsTable.c.event_timestamp
                    > datetime.fromtimestamp(
                        asset_details.last_wipe_timestamp, timezone.utc
                    ).replace(tzinfo=None)
                )
        else:
            table = self._apply_tags_table_joins(AssetEventTagsTable, filter_tags, asset_key)
            tags_query = db_select(
                [
                    AssetEventTagsTable.c.key,
                    AssetEventTagsTable.c.value,
                    AssetEventTagsTable.c.event_id,
                ]
            ).select_from(table)

            if asset_details and asset_details.last_wipe_timestamp:
                tags_query = tags_query.where(
                    AssetEventTagsTable.c.event_timestamp
                    > datetime.fromtimestamp(
                        asset_details.last_wipe_timestamp, timezone.utc
                    ).replace(tzinfo=None)
                )

        if filter_event_id is not None:
            tags_query = tags_query.where(AssetEventTagsTable.c.event_id == filter_event_id)

        with self.index_connection() as conn:
            results = conn.execute(tags_query).fetchall()

        tags_by_event_id: dict[int, dict[str, str]] = defaultdict(dict)
        for row in results:
            key, value, event_id = row
            tags_by_event_id[event_id][key] = value

        return list(tags_by_event_id.values())

    def _asset_materialization_from_json_column(
        self, json_str: str
    ) -> Optional[AssetMaterialization]:
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

        event_or_materialization = deserialize_value(json_str, NamedTuple)
        if isinstance(event_or_materialization, AssetMaterialization):
            return event_or_materialization

        if (
            not isinstance(event_or_materialization, EventLogEntry)
            or not event_or_materialization.is_dagster_event
            or not event_or_materialization.dagster_event.asset_key  # type: ignore
        ):
            return None

        return event_or_materialization.dagster_event.step_materialization_data.materialization  # type: ignore

    def _get_asset_key_values_on_wipe(self) -> Mapping[str, Any]:
        wipe_timestamp = get_current_timestamp()
        values = {
            "asset_details": serialize_value(AssetDetails(last_wipe_timestamp=wipe_timestamp)),
            "last_run_id": None,
        }
        if self.has_asset_key_index_cols():
            values.update(
                dict(
                    wipe_timestamp=datetime_from_timestamp(wipe_timestamp),
                )
            )
        if self.can_read_asset_status_cache():
            values.update(dict(cached_status_data=None))
        return values

    def wipe_asset(self, asset_key: AssetKey) -> None:
        check.inst_param(asset_key, "asset_key", AssetKey)
        wiped_values = self._get_asset_key_values_on_wipe()

        with self.index_connection() as conn:
            conn.execute(
                AssetKeyTable.update()
                .values(**wiped_values)
                .where(
                    AssetKeyTable.c.asset_key == asset_key.to_string(),
                )
            )

    def wipe_asset_partitions(self, asset_key: AssetKey, partition_keys: Sequence[str]) -> None:
        """Remove asset index history from event log for given asset partitions."""
        raise NotImplementedError(
            "Partitioned asset wipe is not supported yet for this event log storage."
        )

    def get_materialized_partitions(
        self,
        asset_key: AssetKey,
        before_cursor: Optional[int] = None,
        after_cursor: Optional[int] = None,
    ) -> set[str]:
        query = (
            db_select(
                [
                    SqlEventLogStorageTable.c.partition,
                    db.func.max(SqlEventLogStorageTable.c.id),
                ]
            )
            .where(
                db.and_(
                    SqlEventLogStorageTable.c.asset_key == asset_key.to_string(),
                    SqlEventLogStorageTable.c.partition != None,  # noqa: E711
                    SqlEventLogStorageTable.c.dagster_event_type
                    == DagsterEventType.ASSET_MATERIALIZATION.value,
                )
            )
            .group_by(SqlEventLogStorageTable.c.partition)
        )

        assets_details = self._get_assets_details([asset_key])
        query = self._add_assets_wipe_filter_to_query(query, assets_details, [asset_key])

        if after_cursor:
            query = query.where(SqlEventLogStorageTable.c.id > after_cursor)
        if before_cursor:
            query = query.where(SqlEventLogStorageTable.c.id < before_cursor)

        with self.index_connection() as conn:
            results = conn.execute(query).fetchall()

        return set([cast(str, row[0]) for row in results])

    def _latest_event_ids_by_partition_subquery(
        self,
        asset_key: AssetKey,
        event_types: Sequence[DagsterEventType],
        asset_partitions: Optional[Sequence[str]] = None,
        before_cursor: Optional[int] = None,
        after_cursor: Optional[int] = None,
    ):
        """Subquery for locating the latest event ids by partition for a given asset key and set
        of event types.
        """
        query = db_select(
            [
                SqlEventLogStorageTable.c.dagster_event_type,
                SqlEventLogStorageTable.c.partition,
                db.func.max(SqlEventLogStorageTable.c.id).label("id"),
            ]
        ).where(
            db.and_(
                SqlEventLogStorageTable.c.asset_key == asset_key.to_string(),
                SqlEventLogStorageTable.c.partition != None,  # noqa: E711
                SqlEventLogStorageTable.c.dagster_event_type.in_(
                    [event_type.value for event_type in event_types]
                ),
            )
        )
        if asset_partitions is not None:
            query = query.where(SqlEventLogStorageTable.c.partition.in_(asset_partitions))
        if before_cursor is not None:
            query = query.where(SqlEventLogStorageTable.c.id < before_cursor)
        if after_cursor is not None:
            query = query.where(SqlEventLogStorageTable.c.id > after_cursor)

        latest_event_ids_subquery = query.group_by(
            SqlEventLogStorageTable.c.dagster_event_type, SqlEventLogStorageTable.c.partition
        )

        assets_details = self._get_assets_details([asset_key])
        return db_subquery(
            self._add_assets_wipe_filter_to_query(
                latest_event_ids_subquery, assets_details, [asset_key]
            ),
            "latest_event_ids_by_partition_subquery",
        )

    def get_latest_storage_id_by_partition(
        self,
        asset_key: AssetKey,
        event_type: DagsterEventType,
        partitions: Optional[set[str]] = None,
    ) -> Mapping[str, int]:
        """Fetch the latest materialzation storage id for each partition for a given asset key.

        Returns a mapping of partition to storage id.
        """
        check.inst_param(asset_key, "asset_key", AssetKey)

        latest_event_ids_by_partition_subquery = self._latest_event_ids_by_partition_subquery(
            asset_key, [event_type], asset_partitions=list(partitions) if partitions else None
        )
        latest_event_ids_by_partition = db_select(
            [
                latest_event_ids_by_partition_subquery.c.partition,
                latest_event_ids_by_partition_subquery.c.id,
            ]
        )

        with self.index_connection() as conn:
            rows = conn.execute(latest_event_ids_by_partition).fetchall()

        latest_materialization_storage_id_by_partition: dict[str, int] = {}
        for row in rows:
            latest_materialization_storage_id_by_partition[cast(str, row[0])] = cast(int, row[1])
        return latest_materialization_storage_id_by_partition

    def get_latest_tags_by_partition(
        self,
        asset_key: AssetKey,
        event_type: DagsterEventType,
        tag_keys: Sequence[str],
        asset_partitions: Optional[Sequence[str]] = None,
        before_cursor: Optional[int] = None,
        after_cursor: Optional[int] = None,
    ) -> Mapping[str, Mapping[str, str]]:
        check.inst_param(asset_key, "asset_key", AssetKey)
        check.inst_param(event_type, "event_type", DagsterEventType)
        check.sequence_param(tag_keys, "tag_keys", of_type=str)
        check.opt_nullable_sequence_param(asset_partitions, "asset_partitions", of_type=str)
        check.opt_int_param(before_cursor, "before_cursor")
        check.opt_int_param(after_cursor, "after_cursor")

        if not tag_keys or len(tag_keys) != len(self.get_asset_tags_to_index(set(tag_keys))):
            check.failed(
                "Only a limited set of tag keys are whitelisted for querying the latest tag values by partition."
            )

        latest_event_ids_subquery = self._latest_event_ids_by_partition_subquery(
            asset_key=asset_key,
            event_types=[event_type],
            asset_partitions=asset_partitions,
            before_cursor=before_cursor,
            after_cursor=after_cursor,
        )

        latest_tags_by_partition_query = (
            db_select(
                [
                    latest_event_ids_subquery.c.partition,
                    AssetEventTagsTable.c.key,
                    AssetEventTagsTable.c.value,
                ]
            )
            .select_from(
                latest_event_ids_subquery.join(
                    AssetEventTagsTable,
                    AssetEventTagsTable.c.event_id == latest_event_ids_subquery.c.id,
                )
            )
            .where(AssetEventTagsTable.c.key.in_(tag_keys))
        )

        latest_tags_by_partition: dict[str, dict[str, str]] = defaultdict(dict)
        with self.index_connection() as conn:
            rows = conn.execute(latest_tags_by_partition_query).fetchall()

        for row in rows:
            latest_tags_by_partition[cast(str, row[0])][cast(str, row[1])] = cast(str, row[2])

        # convert defaultdict to dict
        return dict(latest_tags_by_partition)

    def get_latest_asset_partition_materialization_attempts_without_materializations(
        self, asset_key: AssetKey, after_storage_id: Optional[int] = None
    ) -> Mapping[str, tuple[str, int]]:
        """Fetch the latest materialzation and materialization planned events for each partition of the given asset.
        Return the partitions that have a materialization planned event but no matching (same run) materialization event.
        These materializations could be in progress, or they could have failed. A separate query checking the run status
        is required to know.

        Returns a mapping of partition to [run id, event id].
        """
        check.inst_param(asset_key, "asset_key", AssetKey)

        latest_event_ids_subquery = self._latest_event_ids_by_partition_subquery(
            asset_key,
            [
                DagsterEventType.ASSET_MATERIALIZATION,
                DagsterEventType.ASSET_MATERIALIZATION_PLANNED,
            ],
            after_cursor=after_storage_id,
        )

        latest_events_subquery = db_subquery(
            db_select(
                [
                    SqlEventLogStorageTable.c.dagster_event_type,
                    SqlEventLogStorageTable.c.partition,
                    SqlEventLogStorageTable.c.run_id,
                    SqlEventLogStorageTable.c.id,
                ]
            ).select_from(
                latest_event_ids_subquery.join(
                    SqlEventLogStorageTable,
                    SqlEventLogStorageTable.c.id == latest_event_ids_subquery.c.id,
                ),
            ),
            "latest_events_subquery",
        )

        materialization_planned_events = db_select(
            [
                latest_events_subquery.c.dagster_event_type,
                latest_events_subquery.c.partition,
                latest_events_subquery.c.run_id,
                latest_events_subquery.c.id,
            ]
        ).where(
            latest_events_subquery.c.dagster_event_type
            == DagsterEventType.ASSET_MATERIALIZATION_PLANNED.value
        )

        materialization_events = db_select(
            [
                latest_events_subquery.c.dagster_event_type,
                latest_events_subquery.c.partition,
                latest_events_subquery.c.run_id,
                latest_events_subquery.c.id,
            ]
        ).where(
            latest_events_subquery.c.dagster_event_type
            == DagsterEventType.ASSET_MATERIALIZATION.value
        )

        with self.index_connection() as conn:
            materialization_planned_rows = db_fetch_mappings(conn, materialization_planned_events)
            materialization_rows = db_fetch_mappings(conn, materialization_events)

        materialization_planned_rows_by_partition = {
            row["partition"]: (row["run_id"], row["id"]) for row in materialization_planned_rows
        }
        for mat_row in materialization_rows:
            mat_partition = mat_row["partition"]
            mat_event_id = mat_row["id"]
            if mat_partition not in materialization_planned_rows_by_partition:
                continue
            _, planned_event_id = materialization_planned_rows_by_partition[mat_partition]
            if planned_event_id < mat_event_id:
                # this planned materialization event was followed by a materialization event
                materialization_planned_rows_by_partition.pop(mat_partition)

        return materialization_planned_rows_by_partition

    def _check_partitions_table(self) -> None:
        # Guards against cases where the user is not running the latest migration for
        # partitions storage. Should be updated when the partitions storage schema changes.
        if not self.has_table("dynamic_partitions"):
            raise DagsterInvalidInvocationError(
                "Using dynamic partitions definitions requires the dynamic partitions table, which"
                " currently does not exist. Add this table by running `dagster"
                " instance migrate`."
            )

    def get_dynamic_partitions(self, partitions_def_name: str) -> Sequence[str]:
        """Get the list of partition keys for a partition definition."""
        self._check_partitions_table()
        columns = [
            DynamicPartitionsTable.c.partitions_def_name,
            DynamicPartitionsTable.c.partition,
        ]
        query = (
            db_select(columns)
            .where(DynamicPartitionsTable.c.partitions_def_name == partitions_def_name)
            .order_by(DynamicPartitionsTable.c.id)
        )
        with self.index_connection() as conn:
            rows = conn.execute(query).fetchall()

        return [cast(str, row[1]) for row in rows]

    def has_dynamic_partition(self, partitions_def_name: str, partition_key: str) -> bool:
        self._check_partitions_table()
        query = (
            db_select([DynamicPartitionsTable.c.partition])
            .where(
                db.and_(
                    DynamicPartitionsTable.c.partitions_def_name == partitions_def_name,
                    DynamicPartitionsTable.c.partition == partition_key,
                )
            )
            .limit(1)
        )
        with self.index_connection() as conn:
            results = conn.execute(query).fetchall()

        return len(results) > 0

    def add_dynamic_partitions(
        self, partitions_def_name: str, partition_keys: Sequence[str]
    ) -> None:
        self._check_partitions_table()
        with self.index_connection() as conn:
            existing_rows = conn.execute(
                db_select([DynamicPartitionsTable.c.partition]).where(
                    db.and_(
                        DynamicPartitionsTable.c.partition.in_(partition_keys),
                        DynamicPartitionsTable.c.partitions_def_name == partitions_def_name,
                    )
                )
            ).fetchall()
            existing_keys = set([row[0] for row in existing_rows])
            new_keys = [
                partition_key
                for partition_key in partition_keys
                if partition_key not in existing_keys
            ]

            if new_keys:
                conn.execute(
                    DynamicPartitionsTable.insert(),
                    [
                        dict(partitions_def_name=partitions_def_name, partition=partition_key)
                        for partition_key in new_keys
                    ],
                )

    def delete_dynamic_partition(self, partitions_def_name: str, partition_key: str) -> None:
        self._check_partitions_table()
        with self.index_connection() as conn:
            conn.execute(
                DynamicPartitionsTable.delete().where(
                    db.and_(
                        DynamicPartitionsTable.c.partitions_def_name == partitions_def_name,
                        DynamicPartitionsTable.c.partition == partition_key,
                    )
                )
            )

    @cached_property
    def supports_global_concurrency_limits(self) -> bool:  # pyright: ignore[reportIncompatibleMethodOverride]
        return self.has_table(ConcurrencySlotsTable.name)

    @cached_property
    def has_default_pool_limit_col(self) -> bool:
        # This table was added later, and to avoid forcing a migration
        # we handle in the code if its been added or not.
        if not self.has_table(ConcurrencyLimitsTable.name):
            return False

        with self.index_connection() as conn:
            column_names = [
                x.get("name") for x in db.inspect(conn).get_columns(ConcurrencyLimitsTable.name)
            ]
            return ConcurrencyLimitsTable.c.using_default_limit.name in column_names

    @cached_property
    def has_concurrency_limits_table(self) -> bool:
        # This table was added later, and to avoid forcing a migration
        # we handle in the code if its been added or not.
        return self.has_table(ConcurrencyLimitsTable.name)

    def _reconcile_concurrency_limits_from_slots(self) -> None:
        """Helper function that can be reconciles the concurrency limits table from the concurrency
        slots table.  This should only run when the concurrency limits table exists and is empty,
        since all of the slot configuration operations should keep them in sync.  We reconcile from
        the slots table because the initial implementation did not have the limits table.
        """
        if not self.has_concurrency_limits_table:
            return

        if not self._has_rows(ConcurrencySlotsTable) or self._has_rows(ConcurrencyLimitsTable):
            return

        with self.index_transaction() as conn:
            rows = conn.execute(
                db_select(
                    [
                        ConcurrencySlotsTable.c.concurrency_key,
                        db.func.count().label("count"),
                    ]
                )
                .where(
                    ConcurrencySlotsTable.c.deleted == False,  # noqa: E712
                )
                .group_by(
                    ConcurrencySlotsTable.c.concurrency_key,
                )
            ).fetchall()
            conn.execute(
                ConcurrencyLimitsTable.insert().values(
                    [
                        {
                            "concurrency_key": row[0],
                            "limit": row[1],
                        }
                        for row in rows
                    ]
                )
            )

    def _has_rows(self, table) -> bool:
        with self.index_connection() as conn:
            row = conn.execute(db_select([True]).select_from(table).limit(1)).fetchone()
        return bool(row[0]) if row else False

    def initialize_concurrency_limit_to_default(self, concurrency_key: str) -> bool:
        if not self.has_concurrency_limits_table:
            return False

        self._reconcile_concurrency_limits_from_slots()

        if not self.has_instance:
            return False

        default_limit = self._instance.global_op_concurrency_default_limit
        # initialize outside of connection context
        has_default_pool_limit_col = self.has_default_pool_limit_col

        if has_default_pool_limit_col:
            with self.index_transaction() as conn:
                if default_limit is None:
                    conn.execute(
                        ConcurrencyLimitsTable.delete().where(
                            ConcurrencyLimitsTable.c.concurrency_key == concurrency_key,
                        )
                    )
                    self._allocate_concurrency_slots(conn, concurrency_key, 0)
                else:
                    try:
                        conn.execute(
                            ConcurrencyLimitsTable.insert().values(
                                concurrency_key=concurrency_key,
                                limit=default_limit,
                                using_default_limit=True,
                            )
                        )
                    except db_exc.IntegrityError:
                        conn.execute(
                            ConcurrencyLimitsTable.update()
                            .values(limit=default_limit)
                            .where(
                                db.and_(
                                    ConcurrencyLimitsTable.c.concurrency_key == concurrency_key,
                                    ConcurrencyLimitsTable.c.limit != default_limit,
                                )
                            )
                        )
                    self._allocate_concurrency_slots(conn, concurrency_key, default_limit)
            return True

        if default_limit is None:
            return False

        with self.index_transaction() as conn:
            try:
                conn.execute(
                    ConcurrencyLimitsTable.insert().values(
                        concurrency_key=concurrency_key, limit=default_limit
                    )
                )
            except db_exc.IntegrityError:
                pass

        self._allocate_concurrency_slots(conn, concurrency_key, default_limit)
        return True

    def _upsert_and_lock_limit_row(
        self, conn, concurrency_key: str, num: int, has_default_pool_limit_col: bool
    ):
        """Helper function that can be overridden by each implementing sql variant which obtains a
        lock on the concurrency limits row for the given key and updates it to the given value.
        """
        if not self.has_concurrency_limits_table:
            # no need to grab the lock on the concurrency limits row if the table does not exist
            return None

        row = conn.execute(
            db_select([ConcurrencyLimitsTable.c.id])
            .select_from(ConcurrencyLimitsTable)
            .where(ConcurrencyLimitsTable.c.concurrency_key == concurrency_key)
            .with_for_update()
            .limit(1)
        ).fetchone()

        if not row:
            if has_default_pool_limit_col:
                conn.execute(
                    ConcurrencyLimitsTable.insert().values(
                        concurrency_key=concurrency_key,
                        limit=num,
                        using_default_limit=False,
                    )
                )
            else:
                conn.execute(
                    ConcurrencyLimitsTable.insert().values(
                        concurrency_key=concurrency_key, limit=num
                    )
                )
        else:
            if has_default_pool_limit_col:
                conn.execute(
                    ConcurrencyLimitsTable.update()
                    .where(ConcurrencyLimitsTable.c.concurrency_key == concurrency_key)
                    .values(limit=num, using_default_limit=False)
                )
            else:
                conn.execute(
                    ConcurrencyLimitsTable.update()
                    .where(ConcurrencyLimitsTable.c.concurrency_key == concurrency_key)
                    .values(limit=num)
                )

    def set_concurrency_slots(self, concurrency_key: str, num: int) -> None:
        """Allocate a set of concurrency slots.

        Args:
            concurrency_key (str): The key to allocate the slots for.
            num (int): The number of slots to allocate.
        """
        max_limit = get_max_concurrency_limit_value()
        if num > max_limit:
            raise DagsterInvalidInvocationError(
                f"Cannot have more than {max_limit} slots per concurrency key."
            )
        if num < 0:
            raise DagsterInvalidInvocationError("Cannot have a negative number of slots.")

        # ensure that we have concurrency limits set for all keys
        self._reconcile_concurrency_limits_from_slots()

        # initialize outside of connection context
        has_default_pool_limit_col = self.has_default_pool_limit_col
        with self.index_transaction() as conn:
            self._upsert_and_lock_limit_row(conn, concurrency_key, num, has_default_pool_limit_col)
            keys_to_assign = self._allocate_concurrency_slots(conn, concurrency_key, num)

        if keys_to_assign:
            # we've added some slots... if there are any pending steps, we can assign them now or
            # they will be unutilized until free_concurrency_slots is called
            self.assign_pending_steps(keys_to_assign)

    def delete_concurrency_limit(self, concurrency_key: str) -> None:
        """Delete a concurrency limit and its associated slots.

        Args:
            concurrency_key (str): The key to delete.
        """
        # ensure that we have concurrency limits set for all keys
        self._reconcile_concurrency_limits_from_slots()

        with self.index_transaction() as conn:
            if self.has_concurrency_limits_table:
                conn.execute(
                    ConcurrencyLimitsTable.delete().where(
                        ConcurrencyLimitsTable.c.concurrency_key == concurrency_key
                    )
                )
            self._allocate_concurrency_slots(conn, concurrency_key, 0)

    def _allocate_concurrency_slots(self, conn, concurrency_key: str, num: int) -> list[str]:
        keys_to_assign = []
        count_row = conn.execute(
            db_select([db.func.count()])
            .select_from(ConcurrencySlotsTable)
            .where(
                db.and_(
                    ConcurrencySlotsTable.c.concurrency_key == concurrency_key,
                    ConcurrencySlotsTable.c.deleted == False,  # noqa: E712
                )
            )
        ).fetchone()
        existing = cast(int, count_row[0]) if count_row else 0

        if existing > num:
            # need to delete some slots, favoring ones where the slot is unallocated
            rows = conn.execute(
                db_select([ConcurrencySlotsTable.c.id])
                .select_from(ConcurrencySlotsTable)
                .where(
                    db.and_(
                        ConcurrencySlotsTable.c.concurrency_key == concurrency_key,
                        ConcurrencySlotsTable.c.deleted == False,  # noqa: E712
                    )
                )
                .order_by(
                    db_case([(ConcurrencySlotsTable.c.run_id.is_(None), 1)], else_=0).desc(),
                    ConcurrencySlotsTable.c.id.desc(),
                )
                .limit(existing - num)
            ).fetchall()

            if rows:
                # mark rows as deleted
                conn.execute(
                    ConcurrencySlotsTable.update()
                    .values(deleted=True)
                    .where(ConcurrencySlotsTable.c.id.in_([row[0] for row in rows]))
                )

            # actually delete rows that are marked as deleted and are not claimed... the rest
            # will be deleted when the slots are released by the free_concurrency_slots
            conn.execute(
                ConcurrencySlotsTable.delete().where(
                    db.and_(
                        ConcurrencySlotsTable.c.deleted == True,  # noqa: E712
                        ConcurrencySlotsTable.c.run_id == None,  # noqa: E711
                    )
                )
            )
        elif num > existing:
            # need to add some slots
            rows = [
                {
                    "concurrency_key": concurrency_key,
                    "run_id": None,
                    "step_key": None,
                    "deleted": False,
                }
                for _ in range(existing, num)
            ]
            conn.execute(ConcurrencySlotsTable.insert().values(rows))
            keys_to_assign.extend([concurrency_key for _ in range(existing, num)])
        return keys_to_assign

    def has_unassigned_slots(self, concurrency_key: str) -> bool:
        with self.index_connection() as conn:
            pending_row = conn.execute(
                db_select([db.func.count()])
                .select_from(PendingStepsTable)
                .where(
                    db.and_(
                        PendingStepsTable.c.concurrency_key == concurrency_key,
                        PendingStepsTable.c.assigned_timestamp != None,  # noqa: E711
                    )
                )
            ).fetchone()
            slots = conn.execute(
                db_select([db.func.count()])
                .select_from(ConcurrencySlotsTable)
                .where(
                    db.and_(
                        ConcurrencySlotsTable.c.concurrency_key == concurrency_key,
                        ConcurrencySlotsTable.c.deleted == False,  # noqa: E712
                    )
                )
            ).fetchone()
        pending_count = cast(int, pending_row[0]) if pending_row else 0
        slots_count = cast(int, slots[0]) if slots else 0
        return slots_count > pending_count

    def check_concurrency_claim(
        self, concurrency_key: str, run_id: str, step_key: str
    ) -> ConcurrencyClaimStatus:
        with self.index_connection() as conn:
            pending_row = conn.execute(
                db_select(
                    [
                        PendingStepsTable.c.assigned_timestamp,
                        PendingStepsTable.c.priority,
                        PendingStepsTable.c.create_timestamp,
                    ]
                ).where(
                    db.and_(
                        PendingStepsTable.c.run_id == run_id,
                        PendingStepsTable.c.step_key == step_key,
                        PendingStepsTable.c.concurrency_key == concurrency_key,
                    )
                )
            ).fetchone()

            if not pending_row:
                # no pending step pending_row exists, the slot is blocked and the enqueued timestamp is None
                return ConcurrencyClaimStatus(
                    concurrency_key=concurrency_key,
                    slot_status=ConcurrencySlotStatus.BLOCKED,
                    priority=None,
                    assigned_timestamp=None,
                    enqueued_timestamp=None,
                )

            priority = cast(int, pending_row[1]) if pending_row[1] else None
            assigned_timestamp = cast(datetime, pending_row[0]) if pending_row[0] else None
            create_timestamp = cast(datetime, pending_row[2]) if pending_row[2] else None
            if assigned_timestamp is None:
                return ConcurrencyClaimStatus(
                    concurrency_key=concurrency_key,
                    slot_status=ConcurrencySlotStatus.BLOCKED,
                    priority=priority,
                    assigned_timestamp=None,
                    enqueued_timestamp=create_timestamp,
                )

            # pending step is assigned, check to see if it's been claimed
            slot_row = conn.execute(
                db_select([db.func.count()]).where(
                    db.and_(
                        ConcurrencySlotsTable.c.concurrency_key == concurrency_key,
                        ConcurrencySlotsTable.c.run_id == run_id,
                        ConcurrencySlotsTable.c.step_key == step_key,
                    )
                )
            ).fetchone()

            return ConcurrencyClaimStatus(
                concurrency_key=concurrency_key,
                slot_status=(
                    ConcurrencySlotStatus.CLAIMED
                    if slot_row and slot_row[0]
                    else ConcurrencySlotStatus.BLOCKED
                ),
                priority=priority,
                assigned_timestamp=assigned_timestamp,
                enqueued_timestamp=create_timestamp,
            )

    def can_claim_from_pending(self, concurrency_key: str, run_id: str, step_key: str):
        with self.index_connection() as conn:
            row = conn.execute(
                db_select([PendingStepsTable.c.assigned_timestamp]).where(
                    db.and_(
                        PendingStepsTable.c.run_id == run_id,
                        PendingStepsTable.c.step_key == step_key,
                        PendingStepsTable.c.concurrency_key == concurrency_key,
                    )
                )
            ).fetchone()
            return row and row[0] is not None

    def has_pending_step(self, concurrency_key: str, run_id: str, step_key: str):
        with self.index_connection() as conn:
            row = conn.execute(
                db_select([db.func.count()])
                .select_from(PendingStepsTable)
                .where(
                    db.and_(
                        PendingStepsTable.c.concurrency_key == concurrency_key,
                        PendingStepsTable.c.run_id == run_id,
                        PendingStepsTable.c.step_key == step_key,
                    )
                )
            ).fetchone()
            return row and cast(int, row[0]) > 0

    def assign_pending_steps(self, concurrency_keys: Sequence[str]):
        if not concurrency_keys:
            return

        with self.index_connection() as conn:
            for key in concurrency_keys:
                row = conn.execute(
                    db_select([PendingStepsTable.c.id])
                    .where(
                        db.and_(
                            PendingStepsTable.c.concurrency_key == key,
                            PendingStepsTable.c.assigned_timestamp == None,  # noqa: E711
                        )
                    )
                    .order_by(
                        PendingStepsTable.c.priority.desc(),
                        PendingStepsTable.c.create_timestamp.asc(),
                    )
                    .limit(1)
                ).fetchone()
                if row:
                    conn.execute(
                        PendingStepsTable.update()
                        .where(PendingStepsTable.c.id == row[0])
                        .values(assigned_timestamp=db.func.now())
                    )

    def add_pending_step(
        self,
        concurrency_key: str,
        run_id: str,
        step_key: str,
        priority: Optional[int] = None,
        should_assign: bool = False,
    ):
        with self.index_connection() as conn:
            try:
                conn.execute(
                    PendingStepsTable.insert().values(
                        [
                            dict(
                                run_id=run_id,
                                step_key=step_key,
                                concurrency_key=concurrency_key,
                                priority=priority or 0,
                                assigned_timestamp=db.func.now() if should_assign else None,
                            )
                        ]
                    )
                )
            except db_exc.IntegrityError:
                # do nothing
                pass

    def _remove_pending_steps(self, run_id: str, step_key: Optional[str] = None) -> Sequence[str]:
        # fetch the assigned steps to delete, while grabbing the concurrency keys so that we can
        # assign the next set of queued steps, if necessary
        select_query = (
            db_select(
                [
                    PendingStepsTable.c.id,
                    PendingStepsTable.c.assigned_timestamp,
                    PendingStepsTable.c.concurrency_key,
                ]
            )
            .select_from(PendingStepsTable)
            .where(PendingStepsTable.c.run_id == run_id)
            .with_for_update()
        )
        if step_key:
            select_query = select_query.where(PendingStepsTable.c.step_key == step_key)

        with self.index_connection() as conn:
            rows = conn.execute(select_query).fetchall()
            if not rows:
                return []

            # now, actually delete the pending steps
            conn.execute(
                PendingStepsTable.delete().where(
                    PendingStepsTable.c.id.in_([row[0] for row in rows])
                )
            )

        # return the concurrency keys for the freed slots which were assigned
        to_assign = [cast(str, row[2]) for row in rows if row[1] is not None]
        return to_assign

    def claim_concurrency_slot(
        self, concurrency_key: str, run_id: str, step_key: str, priority: Optional[int] = None
    ) -> ConcurrencyClaimStatus:
        """Claim concurrency slot for step.

        Args:
            concurrency_keys (str): The concurrency key to claim.
            run_id (str): The run id to claim for.
            step_key (str): The step key to claim for.
        """
        # first, register the step by adding to pending queue
        if not self.has_pending_step(
            concurrency_key=concurrency_key, run_id=run_id, step_key=step_key
        ):
            has_unassigned_slots = self.has_unassigned_slots(concurrency_key)
            self.add_pending_step(
                concurrency_key=concurrency_key,
                run_id=run_id,
                step_key=step_key,
                priority=priority,
                should_assign=has_unassigned_slots,
            )

        # if the step is not assigned (i.e. has not been popped from queue), block the claim
        claim_status = self.check_concurrency_claim(
            concurrency_key=concurrency_key, run_id=run_id, step_key=step_key
        )
        if claim_status.is_claimed or not claim_status.is_assigned:
            return claim_status

        # attempt to claim a concurrency slot... this should generally work because we only assign
        # based on the number of unclaimed slots, but this should act as a safeguard, using the slot
        # rows as a semaphore
        slot_status = self._claim_concurrency_slot(
            concurrency_key=concurrency_key, run_id=run_id, step_key=step_key
        )
        return claim_status.with_slot_status(slot_status)

    def _claim_concurrency_slot(
        self, concurrency_key: str, run_id: str, step_key: str
    ) -> ConcurrencySlotStatus:
        """Claim a concurrency slot for the step.  Helper method that is called for steps that are
        popped off the priority queue.

        Args:
            concurrency_key (str): The concurrency key to claim.
            run_id (str): The run id to claim a slot for.
            step_key (str): The step key to claim a slot for.
        """
        with self.index_connection() as conn:
            result = conn.execute(
                db_select([ConcurrencySlotsTable.c.id])
                .select_from(ConcurrencySlotsTable)
                .where(
                    db.and_(
                        ConcurrencySlotsTable.c.concurrency_key == concurrency_key,
                        ConcurrencySlotsTable.c.step_key == None,  # noqa: E711
                        ConcurrencySlotsTable.c.deleted == False,  # noqa: E712
                    )
                )
                .with_for_update(skip_locked=True)
                .limit(1)
            ).fetchone()
            if not result or not result[0]:
                return ConcurrencySlotStatus.BLOCKED
            if not conn.execute(
                ConcurrencySlotsTable.update()
                .values(run_id=run_id, step_key=step_key)
                .where(ConcurrencySlotsTable.c.id == result[0])
            ).rowcount:
                return ConcurrencySlotStatus.BLOCKED

            return ConcurrencySlotStatus.CLAIMED

    def get_pool_limits(self) -> Sequence[PoolLimit]:
        self._reconcile_concurrency_limits_from_slots()
        # initialize outside of connection context
        has_default_col = self.has_default_pool_limit_col
        with self.index_connection() as conn:
            if self.has_concurrency_limits_table and has_default_col:
                query = db_select(
                    [
                        ConcurrencyLimitsTable.c.concurrency_key,
                        ConcurrencyLimitsTable.c.limit,
                        ConcurrencyLimitsTable.c.using_default_limit,
                    ]
                ).select_from(ConcurrencyLimitsTable)
                rows = conn.execute(query).fetchall()
                return [
                    PoolLimit(
                        name=cast(str, row[0]),
                        limit=cast(int, row[1]),
                        from_default=cast(bool, row[2]),
                    )
                    for row in rows
                ]

            if self.has_concurrency_limits_table:
                query = db_select(
                    [
                        ConcurrencyLimitsTable.c.concurrency_key,
                        ConcurrencyLimitsTable.c.limit,
                    ]
                ).select_from(ConcurrencyLimitsTable)
            else:
                query = (
                    db_select(
                        [
                            ConcurrencySlotsTable.c.concurrency_key,
                            db.func.count().label("count"),
                        ]
                    )
                    .where(
                        ConcurrencySlotsTable.c.deleted == False,  # noqa: E712
                    )
                    .group_by(
                        ConcurrencySlotsTable.c.concurrency_key,
                    )
                )
            rows = conn.execute(query).fetchall()
            return [
                PoolLimit(
                    name=cast(str, row[0]),
                    limit=cast(int, row[1]),
                    from_default=False,
                )
                for row in rows
            ]

    def get_concurrency_keys(self) -> set[str]:
        self._reconcile_concurrency_limits_from_slots()

        """Get the set of concurrency limited keys."""
        with self.index_connection() as conn:
            if self.has_concurrency_limits_table:
                query = db_select([ConcurrencyLimitsTable.c.concurrency_key]).select_from(
                    ConcurrencyLimitsTable
                )
            else:
                query = (
                    db_select([ConcurrencySlotsTable.c.concurrency_key])
                    .select_from(ConcurrencySlotsTable)
                    .where(ConcurrencySlotsTable.c.deleted == False)  # noqa: E712
                    .distinct()
                )
            rows = conn.execute(query).fetchall()
            return {cast(str, row[0]) for row in rows}

    def get_concurrency_info(self, concurrency_key: str) -> ConcurrencyKeyInfo:
        """Get the list of concurrency slots for a given concurrency key.

        Args:
            concurrency_key (str): The concurrency key to get the slots for.

        Returns:
            List[Tuple[str, int]]: A list of tuples of run_id and the number of slots it is
                occupying for the given concurrency key.
        """
        with self.index_connection() as conn:
            slot_query = (
                db_select(
                    [
                        ConcurrencySlotsTable.c.run_id,
                        ConcurrencySlotsTable.c.step_key,
                        ConcurrencySlotsTable.c.deleted,
                    ]
                )
                .select_from(ConcurrencySlotsTable)
                .where(ConcurrencySlotsTable.c.concurrency_key == concurrency_key)
            )
            slot_rows = db_fetch_mappings(conn, slot_query)
            slot_count = len([slot_row for slot_row in slot_rows if not slot_row["deleted"]])

            limit = slot_count
            using_default = False

            if self.has_concurrency_limits_table:
                limit_row = conn.execute(
                    db_select(
                        [
                            ConcurrencyLimitsTable.c.limit,
                            ConcurrencyLimitsTable.c.using_default_limit,
                        ]
                    ).where(ConcurrencyLimitsTable.c.concurrency_key == concurrency_key)
                ).fetchone()

                if limit_row:
                    limit = cast(int, limit_row[0])
                    using_default = cast(bool, limit_row[1])
                elif not slot_count:
                    limit = self._instance.global_op_concurrency_default_limit
                    using_default = True

            pending_query = (
                db_select(
                    [
                        PendingStepsTable.c.run_id,
                        PendingStepsTable.c.step_key,
                        PendingStepsTable.c.assigned_timestamp,
                        PendingStepsTable.c.create_timestamp,
                        PendingStepsTable.c.priority,
                    ]
                )
                .select_from(PendingStepsTable)
                .where(PendingStepsTable.c.concurrency_key == concurrency_key)
            )
            pending_rows = db_fetch_mappings(conn, pending_query)

            return ConcurrencyKeyInfo(
                concurrency_key=concurrency_key,
                slot_count=slot_count,
                claimed_slots=[
                    ClaimedSlotInfo(run_id=slot_row["run_id"], step_key=slot_row["step_key"])
                    for slot_row in slot_rows
                    if slot_row["run_id"]
                ],
                pending_steps=[
                    PendingStepInfo(
                        run_id=row["run_id"],
                        step_key=row["step_key"],
                        enqueued_timestamp=utc_datetime_from_naive(row["create_timestamp"]),
                        assigned_timestamp=utc_datetime_from_naive(row["assigned_timestamp"])
                        if row["assigned_timestamp"]
                        else None,
                        priority=row["priority"],
                    )
                    for row in pending_rows
                ],
                limit=limit,
                using_default_limit=using_default,
            )

    def get_concurrency_run_ids(self) -> set[str]:
        with self.index_connection() as conn:
            rows = conn.execute(db_select([PendingStepsTable.c.run_id]).distinct()).fetchall()
            return set([cast(str, row[0]) for row in rows])

    def free_concurrency_slots_for_run(self, run_id: str) -> None:
        self._free_concurrency_slots(run_id=run_id)
        removed_assigned_concurrency_keys = self._remove_pending_steps(run_id=run_id)
        if removed_assigned_concurrency_keys:
            # assign any pending steps that can now claim a slot
            self.assign_pending_steps(removed_assigned_concurrency_keys)

    def free_concurrency_slot_for_step(self, run_id: str, step_key: str) -> None:
        self._free_concurrency_slots(run_id=run_id, step_key=step_key)
        removed_assigned_concurrency_keys = self._remove_pending_steps(
            run_id=run_id, step_key=step_key
        )
        if removed_assigned_concurrency_keys:
            # assign any pending steps that can now claim a slot
            self.assign_pending_steps(removed_assigned_concurrency_keys)

    def _free_concurrency_slots(self, run_id: str, step_key: Optional[str] = None) -> Sequence[str]:
        """Frees concurrency slots for a given run/step.

        Args:
            run_id (str): The run id to free the slots for.
            step_key (Optional[str]): The step key to free the slots for. If not provided, all the
                slots for all the steps of the run will be freed.
        """
        with self.index_connection() as conn:
            # first delete any rows that apply and are marked as deleted.  This happens when the
            # configured number of slots has been reduced, and some of the pruned slots included
            # ones that were already allocated to the run/step
            delete_query = ConcurrencySlotsTable.delete().where(
                db.and_(
                    ConcurrencySlotsTable.c.run_id == run_id,
                    ConcurrencySlotsTable.c.deleted == True,  # noqa: E712
                )
            )
            if step_key:
                delete_query = delete_query.where(ConcurrencySlotsTable.c.step_key == step_key)
            conn.execute(delete_query)

            # next, fetch the slots to free up, while grabbing the concurrency keys so that we can
            # allocate any pending steps from the queue for the freed slots, if necessary
            select_query = (
                db_select([ConcurrencySlotsTable.c.id, ConcurrencySlotsTable.c.concurrency_key])
                .select_from(ConcurrencySlotsTable)
                .where(ConcurrencySlotsTable.c.run_id == run_id)
                .with_for_update()
            )
            if step_key:
                select_query = select_query.where(ConcurrencySlotsTable.c.step_key == step_key)
            rows = conn.execute(select_query).fetchall()
            if not rows:
                return []

            # now, actually free the slots
            conn.execute(
                ConcurrencySlotsTable.update()
                .values(run_id=None, step_key=None)
                .where(
                    db.and_(
                        ConcurrencySlotsTable.c.id.in_([row[0] for row in rows]),
                    )
                )
            )

            # return the concurrency keys for the freed slots
            return [cast(str, row[1]) for row in rows]

    def store_asset_check_event(self, event: EventLogEntry, event_id: Optional[int]) -> None:
        check.inst_param(event, "event", EventLogEntry)
        check.opt_int_param(event_id, "event_id")

        check.invariant(
            self.supports_asset_checks,
            "Asset checks require a database schema migration. Run `dagster instance migrate`.",
        )

        if event.dagster_event_type == DagsterEventType.ASSET_CHECK_EVALUATION_PLANNED:
            self._store_asset_check_evaluation_planned(event, event_id)
        if event.dagster_event_type == DagsterEventType.ASSET_CHECK_EVALUATION:
            if event.run_id == "" or event.run_id is None:
                self._store_runless_asset_check_evaluation(event, event_id)
            else:
                self._update_asset_check_evaluation(event, event_id)

    def _store_asset_check_evaluation_planned(
        self, event: EventLogEntry, event_id: Optional[int]
    ) -> None:
        planned = cast(
            AssetCheckEvaluationPlanned, check.not_none(event.dagster_event).event_specific_data
        )
        with self.index_connection() as conn:
            conn.execute(
                AssetCheckExecutionsTable.insert().values(
                    asset_key=planned.asset_key.to_string(),
                    check_name=planned.check_name,
                    run_id=event.run_id,
                    execution_status=AssetCheckExecutionRecordStatus.PLANNED.value,
                    evaluation_event=serialize_value(event),
                    evaluation_event_timestamp=self._event_insert_timestamp(event),
                )
            )

    def _event_insert_timestamp(self, event):
        # Postgres requires a datetime that is in UTC but has no timezone info
        return datetime.fromtimestamp(event.timestamp, timezone.utc).replace(tzinfo=None)

    def _store_runless_asset_check_evaluation(
        self, event: EventLogEntry, event_id: Optional[int]
    ) -> None:
        evaluation = cast(
            AssetCheckEvaluation, check.not_none(event.dagster_event).event_specific_data
        )
        with self.index_connection() as conn:
            conn.execute(
                AssetCheckExecutionsTable.insert().values(
                    asset_key=evaluation.asset_key.to_string(),
                    check_name=evaluation.check_name,
                    run_id=event.run_id,
                    execution_status=(
                        AssetCheckExecutionRecordStatus.SUCCEEDED.value
                        if evaluation.passed
                        else AssetCheckExecutionRecordStatus.FAILED.value
                    ),
                    evaluation_event=serialize_value(event),
                    evaluation_event_timestamp=self._event_insert_timestamp(event),
                    evaluation_event_storage_id=event_id,
                    materialization_event_storage_id=(
                        evaluation.target_materialization_data.storage_id
                        if evaluation.target_materialization_data
                        else None
                    ),
                )
            )

    def _update_asset_check_evaluation(self, event: EventLogEntry, event_id: Optional[int]) -> None:
        evaluation = cast(
            AssetCheckEvaluation, check.not_none(event.dagster_event).event_specific_data
        )
        with self.index_connection() as conn:
            rows_updated = conn.execute(
                AssetCheckExecutionsTable.update()
                .where(
                    # (asset_key, check_name, run_id) uniquely identifies the row created for the planned event
                    db.and_(
                        AssetCheckExecutionsTable.c.asset_key == evaluation.asset_key.to_string(),
                        AssetCheckExecutionsTable.c.check_name == evaluation.check_name,
                        AssetCheckExecutionsTable.c.run_id == event.run_id,
                    )
                )
                .values(
                    execution_status=(
                        AssetCheckExecutionRecordStatus.SUCCEEDED.value
                        if evaluation.passed
                        else AssetCheckExecutionRecordStatus.FAILED.value
                    ),
                    evaluation_event=serialize_value(event),
                    evaluation_event_timestamp=self._event_insert_timestamp(event),
                    evaluation_event_storage_id=event_id,
                    materialization_event_storage_id=(
                        evaluation.target_materialization_data.storage_id
                        if evaluation.target_materialization_data
                        else None
                    ),
                )
            ).rowcount

            # TODO fix the idx_asset_check_executions_unique index so that this can be a single
            # upsert
            if rows_updated == 0:
                rows_updated = conn.execute(
                    AssetCheckExecutionsTable.insert().values(
                        asset_key=evaluation.asset_key.to_string(),
                        check_name=evaluation.check_name,
                        run_id=event.run_id,
                        execution_status=(
                            AssetCheckExecutionRecordStatus.SUCCEEDED.value
                            if evaluation.passed
                            else AssetCheckExecutionRecordStatus.FAILED.value
                        ),
                        evaluation_event=serialize_value(event),
                        evaluation_event_timestamp=datetime.utcfromtimestamp(event.timestamp),
                        evaluation_event_storage_id=event_id,
                        materialization_event_storage_id=(
                            evaluation.target_materialization_data.storage_id
                            if evaluation.target_materialization_data
                            else None
                        ),
                    )
                ).rowcount

        # 0 isn't normally expected, but occurs with the external instance of step launchers where
        # they don't have planned events.
        if rows_updated > 1:
            raise DagsterInvariantViolationError(
                f"Updated {rows_updated} rows for asset check evaluation {evaluation.asset_check_key} "
                "as a result of duplicate AssetCheckPlanned events."
            )

    def get_asset_check_execution_history(
        self,
        check_key: AssetCheckKey,
        limit: int,
        cursor: Optional[int] = None,
        status: Optional[AbstractSet[AssetCheckExecutionRecordStatus]] = None,
    ) -> Sequence[AssetCheckExecutionRecord]:
        check.inst_param(check_key, "key", AssetCheckKey)
        check.int_param(limit, "limit")
        check.opt_int_param(cursor, "cursor")

        query = (
            db_select(
                [
                    AssetCheckExecutionsTable.c.id,
                    AssetCheckExecutionsTable.c.run_id,
                    AssetCheckExecutionsTable.c.execution_status,
                    AssetCheckExecutionsTable.c.evaluation_event,
                    AssetCheckExecutionsTable.c.create_timestamp,
                ]
            )
            .where(
                db.and_(
                    AssetCheckExecutionsTable.c.asset_key == check_key.asset_key.to_string(),
                    AssetCheckExecutionsTable.c.check_name == check_key.name,
                )
            )
            .order_by(AssetCheckExecutionsTable.c.id.desc())
        ).limit(limit)

        if cursor:
            query = query.where(AssetCheckExecutionsTable.c.id < cursor)

        if status:
            query = query.where(
                AssetCheckExecutionsTable.c.execution_status.in_([s.value for s in status])
            )

        with self.index_connection() as conn:
            rows = db_fetch_mappings(conn, query)

        return [AssetCheckExecutionRecord.from_db_row(row, key=check_key) for row in rows]

    def get_latest_asset_check_execution_by_key(
        self, check_keys: Sequence[AssetCheckKey]
    ) -> Mapping[AssetCheckKey, AssetCheckExecutionRecord]:
        if not check_keys:
            return {}

        latest_ids_subquery = db_subquery(
            db_select(
                [
                    db.func.max(AssetCheckExecutionsTable.c.id).label("id"),
                ]
            )
            .where(
                db.and_(
                    AssetCheckExecutionsTable.c.asset_key.in_(
                        [key.asset_key.to_string() for key in check_keys]
                    ),
                    AssetCheckExecutionsTable.c.check_name.in_([key.name for key in check_keys]),
                )
            )
            .group_by(
                AssetCheckExecutionsTable.c.asset_key,
                AssetCheckExecutionsTable.c.check_name,
            )
        )

        query = db_select(
            [
                AssetCheckExecutionsTable.c.id,
                AssetCheckExecutionsTable.c.asset_key,
                AssetCheckExecutionsTable.c.check_name,
                AssetCheckExecutionsTable.c.run_id,
                AssetCheckExecutionsTable.c.execution_status,
                AssetCheckExecutionsTable.c.evaluation_event,
                AssetCheckExecutionsTable.c.create_timestamp,
            ]
        ).select_from(
            AssetCheckExecutionsTable.join(
                latest_ids_subquery,
                db.and_(
                    AssetCheckExecutionsTable.c.id == latest_ids_subquery.c.id,
                ),
            )
        )

        with self.index_connection() as conn:
            rows = db_fetch_mappings(conn, query)

        results = {}
        for row in rows:
            check_key = AssetCheckKey(
                asset_key=check.not_none(AssetKey.from_db_string(cast(str, row["asset_key"]))),
                name=cast(str, row["check_name"]),
            )
            results[check_key] = AssetCheckExecutionRecord.from_db_row(row, key=check_key)
        return results

    @property
    def supports_asset_checks(self):  # pyright: ignore[reportIncompatibleMethodOverride]
        return self.has_table(AssetCheckExecutionsTable.name)

    def get_latest_planned_materialization_info(
        self,
        asset_key: AssetKey,
        partition: Optional[str] = None,
    ) -> Optional[PlannedMaterializationInfo]:
        records = self._get_event_records(
            event_records_filter=EventRecordsFilter(
                DagsterEventType.ASSET_MATERIALIZATION_PLANNED,
                asset_key=asset_key,
                asset_partitions=[partition] if partition else None,
            ),
            limit=1,
            ascending=False,
        )
        if not records:
            return None

        return PlannedMaterializationInfo(
            storage_id=records[0].storage_id,
            run_id=records[0].run_id,
        )

    def _get_partition_data_versions(
        self,
        asset_key: AssetKey,
        partitions: Sequence[str],
        before_storage_id: Optional[int] = None,
        after_storage_id: Optional[int] = None,
    ) -> dict[str, str]:
        partition_subquery = db_select(
            [SqlEventLogStorageTable.c.partition, SqlEventLogStorageTable.c.id]
        ).where(
            db.and_(
                db.or_(
                    SqlEventLogStorageTable.c.dagster_event_type
                    == DagsterEventType.ASSET_MATERIALIZATION.value,
                    SqlEventLogStorageTable.c.dagster_event_type
                    == DagsterEventType.ASSET_OBSERVATION.value,
                ),
                SqlEventLogStorageTable.c.asset_key == asset_key.to_string(),
                SqlEventLogStorageTable.c.partition.in_(partitions),
            )
        )
        data_version_subquery = db_select(
            [
                AssetEventTagsTable.c.event_id,
                AssetEventTagsTable.c.value,
            ]
        ).where(
            db.and_(
                AssetEventTagsTable.c.key == DATA_VERSION_TAG,
                AssetEventTagsTable.c.asset_key == asset_key.to_string(),
            )
        )

        if before_storage_id is not None:
            partition_subquery = partition_subquery.where(
                SqlEventLogStorageTable.c.id < before_storage_id
            )
            data_version_subquery = data_version_subquery.where(
                AssetEventTagsTable.c.event_id < before_storage_id
            )
        if after_storage_id is not None:
            partition_subquery = partition_subquery.where(
                SqlEventLogStorageTable.c.id > after_storage_id
            )
            data_version_subquery = data_version_subquery.where(
                AssetEventTagsTable.c.event_id > after_storage_id
            )

        partition_subquery = db_subquery(partition_subquery, "partition_subquery")
        data_version_subquery = db_subquery(data_version_subquery, "data_version_subquery")
        data_version_by_partition_subquery = db_subquery(
            db_select(
                [
                    partition_subquery.c.partition,
                    data_version_subquery.c.value,
                    db.func.rank()
                    .over(
                        order_by=db.desc(partition_subquery.c.id),
                        partition_by=partition_subquery.c.partition,
                    )
                    .label("rank"),
                ]
            ).select_from(
                partition_subquery.join(
                    data_version_subquery,
                    data_version_subquery.c.event_id == partition_subquery.c.id,
                )
            ),
            "data_version_by_partition_subquery",
        )
        latest_data_version_by_partition_query = (
            db_select(
                [
                    data_version_by_partition_subquery.c.partition,
                    data_version_by_partition_subquery.c.value,
                ]
            )
            .order_by(data_version_by_partition_subquery.c.rank.asc())
            .where(data_version_by_partition_subquery.c.rank == 1)
        )

        with self.index_connection() as conn:
            rows = conn.execute(latest_data_version_by_partition_query).fetchall()

        return {cast(str, row[0]): cast(str, row[1]) for row in rows}

    def get_updated_data_version_partitions(
        self, asset_key: AssetKey, partitions: Iterable[str], since_storage_id: int
    ) -> set[str]:
        previous_data_versions = self._get_partition_data_versions(
            asset_key=asset_key,
            partitions=list(partitions),
            before_storage_id=since_storage_id + 1,
        )
        current_data_versions = self._get_partition_data_versions(
            asset_key=asset_key,
            partitions=list(partitions),
            after_storage_id=since_storage_id,
        )

        updated_partitions = set()
        for partition, data_version in current_data_versions.items():
            previous_data_version = previous_data_versions.get(partition)
            if data_version and data_version != previous_data_version:
                updated_partitions.add(partition)

        return updated_partitions


def _get_from_row(row: SqlAlchemyRow, column: str) -> object:
    """Utility function for extracting a column from a sqlalchemy row proxy, since '_asdict' is not
    supported in sqlalchemy 1.3.
    """
    if column not in row.keys():
        return None
    return row[column]
