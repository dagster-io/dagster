from typing import Any, Callable

import sqlalchemy as db

from dagster._core.instance import DagsterInstance
from dagster._core.storage.event_log import SqlEventLogStorage, SqliteEventLogStorage
from dagster._core.storage.event_log.schema import (
    AssetKeyTable,
    DynamicPartitionsTable,
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
from dagster._core.storage.schedules import SqliteScheduleStorage, SqlScheduleStorage
from dagster._core.storage.schedules.schema import (
    InstigatorsTable,
    JobTable,
    JobTickTable,
    SecondaryIndexMigrationTable as ScheduleSecondaryIndexTable,
)


def _has_integer_id_column(inspector, table):
    type_by_col_name = {col["name"]: col["type"] for col in inspector.get_columns(table.name)}
    id_col_type = type_by_col_name.get("id")
    return id_col_type and str(id_col_type) == str(db.Integer())


def _convert_id_from_int_to_bigint(conn, table, should_autoincrement):
    # Since we are not using alembic (which might mess up the versioning system), we need to
    # manually handle the dialect differences for running the migration
    dialect = db.inspect(conn).dialect.name
    if dialect == "postgresql":
        statement = db.text(f"ALTER TABLE {table.name} ALTER COLUMN id TYPE BIGINT")
    elif dialect == "mysql":
        if should_autoincrement:
            statement = db.text(f"ALTER TABLE {table.name} MODIFY COLUMN id BIGINT AUTO_INCREMENT")
        else:
            statement = db.text(f"ALTER TABLE {table.name} MODIFY COLUMN id BIGINT")
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


def _restore_asset_event_tags_foreign_key(conn, inspector, print_fn):
    if len(inspector.get_foreign_keys("asset_event_tags")) > 0:
        # There are foreign keys present for the asset event tags table already, no need to restore
        return

    print_fn("Restoring foreign key constraint on asset event tags table")
    conn.execute(
        db.text(
            "ALTER TABLE asset_event_tags ADD CONSTRAINT asset_event_tags_event_id_fkey"
            " FOREIGN KEY (event_id) REFERENCES event_logs(id) ON DELETE CASCADE"
        )
    )
    print_fn("Completed restoring foreign key constraint on asset event tags table")


def _migrate_storage(conn, tables_to_migrate, print_fn):
    inspector = db.inspect(conn)
    all_table_names = set(inspector.get_table_names())

    for table in tables_to_migrate:
        if _has_integer_id_column(inspector, table):
            should_autoincrement = table.columns["id"].autoincrement

            if table.name == "event_logs" and "asset_event_tags" in all_table_names:
                # the asset event tags table has a foreign key on the event_logs id that has to be
                # removed before the event logs col can be converted to bigint
                _remove_asset_event_tags_foreign_key(conn, inspector, print_fn)

            print_fn(f"Altering {table} to use bigint for id column")
            _convert_id_from_int_to_bigint(conn, table, should_autoincrement)
            print_fn(f"Completed {table} migration")

        # restore the foreign key on the asset event tags table if needed, even if we did not just
        # migrate the event logs table in case we hit some error and exited in a bad state
        if table == "event_logs" and "asset_event_tags" in all_table_names:
            _restore_asset_event_tags_foreign_key(conn, print_fn)  # pyright: ignore[reportCallIssue]


def run_bigint_migration(instance: DagsterInstance, print_fn: Callable[..., Any] = print):
    if isinstance(instance.event_log_storage, SqliteEventLogStorage):
        print_fn("Sqlite does not support bigint types, no need to migrate event log storage.")
    elif isinstance(instance.event_log_storage, SqlEventLogStorage):
        with instance.event_log_storage.index_connection() as conn:
            id_tables = [
                SqlEventLogStorageTable,
                EventLogSecondaryIndexTable,
                AssetKeyTable,
                DynamicPartitionsTable,
            ]
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
