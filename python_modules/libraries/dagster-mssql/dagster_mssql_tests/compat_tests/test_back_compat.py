"""Back-compatibility tests: old schemas must survive `dagster instance migrate`.

The pattern mirrors ``dagster_mysql_tests/compat_tests``. Each ``snapshot_<version>_*.sql``
file is a schema (and a little data) captured from a real deployment on an older dagster.
A test restores one into an empty database, runs ``instance.upgrade()``, and asserts the
result is usable -- which is the only way to actually exercise the revisions in
``dagster_mssql/alembic/versions``, since a fresh install never runs them at all.

There are no snapshots yet: dagster-mssql has not had a release to be compatible *with*.
The machinery is here so the first one is a drop-in, and so the batch splitter it depends
on is already tested.

To capture a snapshot, point the target dagster version at a SQL Server database, let it
build its schema, then script the database out with ``mssql-scripter``::

    mssql-scripter --connection-string "..." --schema-and-data > snapshot_X_Y_Z_thing.sql

Name it for the version it came from and what it predates, e.g.
``snapshot_1_13_15_pre_foo_column.sql``. ``GO`` batch separators are handled, so the
scripter's default output needs no editing.
"""

import os
import re
import tempfile
from pathlib import Path

import pytest
import sqlalchemy as db
from dagster._core.instance import DagsterInstance
from dagster._utils import file_relative_path

SNAPSHOT_DIR = Path(__file__).parent

# `GO` is a batch separator understood by sqlcmd, not a T-SQL statement -- the driver
# rejects it. It is only a separator when it is alone on its line.
_GO_SEPARATOR = re.compile(r"^\s*GO\s*(?:--.*)?$", re.IGNORECASE | re.MULTILINE)


def split_batches(script: str) -> list[str]:
    """Split a T-SQL script into the batches a driver can execute one at a time.

    Scripting tools emit ``GO`` between batches; pyodbc has no idea what it means, so the
    script has to be split before it is executed.
    """
    return [batch.strip() for batch in _GO_SEPARATOR.split(script) if batch.strip()]


def reconstruct_from_file(conn_string: str, path: str) -> None:
    """Drop everything in the test database and rebuild it from a snapshot."""
    engine = db.create_engine(conn_string, isolation_level="AUTOCOMMIT")
    try:
        with engine.connect() as conn:
            _drop_all_objects(conn)
            for batch in split_batches(Path(path).read_text(encoding="utf8")):
                conn.execute(db.text(batch))
    finally:
        engine.dispose()


def _drop_all_objects(conn) -> None:
    """Empty the database without dropping it.

    Dropping the database itself would need exclusive access and a connection to
    ``master``; dropping its contents is enough and works with ordinary permissions.
    Foreign keys go first so the tables can be dropped in any order.
    """
    conn.execute(
        db.text("""
        DECLARE @sql NVARCHAR(MAX) = N'';
        SELECT @sql += N'ALTER TABLE ' + QUOTENAME(OBJECT_SCHEMA_NAME(parent_object_id))
            + N'.' + QUOTENAME(OBJECT_NAME(parent_object_id))
            + N' DROP CONSTRAINT ' + QUOTENAME(name) + N';'
        FROM sys.foreign_keys;
        EXEC sp_executesql @sql;
        """)
    )
    conn.execute(
        db.text("""
        DECLARE @sql NVARCHAR(MAX) = N'';
        SELECT @sql += N'DROP TABLE ' + QUOTENAME(SCHEMA_NAME(schema_id))
            + N'.' + QUOTENAME(name) + N';'
        FROM sys.tables;
        EXEC sp_executesql @sql;
        """)
    )


def _snapshots() -> list[Path]:
    return sorted(SNAPSHOT_DIR.glob("snapshot_*.sql"))


class TestBatchSplitter:
    """The splitter runs on every snapshot, so it is worth testing without a database."""

    def test_splits_on_go(self):
        assert split_batches("CREATE TABLE a (i INT)\nGO\nCREATE TABLE b (i INT)\nGO\n") == [
            "CREATE TABLE a (i INT)",
            "CREATE TABLE b (i INT)",
        ]

    def test_go_is_case_insensitive_and_tolerates_whitespace(self):
        assert split_batches("SELECT 1\n  go  \nSELECT 2") == ["SELECT 1", "SELECT 2"]

    def test_trailing_comment_after_go(self):
        assert split_batches("SELECT 1\nGO -- next batch\nSELECT 2") == ["SELECT 1", "SELECT 2"]

    def test_go_inside_a_statement_is_not_a_separator(self):
        """`GO` only separates batches when it is alone on its line."""
        script = "INSERT INTO t VALUES ('GO')\nSELECT 'GO GO'\n"
        assert split_batches(script) == [script.strip()]

    def test_go_as_part_of_an_identifier_is_not_a_separator(self):
        assert split_batches("SELECT * FROM GOODS") == ["SELECT * FROM GOODS"]

    def test_empty_batches_are_dropped(self):
        assert split_batches("GO\n\nGO\nSELECT 1\nGO\n") == ["SELECT 1"]

    def test_empty_script(self):
        assert split_batches("") == []


@pytest.fixture
def restored_database(conn_string):
    """Hand back a database these tests may wipe, and leave dagster's schema behind.

    Restoring a snapshot empties the database, so without this a later module would find
    the storage tables gone. Rebuilding them here keeps the suite order-independent.
    """
    yield conn_string
    from dagster._utils.test.mssql_instance import TestMSSQLInstance

    engine = db.create_engine(conn_string, isolation_level="AUTOCOMMIT")
    try:
        with engine.connect() as conn:
            _drop_all_objects(conn)
    finally:
        engine.dispose()

    TestMSSQLInstance.clean_run_storage(conn_string)
    TestMSSQLInstance.clean_event_log_storage(conn_string)
    TestMSSQLInstance.clean_schedule_storage(conn_string)


class TestRestoreMachinery:
    """Exercise the restore path itself, so the first real snapshot does not have to.

    Without this the whole harness is untested until someone captures a snapshot, and any
    breakage surfaces as a confusing failure in whatever migration they were trying to
    verify.
    """

    def test_restores_a_script_into_an_empty_database(self, restored_database, tmp_path):
        conn_string = restored_database
        script = tmp_path / "snapshot_fake.sql"
        script.write_text(
            "CREATE TABLE compat_probe_a (id INT PRIMARY KEY, name NVARCHAR(64));\n"
            "GO\n"
            "CREATE TABLE compat_probe_b (id INT PRIMARY KEY,\n"
            "  a_id INT REFERENCES compat_probe_a(id));\n"
            "GO\n"
            "INSERT INTO compat_probe_a (id, name) VALUES (1, N'café');\n"
            "GO\n",
            encoding="utf8",
        )

        reconstruct_from_file(conn_string, str(script))

        engine = db.create_engine(conn_string)
        try:
            with engine.connect() as conn:
                tables = set(db.inspect(conn).get_table_names())
                assert {"compat_probe_a", "compat_probe_b"} <= tables
                # nothing else survived the wipe
                assert "runs" not in tables
                name = conn.execute(
                    db.text("SELECT name FROM compat_probe_a WHERE id = 1")
                ).scalar()
                assert name == "café"
        finally:
            engine.dispose()

    def test_wipe_drops_foreign_keys_before_tables(self, restored_database, tmp_path):
        """A second restore has to succeed with FK-referenced tables already present."""
        conn_string = restored_database
        script = tmp_path / "snapshot_fake.sql"
        script.write_text(
            "CREATE TABLE compat_probe_a (id INT PRIMARY KEY);\n"
            "GO\n"
            "CREATE TABLE compat_probe_b (id INT PRIMARY KEY,\n"
            "  a_id INT REFERENCES compat_probe_a(id));\n"
            "GO\n",
            encoding="utf8",
        )

        reconstruct_from_file(conn_string, str(script))
        reconstruct_from_file(conn_string, str(script))  # would fail if FKs blocked the drop

        engine = db.create_engine(conn_string)
        try:
            with engine.connect() as conn:
                assert {"compat_probe_a", "compat_probe_b"} <= set(
                    db.inspect(conn).get_table_names()
                )
        finally:
            engine.dispose()


@pytest.mark.skipif(not _snapshots(), reason="no schema snapshots captured yet")
@pytest.mark.parametrize("snapshot", _snapshots(), ids=lambda p: p.stem)
def test_upgrade_from_snapshot(restored_database, snapshot):
    """Restore an older schema, migrate it, and confirm the instance works afterwards."""
    conn_string = restored_database
    reconstruct_from_file(conn_string, str(snapshot))

    with tempfile.TemporaryDirectory() as tempdir:
        with open(file_relative_path(__file__, "dagster.yaml"), encoding="utf8") as template_fd:
            template = template_fd.read().format(conn_string=conn_string)
        with open(os.path.join(tempdir, "dagster.yaml"), "w", encoding="utf8") as target_fd:
            target_fd.write(template)

        with DagsterInstance.from_config(tempdir) as instance:
            instance.upgrade()

            # The point of migrating is that ordinary reads work afterwards. These go
            # through the columns and indexes the migrations are responsible for adding.
            assert instance.get_runs() is not None
            assert instance.all_asset_keys() is not None
            assert instance.all_instigator_state() is not None
