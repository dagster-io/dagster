"""SQL Server behaviour that the shared storage suites do not exercise.

The shared suites round-trip almost everything through dagster's serdes, which escapes
non-ASCII into ASCII unicode escapes before it reaches the database. That masks codepage
corruption entirely, so the checks here read the affected columns back directly.
"""

import threading

import pytest
import sqlalchemy as db
from dagster._core.storage.dagster_run import DagsterRun, DagsterRunStatus
from dagster._core.utils import make_new_run_id
from dagster._daemon.types import DaemonHeartbeat
from dagster_mssql.event_log import MSSQLEventLogStorage
from dagster_mssql.run_storage import MSSQLRunStorage
from dagster_mssql.schedule_storage import MSSQLScheduleStorage
from dagster_mssql.utils import get_conn_string, parse_mssql_version

NON_ASCII = "café-日本語-🎉 ünïcödé Ω≈ç√"


@pytest.fixture(name="storage", scope="function")
def storage_fixture(conn_string):
    return MSSQLRunStorage.create_clean_storage(conn_string)


@pytest.fixture(name="all_storages", scope="function")
def all_storages_fixture(conn_string):
    """Every storage, so that schema-shape assertions see all three MetaDatas."""
    return (
        MSSQLRunStorage.create_clean_storage(conn_string),
        MSSQLEventLogStorage.create_clean_storage(conn_string),
        MSSQLScheduleStorage.create_clean_storage(conn_string),
    )


class TestNonAsciiAtRest:
    """Under the default (non-UTF-8) collation, VARCHAR silently replaces any character
    outside the codepage with '?'. These columns hold raw user strings, so a regression
    here is real, unrecoverable data loss rather than a display problem.
    """

    def test_run_tags_preserved(self, storage, conn_string):
        run_id = make_new_run_id()
        storage.add_run(
            DagsterRun(
                run_id=run_id,
                job_name="unicode_job",
                status=DagsterRunStatus.NOT_STARTED,
                tags={"note": NON_ASCII},
            )
        )

        # read the column directly -- going back through the run body would only prove
        # that serdes escaped it
        engine = db.create_engine(conn_string)
        try:
            with engine.connect() as conn:
                stored = conn.execute(
                    db.text("SELECT TOP 1 [value] FROM run_tags WHERE [key] = 'note'")
                ).scalar()
        finally:
            engine.dispose()

        assert stored == NON_ASCII

    def test_job_name_preserved(self, storage, conn_string):
        job_name = f"job_{NON_ASCII}"
        storage.add_run(
            DagsterRun(
                run_id=make_new_run_id(),
                job_name=job_name,
                status=DagsterRunStatus.NOT_STARTED,
            )
        )

        engine = db.create_engine(conn_string)
        try:
            with engine.connect() as conn:
                stored = conn.execute(db.text("SELECT TOP 1 pipeline_name FROM runs")).scalar()
        finally:
            engine.dispose()

        assert stored == job_name

    def test_kvs_preserved(self, storage, conn_string):
        storage.set_cursor_values({"unicode_key": NON_ASCII})
        assert storage.get_cursor_values({"unicode_key"}) == {"unicode_key": NON_ASCII}

        engine = db.create_engine(conn_string)
        try:
            with engine.connect() as conn:
                stored = conn.execute(
                    db.text("SELECT TOP 1 [value] FROM kvs WHERE [key] = 'unicode_key'")
                ).scalar()
        finally:
            engine.dispose()

        assert stored == NON_ASCII

    def test_filtering_by_non_ascii_tag(self, storage):
        from dagster import RunsFilter

        run_id = make_new_run_id()
        storage.add_run(
            DagsterRun(
                run_id=run_id,
                job_name="unicode_job",
                status=DagsterRunStatus.NOT_STARTED,
                tags={"note": NON_ASCII},
            )
        )
        # a corrupted write would still match a corrupted filter, so assert on the id
        runs = storage.get_runs(filters=RunsFilter(tags={"note": NON_ASCII}))
        assert [r.run_id for r in runs] == [run_id]


class TestMergeUpserts:
    def test_heartbeat_upsert_is_idempotent(self, storage):
        for i in range(5):
            storage.add_daemon_heartbeat(
                DaemonHeartbeat(
                    timestamp=1700000000.0 + i,
                    daemon_type="SCHEDULER",
                    daemon_id=f"daemon-{i}",
                    errors=[],
                )
            )

        heartbeats = storage.get_daemon_heartbeats()
        assert len(heartbeats) == 1
        assert heartbeats["SCHEDULER"].daemon_id == "daemon-4"

    def test_cursor_upsert_is_idempotent(self, storage):
        for i in range(5):
            storage.set_cursor_values({"cursor": str(i)})
        assert storage.get_cursor_values({"cursor"}) == {"cursor": "4"}

    def test_concurrent_upserts_do_not_collide(self, storage):
        """Without HOLDLOCK, concurrent MERGEs racing on the same key raise duplicate key
        violations or deadlock.
        """
        errors = []

        def hammer(worker: int):
            try:
                for i in range(10):
                    storage.set_cursor_values({"shared": f"{worker}-{i}"})
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=hammer, args=(w,)) for w in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors, f"concurrent upserts failed: {errors[:3]}"
        assert set(storage.get_cursor_values({"shared"})) == {"shared"}

    def test_multi_row_upsert(self, storage):
        storage.set_cursor_values({"a": "1", "b": "2", "c": "3"})
        assert storage.get_cursor_values({"a", "b", "c"}) == {"a": "1", "b": "2", "c": "3"}
        storage.set_cursor_values({"a": "10", "d": "4"})
        assert storage.get_cursor_values({"a", "b", "d"}) == {"a": "10", "b": "2", "d": "4"}


class TestSchemaShape:
    def test_no_rowversion_columns(self, all_storages, conn_string):
        """A bare TIMESTAMP column on SQL Server is a ROWVERSION, which the application
        cannot write to.
        """
        engine = db.create_engine(conn_string)
        try:
            with engine.connect() as conn:
                rows = conn.execute(
                    db.text(
                        "SELECT t.name, c.name FROM sys.columns c "
                        "JOIN sys.tables t ON t.object_id = c.object_id "
                        "WHERE c.system_type_id = TYPE_ID('timestamp')"
                    )
                ).fetchall()
        finally:
            engine.dispose()

        assert rows == []

    def test_filtered_indexes_created(self, all_storages, conn_string):
        """Filtered indexes carry two different jobs on SQL Server.

        The first two mirror the partial indexes dagster defines for Postgres; losing them
        is a performance regression only visible under load. The rest exist because SQL
        Server considers null values *equal* in a unique index, unlike every other
        database dagster supports -- filtering the nulls out is what stops it rejecting
        rows that Postgres and MySQL accept.
        """
        engine = db.create_engine(conn_string)
        try:
            with engine.connect() as conn:
                names = {
                    row[0]
                    for row in conn.execute(
                        db.text(
                            "SELECT name FROM sys.indexes WHERE has_filter = 1 "
                            "AND object_id IN (SELECT object_id FROM sys.tables)"
                        )
                    ).fetchall()
                }
        finally:
            engine.dispose()

        assert names == {
            # partial indexes, matching Postgres
            "idx_events_by_asset",
            "idx_events_by_asset_partition",
            # unique indexes over nullable columns
            "idx_asset_check_executions_unique",
            "idx_pending_steps",
            "idx_asset_daemon_asset_evaluations_asset_key_evaluation_id",
        }

    def test_nulls_are_distinct_in_unique_indexes(self, all_storages, conn_string):
        """Postgres and MySQL treat each null as distinct, so several rows may share a
        unique key as long as part of it is null. SQL Server does not, and dagster relies
        on the permissive behaviour -- for example when recording asset check executions
        that have no partition.
        """
        engine = db.create_engine(conn_string)
        try:
            with engine.begin() as conn:
                for _ in range(3):
                    conn.execute(
                        db.text(
                            "INSERT INTO asset_check_executions "
                            "(asset_key, check_name, run_id, partition, execution_status) "
                            "VALUES (:k, :c, :r, NULL, 'PLANNED')"
                        ),
                        {"k": '["a"]', "c": "chk", "r": None},
                    )
                count = conn.execute(
                    db.text("SELECT COUNT(*) FROM asset_check_executions")
                ).scalar()
        finally:
            engine.dispose()

        assert count == 3

    def test_alembic_stamped_at_head(self, storage):
        current, head = storage.alembic_version()
        assert current is not None
        assert current == head


class TestConnectionString:
    def test_defaults(self):
        conn_string = get_conn_string(
            username="sa", password="pw", hostname="localhost", db_name="test"
        )
        assert conn_string.startswith("mssql+pyodbc://sa:pw@localhost:1433/test?")
        assert "driver=ODBC+Driver+18+for+SQL+Server" in conn_string

    def test_special_characters_are_quoted(self):
        conn_string = get_conn_string(
            username="sa", password="p@ss:w/rd!", hostname="localhost", db_name="test"
        )
        # an unquoted '@' or '/' would break URL parsing and silently reinterpret the host
        assert "p%40ss%3Aw%2Frd%21" in conn_string

    def test_params_passed_through(self):
        conn_string = get_conn_string(
            username="sa",
            password="pw",
            hostname="localhost",
            db_name="test",
            params={"TrustServerCertificate": "yes", "Encrypt": "no"},
        )
        assert "TrustServerCertificate=yes" in conn_string
        assert "Encrypt=no" in conn_string


class TestVersionParsing:
    @pytest.mark.parametrize(
        "raw,expected",
        [
            ("16.0.4265.3", (16, 0, 4265, 3)),
            ("15.0.2000.5", (15, 0, 2000, 5)),
            ("14.0.1000", (14, 0, 1000)),
        ],
    )
    def test_parse(self, raw, expected):
        assert parse_mssql_version(raw) == expected

    def test_ordering(self):
        assert parse_mssql_version("16.0.4265.3") > parse_mssql_version("14.0.1000.169")
