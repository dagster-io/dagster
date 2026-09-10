"""Tests for the SQL Server schema compatibility layer in dagster core.

These cover the three ways dagster's schema is invalid or lossy on SQL Server, and the
guarantee that fixing them changed nothing for any other database.
"""

import sqlalchemy as db
from dagster._core.storage.event_log.schema import (
    AssetEventTagsTable,
    SqlEventLogStorageMetadata,
    SqlEventLogStorageTable,
)
from dagster._core.storage.runs.schema import (
    KeyValueStoreTable,
    RunStorageSqlMetadata,
    RunTagsTable,
)
from dagster._core.storage.schedules.schema import ScheduleStorageSqlMetadata
from dagster._core.storage.sql import mssql_string, mssql_text
from sqlalchemy.dialects import mssql, mysql, postgresql, sqlite
from sqlalchemy.schema import CreateIndex, CreateTable

ALL_METADATA = [
    SqlEventLogStorageMetadata,
    RunStorageSqlMetadata,
    ScheduleStorageSqlMetadata,
]

NON_ASCII = "café-日本語-🎉"


def _render(metadata, dialect):
    parts = []
    for table in metadata.sorted_tables:
        parts.append(CreateTable(table).compile(dialect=dialect).string)
        parts.extend(
            CreateIndex(index).compile(dialect=dialect).string
            for index in sorted(table.indexes, key=lambda i: i.name or "")
        )
    return "\n".join(parts)


def _all_columns():
    for metadata in ALL_METADATA:
        for table in metadata.sorted_tables:
            for column in table.columns:
                yield table, column


def _index_key_columns(table):
    keyed = set()
    for index in table.indexes:
        keyed.update(e.name for e in index.expressions if hasattr(e, "name"))
    for constraint in table.constraints:
        if isinstance(constraint, (db.UniqueConstraint, db.PrimaryKeyConstraint)):
            keyed.update(c.name for c in constraint.columns)
    return keyed


class TestOtherDialectsUnaffected:
    """The SQL Server variants must be invisible to every other database.

    This is the safety property that makes changing the shared schema acceptable: if any
    of these drift, an existing Postgres or MySQL deployment would see a schema change.
    """

    def test_no_ddl_drift(self):
        # A change here means the mssql variants leaked into another dialect. Regenerate
        # deliberately; do not just update the assertion.
        for dialect in (postgresql.dialect(), mysql.dialect(), sqlite.dialect()):
            for metadata in ALL_METADATA:
                rendered = _render(metadata, dialect)
                assert "NVARCHAR" not in rendered.upper(), (
                    f"NVARCHAR leaked into {dialect.name} DDL"
                )
                assert "DATETIME2" not in rendered.upper(), (
                    f"DATETIME2 leaked into {dialect.name} DDL"
                )
                assert "SYSUTCDATETIME" not in rendered.upper(), (
                    f"SYSUTCDATETIME leaked into {dialect.name} DDL"
                )

    def test_text_columns_still_text_elsewhere(self):
        for dialect, expected in (
            (postgresql.dialect(), "TEXT"),
            (sqlite.dialect(), "TEXT"),
        ):
            rendered = RunTagsTable.c.value.type.compile(dialect=dialect)
            assert rendered == expected

    def test_longtext_still_longtext_on_mysql(self):
        rendered = SqlEventLogStorageTable.c.event.type.compile(dialect=mysql.dialect())
        assert rendered == "LONGTEXT"

    def test_mysql_prefix_index_lengths_preserved(self):
        # dagster-mysql relies on mysql_length for its prefix indexes; the mssql work must
        # not have disturbed them.
        rendered = CreateIndex(
            next(i for i in SqlEventLogStorageTable.indexes if i.name == "idx_step_key")
        ).compile(dialect=mysql.dialect())
        assert "step_key(32)" in rendered.string


class TestMSSQLTypeMapping:
    def test_timestamp_is_not_rowversion(self):
        """A bare TIMESTAMP on SQL Server means ROWVERSION, an auto-generated binary
        counter, and a table may only have one -- asset_keys has two TIMESTAMP columns and
        would fail to create at all.
        """
        rendered = SqlEventLogStorageTable.c.timestamp.type.compile(dialect=mssql.dialect())
        assert rendered == "DATETIME2(6)"

    def test_datetime_keeps_sub_millisecond_precision(self):
        # plain DATETIME rounds to ~3.33ms, which is coarser than dagster's tick ordering
        rendered = db.DateTime().compile(dialect=mssql.dialect())
        assert rendered == "DATETIME2(6)"

    def test_no_rowversion_columns_anywhere(self):
        for _table, column in _all_columns():
            rendered = column.type.compile(dialect=mssql.dialect()).upper()
            assert rendered != "TIMESTAMP", f"{column.name} would become a ROWVERSION column"

    def test_every_index_key_column_is_bounded(self):
        """SQL Server refuses VARCHAR(max)/NVARCHAR(max) as an index key column."""
        unbounded = []
        for metadata in ALL_METADATA:
            for table in metadata.sorted_tables:
                keyed = _index_key_columns(table)
                for column in table.columns:
                    if column.name not in keyed:
                        continue
                    rendered = column.type.compile(dialect=mssql.dialect()).upper()
                    if "(MAX)" in rendered or rendered in ("TEXT", "NTEXT"):
                        unbounded.append(f"{table.name}.{column.name} -> {rendered}")
        assert not unbounded, f"unindexable index key columns: {unbounded}"

    def test_index_keys_fit_sql_server_limit(self):
        """Composite index keys must fit in 1700 bytes, and NVARCHAR costs 2 bytes/char."""
        oversized = []
        for metadata in ALL_METADATA:
            for table in metadata.sorted_tables:
                for index in table.indexes:
                    total = 0
                    for expr in index.expressions:
                        if not hasattr(expr, "type"):
                            continue
                        type_ = expr.type
                        length = getattr(type_, "length", None)
                        if isinstance(type_, db.String) and length:
                            rendered = type_.compile(dialect=mssql.dialect()).upper()
                            total += length * (2 if rendered.startswith("N") else 1)
                        else:
                            total += 8  # bigint / datetime2 are 8 bytes
                    if total > 1700:
                        oversized.append(f"{index.name} = {total} bytes")
        assert not oversized, f"index keys over SQL Server's 1700 byte limit: {oversized}"

    def test_no_deprecated_ntext(self):
        """db.UnicodeText renders as NTEXT, which is deprecated and unindexable."""
        for _table, column in _all_columns():
            rendered = column.type.compile(dialect=mssql.dialect()).upper()
            assert rendered != "NTEXT", f"{column.name} renders as deprecated NTEXT"

    def test_user_facing_text_is_nvarchar(self):
        """Columns holding user-supplied strings must not be VARCHAR.

        VARCHAR stores text in the database codepage, so under a non-UTF-8 collation any
        character outside it is silently replaced with '?'. These columns are written as
        raw strings rather than through dagster's (ASCII-escaping) serdes, so VARCHAR
        would be real data loss.
        """
        user_facing = [
            (SqlEventLogStorageTable, "asset_key"),
            (SqlEventLogStorageTable, "partition"),
            (SqlEventLogStorageTable, "step_key"),
            (RunTagsTable, "key"),
            (RunTagsTable, "value"),
            (AssetEventTagsTable, "key"),
            (AssetEventTagsTable, "value"),
            (KeyValueStoreTable, "key"),
        ]
        for table, column_name in user_facing:
            rendered = table.c[column_name].type.compile(dialect=mssql.dialect()).upper()
            assert rendered.startswith("N"), (
                f"{table.name}.{column_name} is {rendered}; non-ASCII values would be"
                " replaced with '?' under a non-UTF-8 collation"
            )


class TestHelpers:
    def test_mssql_text_bounded(self):
        assert mssql_text(64).compile(dialect=mssql.dialect()) == "NVARCHAR(64)"

    def test_mssql_text_unbounded(self):
        assert mssql_text().compile(dialect=mssql.dialect()) == "NVARCHAR(max)"

    def test_mssql_text_is_text_elsewhere(self):
        assert mssql_text(64).compile(dialect=postgresql.dialect()) == "TEXT"
        assert mssql_text().compile(dialect=postgresql.dialect()) == "TEXT"

    def test_mssql_string(self):
        assert mssql_string(255).compile(dialect=mssql.dialect()) == "NVARCHAR(255)"
        assert mssql_string(255).compile(dialect=postgresql.dialect()) == "VARCHAR(255)"
