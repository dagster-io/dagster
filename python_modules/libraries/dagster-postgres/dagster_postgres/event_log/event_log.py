from typing import Optional

import sqlalchemy as db

import dagster._check as check
from dagster.core.events.log import EventLogEntry
from dagster.core.storage.event_log import (
    AssetKeyTable,
    SqlEventLogStorage,
    SqlEventLogStorageMetadata,
    SqlEventLogStorageTable,
)
from dagster.core.storage.event_log.migration import ASSET_KEY_INDEX_COLS
from dagster.core.storage.sql import (
    check_alembic_revision,
    create_engine,
    run_alembic_upgrade,
    stamp_alembic_rev,
)
from dagster.serdes import ConfigurableClass, ConfigurableClassData, deserialize_as

from ..utils import (
    create_pg_connection,
    pg_alembic_config,
    pg_config,
    pg_statement_timeout,
    pg_url_from_config,
    retry_pg_connection_fn,
    retry_pg_creation_fn,
)
from .event_watcher import PostgresEventWatcher

CHANNEL_NAME = "run_events"


class PostgresEventLogStorage(SqlEventLogStorage, ConfigurableClass):
    """Postgres-backed event log storage.

    Users should not directly instantiate this class; it is instantiated by internal machinery when
    ``dagit`` and ``dagster-graphql`` load, based on the values in the ``dagster.yaml`` file in
    ``$DAGSTER_HOME``. Configuration of this class should be done by setting values in that file.

    To use Postgres for event log storage, you can add a block such as the following to your
    ``dagster.yaml``:

    .. literalinclude:: ../../../../../../examples/docs_snippets/docs_snippets/deploying/dagster-pg.yaml
       :caption: dagster.yaml
       :lines: 12-21
       :language: YAML

    Note that the fields in this config are :py:class:`~dagster.StringSource` and
    :py:class:`~dagster.IntSource` and can be configured from environment variables.

    """

    def __init__(self, postgres_url, should_autocreate_tables=True, inst_data=None):
        self._inst_data = check.opt_inst_param(inst_data, "inst_data", ConfigurableClassData)
        self.postgres_url = check.str_param(postgres_url, "postgres_url")
        self.should_autocreate_tables = check.bool_param(
            should_autocreate_tables, "should_autocreate_tables"
        )

        self._disposed = False

        # Default to not holding any connections open to prevent accumulating connections per DagsterInstance
        self._engine = create_engine(
            self.postgres_url, isolation_level="AUTOCOMMIT", poolclass=db.pool.NullPool
        )

        # lazy init
        self._event_watcher: Optional[PostgresEventWatcher] = None

        self._secondary_index_cache = {}

        table_names = retry_pg_connection_fn(lambda: db.inspect(self._engine).get_table_names())

        # Stamp and create tables if the main table does not exist (we can't check alembic
        # revision because alembic config may be shared with other storage classes)
        if self.should_autocreate_tables and "event_logs" not in table_names:
            retry_pg_creation_fn(self._init_db)
            self.reindex_events()
            self.reindex_assets()

        super().__init__()

    def _init_db(self):
        with self._connect() as conn:
            with conn.begin():
                SqlEventLogStorageMetadata.create_all(conn)
                stamp_alembic_rev(pg_alembic_config(__file__), conn)

    def optimize_for_dagit(self, statement_timeout):
        # When running in dagit, hold an open connection and set statement_timeout
        self._engine = create_engine(
            self.postgres_url,
            isolation_level="AUTOCOMMIT",
            pool_size=1,
            connect_args={"options": pg_statement_timeout(statement_timeout)},
        )

    def upgrade(self):
        alembic_config = pg_alembic_config(__file__)
        with self._connect() as conn:
            run_alembic_upgrade(alembic_config, conn)

    @property
    def inst_data(self):
        return self._inst_data

    @classmethod
    def config_type(cls):
        return pg_config()

    @staticmethod
    def from_config_value(inst_data, config_value):
        return PostgresEventLogStorage(
            inst_data=inst_data,
            postgres_url=pg_url_from_config(config_value),
            should_autocreate_tables=config_value.get("should_autocreate_tables", True),
        )

    @staticmethod
    def create_clean_storage(conn_string, should_autocreate_tables=True):
        engine = create_engine(
            conn_string, isolation_level="AUTOCOMMIT", poolclass=db.pool.NullPool
        )
        try:
            SqlEventLogStorageMetadata.drop_all(engine)
        finally:
            engine.dispose()

        return PostgresEventLogStorage(conn_string, should_autocreate_tables)

    def store_event(self, event):
        """Store an event corresponding to a pipeline run.
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
            conn.execute(
                """NOTIFY {channel}, %s; """.format(channel=CHANNEL_NAME),
                (res[0] + "_" + str(res[1]),),
            )

        if (
            event.is_dagster_event
            and (
                event.dagster_event.is_step_materialization
                or event.dagster_event.is_asset_observation
                or event.dagster_event.is_asset_materialization_planned
            )
            and event.dagster_event.asset_key
        ):
            self.store_asset_event(event)

    def store_asset_event(self, event):
        check.inst_param(event, "event", EventLogEntry)
        if not event.is_dagster_event or not event.dagster_event.asset_key:
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

        # The AssetKeyTable contains a `last_materialization_timestamp` column that is exclusively
        # used to determine if an asset exists (last materialization timestamp > wipe timestamp).
        # This column is used nowhere else, and as of AssetObservation/AssetMaterializationPlanned
        # event creation, we want to extend this functionality to ensure that assets with any event
        # (observation, materialization, or materialization planned) yielded with timestamp
        # > wipe timestamp display in Dagit.

        # As of the following PRs, we update last_materialization_timestamp to store the timestamp
        # of the latest asset observation, materialization, or materialization_planned that has occurred.
        # https://github.com/dagster-io/dagster/pull/6885
        # https://github.com/dagster-io/dagster/pull/7319

        # The AssetKeyTable also contains a `last_run_id` column that is updated upon asset
        # materialization. This column was not being used until the below PR. This new change
        # writes to the column upon `ASSET_MATERIALIZATION_PLANNED` events to fetch the last
        # run id for a set of assets in one roundtrip call to event log storage.
        # https://github.com/dagster-io/dagster/pull/7319

        values = self._get_asset_entry_values(event, self.has_secondary_index(ASSET_KEY_INDEX_COLS))
        with self.index_connection() as conn:
            query = db.dialects.postgresql.insert(AssetKeyTable).values(
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

    def _connect(self):
        return create_pg_connection(self._engine, pg_alembic_config(__file__), "event log")

    def run_connection(self, run_id=None):
        return self._connect()

    def index_connection(self):
        return self._connect()

    def has_secondary_index(self, name):
        if name not in self._secondary_index_cache:
            self._secondary_index_cache[name] = super(
                PostgresEventLogStorage, self
            ).has_secondary_index(name)
        return self._secondary_index_cache[name]

    def enable_secondary_index(self, name):
        super(PostgresEventLogStorage, self).enable_secondary_index(name)
        if name in self._secondary_index_cache:
            del self._secondary_index_cache[name]

    def watch(self, run_id, start_cursor, callback):
        if self._event_watcher is None:
            self._event_watcher = PostgresEventWatcher(
                self.postgres_url,
                [CHANNEL_NAME],
                self._gen_event_log_entry_from_cursor,
            )

        self._event_watcher.watch_run(run_id, start_cursor, callback)

    def _gen_event_log_entry_from_cursor(self, cursor) -> EventLogEntry:
        with self._engine.connect() as conn:
            cursor_res = conn.execute(
                db.select([SqlEventLogStorageTable.c.event]).where(
                    SqlEventLogStorageTable.c.id == cursor
                ),
            )
            return deserialize_as(cursor_res.scalar(), EventLogEntry)

    def end_watch(self, run_id, handler):
        if self._event_watcher is None:
            return

        self._event_watcher.unwatch_run(run_id, handler)

    def __del__(self):
        # Keep the inherent limitations of __del__ in Python in mind!
        self.dispose()

    def dispose(self):
        if not self._disposed:
            self._disposed = True
            if self._event_watcher:
                self._event_watcher.close()

    def alembic_version(self):
        alembic_config = pg_alembic_config(__file__)
        with self._connect() as conn:
            return check_alembic_revision(alembic_config, conn)
