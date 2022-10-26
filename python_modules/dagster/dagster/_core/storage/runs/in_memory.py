from contextlib import contextmanager

import sqlalchemy as db
from sqlalchemy.pool import NullPool

from dagster._core.storage.sql import create_engine, get_alembic_config, stamp_alembic_rev
from dagster._core.storage.sqlite import create_in_memory_conn_string

from .schema import InstanceInfo, RunStorageSqlMetadata
from .sql_run_storage import SqlRunStorage


class InMemoryRunStorage(SqlRunStorage):
    """
    In memory only run storage. Used by ephemeral DagsterInstance or for testing purposes.

    WARNING: Dagit and other core functionality will not work if this is used on a real DagsterInstance
    """

    def __init__(self, preload=None):
        self._conn = self._create_connection()

        self.migrate()
        self.optimize()

        if preload:
            for payload in preload:
                self.add_pipeline_snapshot(
                    payload.pipeline_snapshot, payload.pipeline_run.pipeline_snapshot_id
                )
                self.add_execution_plan_snapshot(
                    payload.execution_plan_snapshot, payload.pipeline_run.execution_plan_snapshot_id
                )
                self.add_run(payload.pipeline_run)

    def _create_connection(self):
        engine = create_engine(create_in_memory_conn_string("runs"), poolclass=NullPool)
        conn = engine.connect()
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        RunStorageSqlMetadata.create_all(conn)
        alembic_config = get_alembic_config(__file__, "sqlite/alembic/alembic.ini")
        stamp_alembic_rev(alembic_config, conn)
        table_names = db.inspect(conn).get_table_names()
        if "instance_info" not in table_names:
            InstanceInfo.create(conn)
        return conn

    @contextmanager
    def connect(self):
        yield self._conn

    def upgrade(self):
        pass
