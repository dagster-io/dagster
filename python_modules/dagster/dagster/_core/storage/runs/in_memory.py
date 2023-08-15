import uuid
from contextlib import contextmanager
from typing import Iterator, Optional, Sequence

import sqlalchemy as db
from sqlalchemy.engine import Connection
from sqlalchemy.pool import NullPool

from dagster._core.debug import DebugRunPayload
from dagster._core.storage.sql import create_engine, get_alembic_config, stamp_alembic_rev
from dagster._core.storage.sqlite import create_in_memory_conn_string

from .schema import InstanceInfo, RunStorageSqlMetadata
from .sql_run_storage import SqlRunStorage


class InMemoryRunStorage(SqlRunStorage):
    """In memory only run storage. Used by ephemeral DagsterInstance or for testing purposes.

    WARNING: The Dagster UI and other core functionality will not work if this is used on a real DagsterInstance
    """

    def __init__(self, preload: Optional[Sequence[DebugRunPayload]] = None):
        self._engine = create_engine(
            create_in_memory_conn_string(f"runs-{uuid.uuid4()}"),
            poolclass=NullPool,
        )

        # hold one connection for life of instance, but vend new ones for specific calls
        self._held_conn = self._engine.connect()

        with self._held_conn.begin():
            RunStorageSqlMetadata.create_all(self._held_conn)
            alembic_config = get_alembic_config(__file__, "sqlite/alembic/alembic.ini")
            stamp_alembic_rev(alembic_config, self._held_conn)

            table_names = db.inspect(self._held_conn).get_table_names()

            if "instance_info" not in table_names:
                InstanceInfo.create(self._held_conn)

        self.migrate()
        self.optimize()

        if preload:
            for payload in preload:
                self.add_job_snapshot(payload.job_snapshot, payload.dagster_run.job_snapshot_id)
                self.add_execution_plan_snapshot(
                    payload.execution_plan_snapshot, payload.dagster_run.execution_plan_snapshot_id
                )
                self.add_run(payload.dagster_run)

    @contextmanager
    def connect(self) -> Iterator[Connection]:
        with self._engine.connect() as conn:
            with conn.begin():
                conn.execute(db.text("PRAGMA journal_mode=WAL;"))
                conn.execute(db.text("PRAGMA foreign_keys=ON;"))
                yield conn

    def upgrade(self) -> None:
        pass

    def dispose(self) -> None:
        self._held_conn.close()
        self._engine.dispose()
