"""End-to-end tests for loading a DagsterInstance backed by SQL Server.

Everything else in this suite constructs the storage classes directly. These go through
``dagster.yaml``, which is how a deployment actually reaches them -- and therefore through
``mssql_config()``, ``InstanceRef``, and the ``storage: mssql:`` branch in dagster core.
None of that is exercised by instantiating ``MSSQLRunStorage`` in a test.
"""

import logging
from tempfile import TemporaryDirectory
from urllib.parse import urlparse

import pytest
import sqlalchemy as db
import yaml
from dagster._core.instance import DagsterInstance
from dagster._core.instance.ref import InstanceRef
from dagster._core.storage.sql import create_engine
from dagster._core.test_utils import instance_for_test
from dagster._serdes import ConfigurableClassData
from dagster_mssql import (
    DagsterMSSQLStorage,
    MSSQLEventLogStorage,
    MSSQLRunStorage,
    MSSQLScheduleStorage,
)
from dagster_mssql.utils import mssql_isolation_level, warn_if_read_committed_snapshot_disabled
from dagster_shared.yaml_utils import safe_load_yaml
from sqlalchemy.pool import NullPool

TEST_PASSWORD = "Dagster!Passw0rd"
DRIVER = "ODBC Driver 18 for SQL Server"


def split_storage_config(hostname, port):
    """The legacy form: each storage configured separately."""
    return f"""
      run_storage:
        module: dagster_mssql.run_storage
        class: MSSQLRunStorage
        config:
          mssql_db:
            username: sa
            password: "{TEST_PASSWORD}"
            hostname: {hostname}
            port: {port}
            db_name: test
            driver: "{DRIVER}"
            params:
              TrustServerCertificate: "yes"

      event_log_storage:
        module: dagster_mssql.event_log
        class: MSSQLEventLogStorage
        config:
          mssql_db:
            username: sa
            password: "{TEST_PASSWORD}"
            hostname: {hostname}
            port: {port}
            db_name: test
            driver: "{DRIVER}"
            params:
              TrustServerCertificate: "yes"

      schedule_storage:
        module: dagster_mssql.schedule_storage
        class: MSSQLScheduleStorage
        config:
          mssql_db:
            username: sa
            password: "{TEST_PASSWORD}"
            hostname: {hostname}
            port: {port}
            db_name: test
            driver: "{DRIVER}"
            params:
              TrustServerCertificate: "yes"
    """


def unified_storage_config(hostname, port):
    """The `storage: mssql:` form, which routes through dagster core's InstanceRef."""
    return f"""
      storage:
        mssql:
          mssql_db:
            username: sa
            password: "{TEST_PASSWORD}"
            hostname: {hostname}
            db_name: test
            port: {port}
            driver: "{DRIVER}"
            params:
              TrustServerCertificate: "yes"
    """


def url_storage_config(conn_string):
    return f"""
      storage:
        mssql:
          mssql_url: "{conn_string}"
    """


@pytest.fixture
def host_and_port(conn_string):
    parsed = urlparse(conn_string)
    return parsed.hostname, parsed.port


def _set_rcsi(conn_string: str, state: str) -> None:
    """Toggle READ_COMMITTED_SNAPSHOT on the test database.

    Runs from `master` in AUTOCOMMIT: ALTER DATABASE is rejected inside a multi-statement
    transaction, and ROLLBACK IMMEDIATE would otherwise sever the connection issuing it.
    """
    master = conn_string.replace("/test?", "/master?")
    engine = create_engine(master, isolation_level="AUTOCOMMIT", poolclass=NullPool)
    try:
        with engine.connect() as conn:
            conn.execute(
                db.text(
                    f"ALTER DATABASE test SET READ_COMMITTED_SNAPSHOT {state} "
                    "WITH ROLLBACK IMMEDIATE"
                )
            )
    finally:
        engine.dispose()


class TestLoadFromConfig:
    def test_split_storage_config(self, conn_string, host_and_port):
        MSSQLEventLogStorage.wipe_storage(conn_string)
        MSSQLRunStorage.wipe_storage(conn_string)
        MSSQLScheduleStorage.wipe_storage(conn_string)

        with instance_for_test(
            overrides=safe_load_yaml(split_storage_config(*host_and_port))
        ) as instance:
            assert isinstance(instance.run_storage, MSSQLRunStorage)
            assert isinstance(instance.event_log_storage, MSSQLEventLogStorage)
            assert isinstance(instance.schedule_storage, MSSQLScheduleStorage)

    def test_unified_storage_config(self, conn_string, host_and_port):
        """`storage: mssql:` goes through the branch added to dagster core's InstanceRef.

        A typo there resolves to the wrong class, or to none at all, and no other test in
        this suite would notice.
        """
        MSSQLEventLogStorage.wipe_storage(conn_string)
        MSSQLRunStorage.wipe_storage(conn_string)
        MSSQLScheduleStorage.wipe_storage(conn_string)

        with instance_for_test(
            overrides=safe_load_yaml(unified_storage_config(*host_and_port))
        ) as instance:
            assert isinstance(instance.run_storage, MSSQLRunStorage)
            assert isinstance(instance.event_log_storage, MSSQLEventLogStorage)
            assert isinstance(instance.schedule_storage, MSSQLScheduleStorage)

    def test_mssql_url_form(self, conn_string):
        with instance_for_test(
            overrides=safe_load_yaml(url_storage_config(conn_string))
        ) as instance:
            assert isinstance(instance.run_storage, MSSQLRunStorage)

    def test_composite_storage_data_rehydrates(self, conn_string):
        """The three *_storage_data properties are what InstanceRef persists and reloads.

        If any of them names a class that does not exist, or a module it does not live in,
        the instance still constructs fine and only fails when something later reads the
        ref back.
        """
        inst_data = ConfigurableClassData(
            "dagster_mssql",
            "DagsterMSSQLStorage",
            yaml.dump({"mssql_url": conn_string}),
        )
        storage = DagsterMSSQLStorage.from_config_value(inst_data, {"mssql_url": conn_string})

        for data, expected in (
            (storage.run_storage_data, MSSQLRunStorage),
            (storage.event_storage_data, MSSQLEventLogStorage),
            (storage.schedule_storage_data, MSSQLScheduleStorage),
        ):
            assert data is not None
            assert data.module_name == "dagster_mssql"
            rehydrated = data.rehydrate()
            assert isinstance(rehydrated, expected)

    def test_writes_and_reads_back(self, conn_string):
        """A smoke test that the instance is actually usable, not merely constructible."""
        with instance_for_test(
            overrides=safe_load_yaml(url_storage_config(conn_string))
        ) as instance:
            instance.upgrade()
            assert instance.get_runs() is not None
            assert instance.all_asset_keys() == [] or instance.all_asset_keys() is not None
            instance.run_storage.set_cursor_values({"test_cursor": "café-日本語"})
            assert instance.run_storage.get_cursor_values({"test_cursor"}) == {
                "test_cursor": "café-日本語"
            }


def test_connection_leak(conn_string, host_and_port):
    """Instances must not each hold a connection open.

    dagster constructs a DagsterInstance per code location and per run launch; if each one
    kept a connection, a busy deployment would exhaust SQL Server's connection limit --
    and on Azure SQL that limit is a per-tier quota, not a tunable.
    """
    num_instances = 20

    with TemporaryDirectory() as tempdir:
        copies = [
            DagsterInstance.from_ref(
                InstanceRef.from_dir(
                    tempdir, overrides=safe_load_yaml(split_storage_config(*host_and_port))
                )
            )
            for _ in range(num_instances)
        ]

        engine = create_engine(
            conn_string, isolation_level=mssql_isolation_level(), poolclass=NullPool
        )
        try:
            with engine.connect() as conn:
                sessions = conn.execute(
                    db.text("SELECT COUNT(*) FROM sys.dm_exec_sessions WHERE database_id = DB_ID()")
                ).scalar()
        finally:
            engine.dispose()

        # Includes this connection and any internal ones; the point is that it did not
        # scale with the number of instances.
        assert sessions < num_instances

        for copy in copies:
            copy.dispose()


class TestReadCommittedSnapshotWarning:
    """RCSI off is a real performance cliff whose symptom is nothing like its cause.

    Without it SQL Server takes shared read locks, so the daemon and the webserver block
    each other; what an operator sees is intermittent timeouts under load. The warning is
    the only thing connecting the two.
    """

    def test_reports_enabled_on_the_test_database(self, conn_string, caplog):
        # the test harness turns RCSI on, matching what the docs tell operators to do
        engine = create_engine(conn_string, poolclass=NullPool)
        try:
            with caplog.at_level(logging.WARNING):
                assert warn_if_read_committed_snapshot_disabled(engine) is True
            assert "READ_COMMITTED_SNAPSHOT" not in caplog.text
        finally:
            engine.dispose()

    def test_warns_when_disabled(self, conn_string, caplog, monkeypatch):
        import dagster_mssql.utils as utils

        monkeypatch.setattr(utils, "_RCSI_WARNED", set())
        engine = create_engine(conn_string, poolclass=NullPool)
        try:
            _set_rcsi(conn_string, "OFF")
            try:
                with caplog.at_level(logging.WARNING):
                    assert warn_if_read_committed_snapshot_disabled(engine) is False
                assert "READ_COMMITTED_SNAPSHOT is not enabled" in caplog.text
                assert "ALTER DATABASE" in caplog.text  # the message says how to fix it

                # a second call stays quiet: three storages share one database and should
                # not produce three copies of the same warning
                caplog.clear()
                with caplog.at_level(logging.WARNING):
                    warn_if_read_committed_snapshot_disabled(engine)
                assert "READ_COMMITTED_SNAPSHOT" not in caplog.text
            finally:
                _set_rcsi(conn_string, "ON")
        finally:
            engine.dispose()

    def test_unreadable_setting_does_not_raise(self, monkeypatch):
        """A locked-down deployment may refuse the query; that must not break startup."""
        import sqlalchemy.exc as db_exc

        class FailingEngine:
            def connect(self):
                raise db_exc.OperationalError("SELECT", {}, Exception("permission denied"))

        assert warn_if_read_committed_snapshot_disabled(FailingEngine()) is None
