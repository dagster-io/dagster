from collections import OrderedDict
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, ContextManager, cast  # noqa: UP035

import dagster._check as check
import sqlalchemy as db
import sqlalchemy.dialects as db_dialects
import sqlalchemy.pool as db_pool
from dagster._config.config_schema import UserConfigSchema
from dagster._core.errors import DagsterInvariantViolationError
from dagster._core.event_api import EventHandlerFn
from dagster._core.events import ASSET_CHECK_EVENTS, ASSET_EVENTS, BATCH_WRITABLE_EVENTS
from dagster._core.events.log import EventLogEntry
from dagster._core.storage.asset_check_execution_record import AssetCheckExecutionRecordStatus
from dagster._core.storage.config import pg_config
from dagster._core.storage.event_log import (
    AssetKeyTable,
    DynamicPartitionsTable,
    SqlEventLogStorage,
    SqlEventLogStorageMetadata,
    SqlEventLogStorageTable,
)
from dagster._core.storage.event_log.base import EventLogCursor
from dagster._core.storage.event_log.migration import ASSET_KEY_INDEX_COLS
from dagster._core.storage.event_log.polling_event_watcher import SqlPollingEventWatcher
from dagster._core.storage.event_log.schema import AssetCheckExecutionsTable
from dagster._core.storage.sql import (
    AlembicVersion,
    check_alembic_revision,
    create_engine,
    run_alembic_upgrade,
    stamp_alembic_rev,
)
from dagster._core.storage.sqlalchemy_compat import db_result, db_select
from dagster._serdes import (
    ConfigurableClass,
    ConfigurableClassData,
    deserialize_value,
    serialize_value,
)
from sqlalchemy import event
from sqlalchemy.engine import Connection

from dagster_postgres.utils import (
    create_pg_connection,
    create_pg_engine,
    get_token_provider_from_config,
    pg_alembic_config,
    pg_url_from_config,
    retry_pg_connection_fn,
    retry_pg_creation_fn,
    set_pg_statement_timeout,
)

if TYPE_CHECKING:
    from dagster._core.definitions.asset_checks.asset_check_evaluation import (
        AssetCheckEvaluationPlanned,
    )

    from dagster_postgres.auth import PgTokenProvider

CHANNEL_NAME = "run_events"


class PostgresEventLogStorage(SqlEventLogStorage, ConfigurableClass):
    """Postgres-backed event log storage.

    Users should not directly instantiate this class; it is instantiated by internal machinery when
    ``dagster-webserver`` and ``dagster-graphql`` load, based on the values in the ``dagster.yaml`` file in
    ``$DAGSTER_HOME``. Configuration of this class should be done by setting values in that file.

    To use Postgres for all of the components of your instance storage, you can add the following
    block to your ``dagster.yaml``:

    .. literalinclude:: ../../../../../../examples/docs_snippets/docs_snippets/deployment/oss/dagster-pg.yaml
       :caption: dagster.yaml
       :lines: 1-8
       :language: YAML

    If you are configuring the different storage components separately and are specifically
    configuring your event log storage to use Postgres, you can add a block such as the following
    to your ``dagster.yaml``:

    .. literalinclude:: ../../../../../../examples/docs_snippets/docs_snippets/deployment/oss/dagster-pg-legacy.yaml
       :caption: dagster.yaml
       :lines: 12-21
       :language: YAML

    Note that the fields in this config are :py:class:`~dagster.StringSource` and
    :py:class:`~dagster.IntSource` and can be configured from environment variables.

    """

    def __init__(
        self,
        postgres_url: str,
        should_autocreate_tables: bool = True,
        inst_data: ConfigurableClassData | None = None,
        token_provider: "PgTokenProvider | None" = None,
    ):
        self._inst_data = check.opt_inst_param(inst_data, "inst_data", ConfigurableClassData)
        self.postgres_url = check.str_param(postgres_url, "postgres_url")
        self.should_autocreate_tables = check.bool_param(
            should_autocreate_tables, "should_autocreate_tables"
        )
        self._token_provider = token_provider

        # Default to not holding any connections open to prevent accumulating connections per DagsterInstance
        self._engine = create_pg_engine(
            self.postgres_url,
            self._token_provider,
            isolation_level="AUTOCOMMIT",
            poolclass=db_pool.NullPool,
        )
        self._event_watcher: SqlPollingEventWatcher | None = None

        self._secondary_index_cache = {}

        # Stamp and create tables if the main table does not exist (we can't check alembic
        # revision because alembic config may be shared with other storage classes)
        if self.should_autocreate_tables:
            table_names = retry_pg_connection_fn(lambda: db.inspect(self._engine).get_table_names())
            if "event_logs" not in table_names:
                retry_pg_creation_fn(self._init_db)
                self.reindex_events()
                self.reindex_assets()

        super().__init__()

    def _init_db(self) -> None:
        with self._connect() as conn:
            with conn.begin():
                SqlEventLogStorageMetadata.create_all(conn)
                stamp_alembic_rev(pg_alembic_config(__file__), conn)

    def optimize_for_webserver(
        self, statement_timeout: int, pool_recycle: int, max_overflow: int
    ) -> None:
        # When running in dagster-webserver, hold an open connection and set statement_timeout
        kwargs: dict[str, Any] = {
            "isolation_level": "AUTOCOMMIT",
            "pool_size": 1,
            "pool_recycle": pool_recycle,
            "max_overflow": max_overflow,
        }
        existing_options = self._engine.url.query.get("options")
        if existing_options:
            kwargs["connect_args"] = {"options": existing_options}
        self._engine = create_pg_engine(self.postgres_url, self._token_provider, **kwargs)
        event.listen(
            self._engine,
            "connect",
            lambda connection, _: set_pg_statement_timeout(connection, statement_timeout),
        )

    def upgrade(self) -> None:
        alembic_config = pg_alembic_config(__file__)
        with self._connect() as conn:
            run_alembic_upgrade(alembic_config, conn)

    @property
    def inst_data(self) -> ConfigurableClassData | None:
        return self._inst_data

    @classmethod
    def config_type(cls) -> UserConfigSchema:
        return pg_config()

    @classmethod
    def from_config_value(
        cls, inst_data: ConfigurableClassData | None, config_value: Mapping[str, Any]
    ) -> "PostgresEventLogStorage":
        return PostgresEventLogStorage(
            inst_data=inst_data,
            postgres_url=pg_url_from_config(config_value),
            should_autocreate_tables=config_value.get("should_autocreate_tables", True),
            token_provider=get_token_provider_from_config(config_value),
        )

    @staticmethod
    def create_clean_storage(
        conn_string: str, should_autocreate_tables: bool = True
    ) -> "PostgresEventLogStorage":
        engine = create_engine(
            conn_string, isolation_level="AUTOCOMMIT", poolclass=db_pool.NullPool
        )
        try:
            SqlEventLogStorageMetadata.drop_all(engine)
        finally:
            engine.dispose()

        return PostgresEventLogStorage(conn_string, should_autocreate_tables)

    def store_event(self, event: EventLogEntry) -> None:
        """Store an event corresponding to a run.

        Args:
            event (EventLogEntry): The event to store.
        """
        check.inst_param(event, "event", EventLogEntry)
        insert_event_statement = self.prepare_insert_event(event)  # from SqlEventLogStorage.py
        with self._connect() as conn:
            result = conn.execute(
                insert_event_statement.returning(
                    SqlEventLogStorageTable.c.run_id, SqlEventLogStorageTable.c.id
                )
            )
            res = result.fetchone()
            result.close()

            # LISTEN/NOTIFY no longer used for pg event watch - preserved here to support version skew
            conn.execute(
                db.text(f"""NOTIFY {CHANNEL_NAME}, :notify_id; """),
                {"notify_id": res[0] + "_" + str(res[1])},  # type: ignore
            )
            event_id = int(res[1])  # type: ignore

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

    def store_event_batch(self, events: Sequence[EventLogEntry]) -> None:
        from dagster import DagsterEventType

        check.sequence_param(events, "event", of_type=EventLogEntry)

        event_types = {event.get_dagster_event().event_type for event in events}

        check.invariant(
            all(event_type in BATCH_WRITABLE_EVENTS for event_type in event_types),
            f"{BATCH_WRITABLE_EVENTS} are the only currently supported events for batch writes.",
        )
        events = [
            event
            for event in events
            if not event.get_dagster_event().is_asset_failed_to_materialize
        ]
        if len(events) == 0:
            return
        # recompute after filtering (ASSET_FAILED_TO_MATERIALIZE may have been the only type)
        event_types = {event.get_dagster_event().event_type for event in events}

        if event_types == {DagsterEventType.ASSET_MATERIALIZATION} or event_types == {
            DagsterEventType.ASSET_OBSERVATION
        }:
            insert_event_statement = self.prepare_insert_event_batch(events)
            with self._connect() as conn:
                result = conn.execute(
                    insert_event_statement.returning(SqlEventLogStorageTable.c.id)
                )
                event_ids = [cast("int", row[0]) for row in result.fetchall()]

            # We only update the asset table with the last event
            self.store_asset_event(events[-1], event_ids[-1])

            if any(event_id is None for event_id in event_ids):
                raise DagsterInvariantViolationError(
                    "Cannot store asset event tags for null event id."
                )

            self.store_asset_event_tags(events, event_ids)
            return

        planned_event_types = {
            DagsterEventType.ASSET_MATERIALIZATION_PLANNED,
            DagsterEventType.ASSET_CHECK_EVALUATION_PLANNED,
        }
        if event_types.issubset(planned_event_types):
            self._store_planned_events_batch(events)
            return

        return super().store_event_batch(events)

    def _store_planned_events_batch(self, events: Sequence[EventLogEntry]) -> None:
        """Bulk-write ASSET_MATERIALIZATION_PLANNED and ASSET_CHECK_EVALUATION_PLANNED events.

        Replaces O(N) per-event inserts (one event-log row, one asset-key upsert, and one
        asset-check-execution row per event) with at most three statements: one bulk INSERT
        into the event log, one bulk upsert into the asset_keys table, and one bulk INSERT
        into the asset_check_executions table.

        Scope: this fast path is Postgres-only. `SqliteEventLogStorage`, the in-memory
        storage, and `dagster-mysql` (`MySQLEventLogStorage`) still inherit the base
        `EventLogStorage.store_event_batch` per-event loop. They get correct results but
        not the speedup. Generalizing to those backends requires per-dialect upsert syntax
        (`INSERT OR REPLACE` / `INSERT ... ON DUPLICATE KEY UPDATE`) and is intentionally
        deferred -- see the PR description for the follow-up.

        All three statements run on a single connection inside a single explicit transaction.
        On Postgres the engine runs in AUTOCOMMIT isolation level, so a partial failure
        without an enclosing transaction would leave the event_log rows committed while the
        side-table rows were not. Storage callers (`DagsterInstance._store_and_notify`) then
        fall back to per-event `store_event`, which would duplicate event_log rows and
        `asset_check_executions` rows. Wrapping in `conn.begin()` makes the bulk path
        all-or-nothing so that fallback is correct.
        """
        from dagster import DagsterEventType

        insert_event_statement = self.prepare_insert_event_batch(events)
        # Use `index_connection()` so this path honors any subclass override that points
        # the side-table writes (asset_keys, asset_check_executions) at a separate
        # connection/database. For PostgresEventLogStorage in OSS this aliases to
        # `_connect()`, but the abstraction exists for sharded-index setups and the
        # existing materialization fast path's side-table writes (via store_asset_event)
        # go through `index_connection()`. Keeping the convention here means the bulk
        # path doesn't silently bypass the abstraction.
        with self.index_connection() as conn:
            with conn.begin():
                result = conn.execute(
                    insert_event_statement.returning(SqlEventLogStorageTable.c.id)
                )
                event_ids = [cast("int", row[0]) for row in result.fetchall()]

                if any(event_id is None for event_id in event_ids):
                    raise DagsterInvariantViolationError(
                        "Cannot store planned events with null event id."
                    )

                # Pair each event_id (returned in input order) back with its source event.
                mat_planned: list[tuple[EventLogEntry, int]] = []
                check_planned: list[tuple[EventLogEntry, int]] = []
                for log_entry, event_id in zip(events, event_ids):
                    dagster_event = log_entry.get_dagster_event()
                    if dagster_event.is_asset_materialization_planned:
                        mat_planned.append((log_entry, event_id))
                    elif (
                        dagster_event.event_type == DagsterEventType.ASSET_CHECK_EVALUATION_PLANNED
                    ):
                        check_planned.append((log_entry, event_id))

                if mat_planned:
                    self._bulk_upsert_asset_keys_for_planned(conn, mat_planned)
                if check_planned:
                    self._bulk_insert_check_planned_evaluations(conn, check_planned)

    def _bulk_upsert_asset_keys_for_planned(
        self,
        conn: Connection,
        mat_planned: Sequence[tuple[EventLogEntry, int]],
    ) -> None:
        """Upsert AssetKeyTable rows for ASSET_MATERIALIZATION_PLANNED events in one statement.

        Contract: the *last* event per asset key in input order wins, matching the per-event
        behavior of `store_asset_event` (which writes each row sequentially so each successive
        write overwrites the previous). Callers that resort the batch may inadvertently flip
        which event is materialized into AssetKeyTable -- the caller in
        `RunDomain._log_asset_planned_events` sorts by `asset_key.to_db_string()`, which is
        deterministic but independent of this contract.

        Dedup is keyed by `asset_key.to_string()` because that is the value stored in the
        `asset_key` column. `to_db_string()` (used by the upstream sort) is a separate
        normalization and is not interchangeable.
        """
        has_index_cols = self.has_secondary_index(ASSET_KEY_INDEX_COLS)

        latest_by_key: OrderedDict[str, tuple[EventLogEntry, int]] = OrderedDict()
        for log_entry, event_id in mat_planned:
            asset_key = check.not_none(log_entry.get_dagster_event().asset_key)
            latest_by_key[asset_key.to_string()] = (log_entry, event_id)

        rows: list[dict[str, Any]] = []
        for asset_key_str, (log_entry, event_id) in latest_by_key.items():
            values = self._get_asset_entry_values(log_entry, event_id, has_index_cols)
            if not values:
                continue
            rows.append({"asset_key": asset_key_str, **values})

        if not rows:
            return

        # All rows have the same keys (values shape only depends on event type +
        # has_index_cols), so any row's keys are representative.
        update_cols = [key for key in rows[0].keys() if key != "asset_key"]

        stmt = db_dialects.postgresql.insert(AssetKeyTable).values(rows)
        stmt = stmt.on_conflict_do_update(
            index_elements=[AssetKeyTable.c.asset_key],
            set_={col: stmt.excluded[col] for col in update_cols},
        )
        conn.execute(stmt)

    def _bulk_insert_check_planned_evaluations(
        self,
        conn: Connection,
        check_planned: Sequence[tuple[EventLogEntry, int]],
    ) -> None:
        """Insert all AssetCheckExecutionsTable rows for ASSET_CHECK_EVALUATION_PLANNED events
        in one statement, flattening across each event's partitions_subset.
        """
        check.invariant(
            self.supports_asset_checks,
            "Asset checks require a database schema migration. Run `dagster instance migrate`.",
        )

        rows: list[dict[str, Any]] = []
        for log_entry, event_id in check_planned:
            planned = cast(
                "AssetCheckEvaluationPlanned",
                check.not_none(log_entry.dagster_event).event_specific_data,
            )
            partition_keys: Sequence[str | None]
            if planned.partitions_subset:
                partition_keys = list(planned.partitions_subset.get_partition_keys())
            else:
                partition_keys = [None]
            event_timestamp = self._event_insert_timestamp(log_entry)
            serialized_event = serialize_value(log_entry)
            for partition_key in partition_keys:
                rows.append(
                    dict(
                        asset_key=planned.asset_key.to_string(),
                        check_name=planned.check_name,
                        partition=partition_key,
                        run_id=log_entry.run_id,
                        execution_status=AssetCheckExecutionRecordStatus.PLANNED.value,
                        evaluation_event=serialized_event,
                        evaluation_event_timestamp=event_timestamp,
                        evaluation_event_storage_id=event_id,
                    )
                )

        if not rows:
            return

        conn.execute(AssetCheckExecutionsTable.insert().values(rows))

    def store_asset_event(self, event: EventLogEntry, event_id: int) -> None:
        check.inst_param(event, "event", EventLogEntry)
        if not (event.dagster_event and event.dagster_event.asset_key):
            return

        # We switched to storing the entire event record of the last materialization instead of just
        # the AssetMaterialization object, so that we have access to metadata like timestamp,
        # job, run_id, etc.
        #
        # This should make certain asset queries way more performant, without having to do extra
        # queries against the event log.
        #
        # This should be accompanied by a schema change in 0.12.0, renaming `last_materialization`
        # to `last_materialization_event`, for clarity.  For now, we should do some back-compat.
        #
        # https://github.com/dagster-io/dagster/issues/3945

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

        # The AssetKeyTable also contains a `last_run_id` column that is updated upon asset
        # materialization. This column was not being used until the below PR. This new change
        # writes to the column upon `ASSET_MATERIALIZATION_PLANNED` events to fetch the last
        # run id for a set of assets in one roundtrip call to event log storage.
        # https://github.com/dagster-io/dagster/pull/7319

        values = self._get_asset_entry_values(
            event, event_id, self.has_secondary_index(ASSET_KEY_INDEX_COLS)
        )
        with self.index_connection() as conn:
            query = db_dialects.postgresql.insert(AssetKeyTable).values(
                asset_key=event.dagster_event.asset_key.to_string(),
                **values,
            )
            if values:
                query = query.on_conflict_do_update(
                    index_elements=[AssetKeyTable.c.asset_key],
                    set_=dict(**values),
                )
            else:
                query = query.on_conflict_do_nothing()
            conn.execute(query)

    def add_dynamic_partitions(
        self, partitions_def_name: str, partition_keys: Sequence[str]
    ) -> None:
        if not partition_keys:
            return

        # Overload base implementation to push upsert logic down into the db layer
        self._check_partitions_table()
        with self.index_connection() as conn:
            conn.execute(
                db_dialects.postgresql.insert(DynamicPartitionsTable)
                .values(
                    [
                        dict(partitions_def_name=partitions_def_name, partition=partition_key)
                        for partition_key in partition_keys
                    ]
                )
                .on_conflict_do_nothing(),
            )

    def _connect(self) -> ContextManager[Connection]:
        return create_pg_connection(self._engine)

    def run_connection(self, run_id: str | None = None) -> ContextManager[Connection]:
        return self._connect()

    def index_connection(self) -> ContextManager[Connection]:
        return self._connect()

    @contextmanager
    def index_transaction(self) -> Iterator[Connection]:
        """Context manager yielding a connection to the index shard that has begun a transaction."""
        with self.index_connection() as conn:
            if conn.in_transaction():
                yield conn
            else:
                conn = conn.execution_options(isolation_level="READ COMMITTED")  # noqa: PLW2901
                with conn.begin():
                    yield conn

    def has_table(self, table_name: str) -> bool:
        return bool(self._engine.dialect.has_table(self._engine.connect(), table_name))

    def has_secondary_index(self, name: str) -> bool:
        if name not in self._secondary_index_cache:
            self._secondary_index_cache[name] = super().has_secondary_index(name)
        return self._secondary_index_cache[name]

    def enable_secondary_index(self, name: str) -> None:
        super().enable_secondary_index(name)
        if name in self._secondary_index_cache:
            del self._secondary_index_cache[name]

    def watch(
        self,
        run_id: str,
        cursor: str | None,
        callback: EventHandlerFn,
    ) -> None:
        if cursor and EventLogCursor.parse(cursor).is_offset_cursor():
            check.failed("Cannot call `watch` with an offset cursor")
        if self._event_watcher is None:
            self._event_watcher = SqlPollingEventWatcher(self)

        self._event_watcher.watch_run(run_id, cursor, callback)

    def _gen_event_log_entry_from_cursor(self, cursor) -> EventLogEntry:
        with (
            self._engine.connect() as conn,
            db_result(
                conn,
                db_select([SqlEventLogStorageTable.c.event]).where(
                    SqlEventLogStorageTable.c.id == cursor
                ),
            ) as cursor_res,
        ):
            return deserialize_value(cursor_res.scalar(), EventLogEntry)

    def end_watch(self, run_id: str, handler: EventHandlerFn) -> None:
        if self._event_watcher:
            self._event_watcher.unwatch_run(run_id, handler)

    def dispose(self) -> None:
        if self._event_watcher:
            self._event_watcher.close()
            self._event_watcher = None

    def alembic_version(self) -> AlembicVersion:
        alembic_config = pg_alembic_config(__file__)
        with self._connect() as conn:
            return check_alembic_revision(alembic_config, conn)
