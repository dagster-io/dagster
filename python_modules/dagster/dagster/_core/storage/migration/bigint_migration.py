from typing import Callable

import sqlalchemy as db

from dagster._core.instance import DagsterInstance
from dagster._core.storage.event_log import (
    SqlEventLogStorage,
    SqlEventLogStorageMetadata,
    SqliteEventLogStorage,
)
from dagster._core.storage.runs import RunStorageSqlMetadata, SqliteRunStorage, SqlRunStorage
from dagster._core.storage.schedules import (
    ScheduleStorageSqlMetadata,
    SqliteScheduleStorage,
    SqlScheduleStorage,
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


def _drop_foreign_key_constraint(conn, table, fk):
    conn.execute(db.text(f"ALTER TABLE {table} DROP CONSTRAINT {fk['name']}"))


def _add_foreign_key_constraint(conn, table, fk):
    constrained_columns = ", ".join(fk["constrained_columns"])
    referred_columns = ", ".join(fk["referred_columns"])
    conn.execute(
        db.text(
            f"ALTER TABLE {table} ADD CONSTRAINT {fk['name']} FOREIGN KEY ({constrained_columns})"
            f" REFERENCES {fk['referred_table']}({referred_columns}) ON DELETE CASCADE"
        )
    )


def _migrate_storage(conn, metadata, print_fn):
    inspector = db.inspect(conn)
    storage_tables = [table for table in inspector.get_table_names() if table in metadata.tables]
    to_migrate = set()
    for table in storage_tables:
        if _has_integer_id_column(inspector, table):
            to_migrate.add(table)

    dropped_fks = []
    for table in storage_tables:
        for fk in inspector.get_foreign_keys(table):
            if fk["referred_table"] not in to_migrate:
                continue

            if "id" not in fk["referred_columns"]:
                continue

            print_fn(f"Dropping foreign key {fk['name']} on table {table}")
            _drop_foreign_key_constraint(conn, table, fk)
            dropped_fks.append(tuple([table, fk]))
            print_fn(f"Completed dropping foreign key {fk['name']} on table {table}")

    for table in to_migrate:
        print_fn(f"Altering {table} to use bigint for id column")
        _convert_int_to_bigint(conn, table, "id")
        print_fn(f"Completed {table} migration")

    for table, fk in dropped_fks:
        # first convert the constrained column to bigint, to match the referred column
        assert len(fk["constrained_columns"]) == 1
        constrained_col = fk["constrained_columns"][0]
        print_fn(f"Altering {table} to use bigint for {constrained_col} column")
        _convert_int_to_bigint(conn, table, constrained_col)
        print_fn(f"Completed {table} migration")

        # add the foreign key constraint back, if it does not exist
        print_fn(f"Adding foreign key {fk['name']} on table {table}")
        _add_foreign_key_constraint(conn, table, fk)
        print_fn(f"Completed adding foreign key {fk['name']} on table {table}")


def run_bigint_migration(instance: DagsterInstance, print_fn: Callable = print):
    if isinstance(instance.event_log_storage, SqliteEventLogStorage):
        print_fn("Sqlite does not support bigint types, no need to migrate event log storage.")
    elif isinstance(instance.event_log_storage, SqlEventLogStorage):
        with instance.event_log_storage.index_connection() as conn:
            _migrate_storage(conn, SqlEventLogStorageMetadata, print_fn)

    if isinstance(instance.run_storage, SqliteRunStorage):
        print_fn("Sqlite does not support bigint types, no need to migrate run storage.")
    elif isinstance(instance.run_storage, SqlRunStorage):
        with instance.run_storage.connect() as conn:
            _migrate_storage(conn, RunStorageSqlMetadata, print_fn)

    if isinstance(instance.schedule_storage, SqliteScheduleStorage):
        print_fn("Sqlite does not support bigint types, no need to migrate schedule storage.")
    elif isinstance(instance.schedule_storage, SqlScheduleStorage):
        with instance.schedule_storage.connect() as conn:
            _migrate_storage(conn, ScheduleStorageSqlMetadata, print_fn)
