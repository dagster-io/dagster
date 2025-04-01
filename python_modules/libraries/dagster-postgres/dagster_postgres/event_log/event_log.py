from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from typing import Any, ContextManager, Optional, cast  # noqa: UP035

import dagster._check as check
import sqlalchemy as db
import sqlalchemy.dialects as db_dialects
import sqlalchemy.pool as db_pool
from dagster._config.config_schema import UserConfigSchema
from dagster._core.errors import DagsterInvariantViolationError
from dagster._core.event_api import EventHandlerFn
from dagster._core.events import ASSET_CHECK_EVENTS, ASSET_EVENTS, BATCH_WRITABLE_EVENTS
from dagster._core.events.log import EventLogEntry
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
from dagster._core.storage.sql import (
    AlembicVersion,
    check_alembic_revision,
    create_engine,
    run_alembic_upgrade,
    stamp_alembic_rev,
)
from dagster._core.storage.sqlalchemy_compat import db_select
from dagster._serdes import ConfigurableClass, ConfigurableClassData, deserialize_value
from sqlalchemy import event
from sqlalchemy.engine import Connection

from dagster_postgres.utils import (
    create_pg_connection,
    pg_alembic_config,
    pg_url_from_config,
    retry_pg_connection_fn,
    retry_pg_creation_fn,
    set_pg_statement_timeout,
)

CHANNEL_NAME = "run_events"


class PostgresEventLogStorage(SqlEventLogStorage, ConfigurableClass):
    """Postgres-backed event log storage.

    Users should not directly instantiate this class; it is instantiated by internal machinery when
    ``dagster-webserver`` and ``dagster-graphql`` load, based on the values in the ``dagster.yaml`` file in
    ``$DAGSTER_HOME``. Configuration of this class should be done by setting values in that file.

    To use Postgres for all of the components of your instance storage, you can add the following
    block to your ``dagster.yaml``:

    .. literalinclude:: ../../../../../../examples/docs_snippets/docs_snippets/deploying/dagster-pg.yaml
       :caption: dagster.yaml
       :lines: 1-8
       :language: YAML

    If you are configuring the different storage components separately and are specifically
    configuring your event log storage to use Postgres, you can add a block such as the following
    to your ``dagster.yaml``:

    .. literalinclude:: ../../../../../../examples/docs_snippets/docs_snippets/deploying/dagster-pg-legacy.yaml
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
        inst_data: Optional[ConfigurableClassData] = None,
    ):
        self._inst_data = check.opt_inst_param(inst_data, "inst_data", ConfigurableClassData)
        self.postgres_url = check.str_param(postgres_url, "postgres_url")
        self.should_autocreate_tables = check.bool_param(
            should_autocreate_tables, "should_autocreate_tables"
        )

        # Default to not holding any connections open to prevent accumulating connections per DagsterInstance
        self._engine = create_engine(
            self.postgres_url, isolation_level="AUTOCOMMIT", poolclass=db_pool.NullPool
        )
        self._event_watcher: Optional[SqlPollingEventWatcher] = None

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
        kwargs = {
            "isolation_level": "AUTOCOMMIT",
            "pool_size": 1,
            "pool_recycle": pool_recycle,
            "max_overflow": max_overflow,
        }
        existing_options = self._engine.url.query.get("options")
        if existing_options:
            kwargs["connect_args"] = {"options": existing_options}
        self._engine = create_engine(self.postgres_url, **kwargs)
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
    def inst_data(self) -> Optional[ConfigurableClassData]:
        return self._inst_data

    @classmethod
    def config_type(cls) -> UserConfigSchema:
        return pg_config()

    @classmethod
    def from_config_value(
        cls, inst_data: Optional[ConfigurableClassData], config_value: Mapping[str, Any]
    ) -> "PostgresEventLogStorage":
        return PostgresEventLogStorage(
            inst_data=inst_data,
            postgres_url=pg_url_from_config(config_value),
            should_autocreate_tables=config_value.get("should_autocreate_tables", True),
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
        check.sequence_param(events, "event", of_type=EventLogEntry)

        check.invariant(
            all(event.get_dagster_event().event_type in BATCH_WRITABLE_EVENTS for event in events),
            f"{BATCH_WRITABLE_EVENTS} are the only currently supported events for batch writes.",
        )
        events = [
            event
            for event in events
            if not event.get_dagster_event().is_asset_failed_to_materialize
        ]
        if len(events) == 0:
            return

        insert_event_statement = self.prepare_insert_event_batch(events)
        with self._connect() as conn:
            result = conn.execute(insert_event_statement.returning(SqlEventLogStorageTable.c.id))
            event_ids = [cast(int, row[0]) for row in result.fetchall()]

        # We only update the asset table with the last event
        self.store_asset_event(events[-1], event_ids[-1])

        if any(event_id is None for event_id in event_ids):
            raise DagsterInvariantViolationError("Cannot store asset event tags for null event id.")

        self.store_asset_event_tags(events, event_ids)

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

    def run_connection(self, run_id: Optional[str] = None) -> ContextManager[Connection]:
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
        cursor: Optional[str],
        callback: EventHandlerFn,
    ) -> None:
        if cursor and EventLogCursor.parse(cursor).is_offset_cursor():
            check.failed("Cannot call `watch` with an offset cursor")
        if self._event_watcher is None:
            self._event_watcher = SqlPollingEventWatcher(self)

        self._event_watcher.watch_run(run_id, cursor, callback)

    def _gen_event_log_entry_from_cursor(self, cursor) -> EventLogEntry:
        with self._engine.connect() as conn:
            cursor_res = conn.execute(
                db_select([SqlEventLogStorageTable.c.event]).where(
                    SqlEventLogStorageTable.c.id == cursor
                ),
            )
            return deserialize_value(cursor_res.scalar(), EventLogEntry)  # type: ignore

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
