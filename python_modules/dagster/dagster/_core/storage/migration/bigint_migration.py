from typing import Callable

import sqlalchemy as db

from dagster._core.instance import DagsterInstance
from dagster._core.storage.event_log import (
    SqlEventLogStorage,
    SqliteEventLogStorage,
)
from dagster._core.storage.event_log.schema import (
    AssetKeyTable,
    SecondaryIndexMigrationTable as EventLogSecondaryIndexTable,
    SqlEventLogStorageTable,
)
from dagster._core.storage.runs import SqliteRunStorage, SqlRunStorage
from dagster._core.storage.runs.schema import (
    BulkActionsTable,
    RunsTable,
    RunTagsTable,
    SecondaryIndexMigrationTable as RunSecondaryIndexTable,
    SnapshotsTable,
)
from dagster._core.storage.schedules import (
    SqliteScheduleStorage,
    SqlScheduleStorage,
)
from dagster._core.storage.schedules.schema import (
    InstigatorsTable,
    JobTable,
    JobTickTable,
    SecondaryIndexMigrationTable as ScheduleSecondaryIndexTable,
)


def _has_integer_id_column(inspector, table):
    type_by_col_name = {col["name"]: col["type"] for col in inspector.get_columns(table)}
    id_col_type = type_by_col_name.get("id")
    return id_col_type and str(id_col_type) == str(db.Integer())


def _convert_int_to_bigint(conn, table, colname):
    # Since we are not using alembic (which might mess up the versioning system), we need to
    # manually handle the dialect differences for running the migration
    dialect = db.inspect(conn).dialect.name
    if dialect == "postgresql":
        statement = db.text(f"ALTER TABLE {table} ALTER COLUMN {colname} TYPE BIGINT")
    elif dialect == "mysql":
        statement = db.text(f"ALTER TABLE {table} MODIFY COLUMN {colname} BIGINT")
    else:
        raise Exception(f"Unsupported dialect {dialect}")
    conn.execute(statement)


def _remove_asset_event_tags_foreign_key(conn, inspector, print_fn):
    for fk in inspector.get_foreign_keys("asset_event_tags"):
        # even though there should only be one foreign key, each dialect might have a
        # different naming scheme.  Drop all foreign keys in case this migration exited in
        # a bad state
        print_fn("Dropping foreign key constraint on asset event tags table")
        conn.execute(db.text(f"ALTER TABLE asset_event_tags DROP CONSTRAINT {fk['name']}"))
        print_fn("Completed dropping foreign key constraint on asset event tags table")


def _restore_asset_event_tags_foreign_key(conn, print_fn):
    print_fn("Restoring foreign key constraint on asset event tags table")
    # For pseudo-idempotence, just come up with a foreign key name rather on relying for the
    # foreign key name to be the same across invocations
    conn.execute(
        db.text(
            "ALTER TABLE asset_event_tags ADD CONSTRAINT asset_event_tags_event_id_fkey"
            " FOREIGN KEY (event_id) REFERENCES event_logs(id) ON DELETE CASCADE"
        )
    )
    print_fn("Completed restoring foreign key constraint on asset event tags table")


def _migrate_storage(conn, id_tables, print_fn):
    inspector = db.inspect(conn)
    table_names = [table.name for table in id_tables]
    storage_tables = [table for table in inspector.get_table_names() if table in table_names]
    to_migrate = set()
    for table in storage_tables:
        if _has_integer_id_column(inspector, table):
            to_migrate.add(table)

    for table in to_migrate:
        if table == "event_logs" and "asset_event_tags" in storage_tables:
            # the asset event tags table has a foreign key on the event_logs id that has to be
            # removed before the event logs col can be converted to bigint
            _remove_asset_event_tags_foreign_key(conn, inspector, print_fn)

        print_fn(f"Altering {table} to use bigint for id column")
        _convert_int_to_bigint(conn, table, "id")
        print_fn(f"Completed {table} migration")

        if table == "event_logs" and "asset_event_tags" in storage_tables:
            _restore_asset_event_tags_foreign_key(conn, print_fn)


def run_bigint_migration(instance: DagsterInstance, print_fn: Callable = print):
    if isinstance(instance.event_log_storage, SqliteEventLogStorage):
        print_fn("Sqlite does not support bigint types, no need to migrate event log storage.")
    elif isinstance(instance.event_log_storage, SqlEventLogStorage):
        with instance.event_log_storage.index_connection() as conn:
            id_tables = [SqlEventLogStorageTable, EventLogSecondaryIndexTable, AssetKeyTable]
            _migrate_storage(conn, id_tables, print_fn)

    if isinstance(instance.run_storage, SqliteRunStorage):
        print_fn("Sqlite does not support bigint types, no need to migrate run storage.")
    elif isinstance(instance.run_storage, SqlRunStorage):
        with instance.run_storage.connect() as conn:
            id_tables = [
                RunsTable,
                RunSecondaryIndexTable,
                RunTagsTable,
                SnapshotsTable,
                BulkActionsTable,
            ]
            _migrate_storage(conn, id_tables, print_fn)

    if isinstance(instance.schedule_storage, SqliteScheduleStorage):
        print_fn("Sqlite does not support bigint types, no need to migrate schedule storage.")
    elif isinstance(instance.schedule_storage, SqlScheduleStorage):
        with instance.schedule_storage.connect() as conn:
            id_tables = [JobTable, InstigatorsTable, JobTickTable, ScheduleSecondaryIndexTable]
            _migrate_storage(conn, id_tables, print_fn)
