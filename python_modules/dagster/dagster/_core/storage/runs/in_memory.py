import uuid
from collections.abc import Iterator, Sequence
from contextlib import contextmanager

import sqlalchemy as db
from sqlalchemy.engine import Connection
from sqlalchemy.pool import NullPool

from dagster._core.debug import DebugRunPayload
from dagster._core.storage.runs.migration import RUN_BACKFILL_ID
from dagster._core.storage.runs.schema import (
    InstanceInfo,
    RunStorageSqlMetadata,
    SecondaryIndexMigrationTable,
)
from dagster._core.storage.runs.sql_run_storage import SqlRunStorage
from dagster._core.storage.sql import create_engine, get_alembic_config, stamp_alembic_rev
from dagster._core.storage.sqlite import create_in_memory_conn_string


class InMemoryRunStorage(SqlRunStorage):
    """In memory only run storage. Used by ephemeral DagsterInstance or for testing purposes.

    WARNING: The Dagster UI and other core functionality will not work if this is used on a real DagsterInstance
    """

    def __init__(self, preload: Sequence[DebugRunPayload] | None = None):
        self._engine = create_engine(
            create_in_memory_conn_string(f"runs-{uuid.uuid4()}"),
            poolclass=NullPool,
        )

        # hold one connection for life of instance, but vend new ones for specific calls
        self._held_conn = self._engine.connect()

        with self._held_conn.begin():
            RunStorageSqlMetadata.create_all(self._held_conn)
            self._held_conn.execute(
                SecondaryIndexMigrationTable.insert().values(
                    name=RUN_BACKFILL_ID, migration_completed=db.func.current_timestamp()
                )
            )
            alembic_config = get_alembic_config(__file__, "sqlite/alembic/alembic.ini")
            stamp_alembic_rev(alembic_config, self._held_conn)

            table_names = db.inspect(self._held_conn).get_table_names()

            if "instance_info" not in table_names:
                InstanceInfo.create(self._held_conn)

        if preload:
            for payload in preload:
                run = payload.dagster_run
                job_snap_id = self.add_job_snapshot(payload.job_snapshot)
                plan_snap_id = self.add_execution_plan_snapshot(payload.execution_plan_snapshot)

                # if the snapshot id has shifted due to changes in json structure
                # update the runs pointers
                if job_snap_id != run.job_snapshot_id:
                    run = run._replace(job_snapshot_id=job_snap_id)
                if plan_snap_id != run.execution_plan_snapshot_id:
                    run = run._replace(execution_plan_snapshot_id=plan_snap_id)

                self.add_run(run)

    def has_secondary_index(self, name: str) -> bool:
        return True

    def has_built_index(self, migration_name: str) -> bool:
        # Every in-memory database starts from the current schema and has no
        # historical rows requiring a data migration.
        return True

    @contextmanager
    def connect(self) -> Iterator[Connection]:
        with self._engine.connect() as conn:
            with conn.begin():
                conn.execute(db.text("PRAGMA journal_mode=WAL;")).close()
                conn.execute(db.text("PRAGMA foreign_keys=ON;")).close()
                yield conn

    def upgrade(self) -> None:
        pass

    def dispose(self) -> None:
        self._held_conn.close()
        self._engine.dispose()
