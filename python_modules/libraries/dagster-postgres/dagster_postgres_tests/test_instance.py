import tempfile
from urllib.parse import unquote, urlparse

import pytest
import sqlalchemy as db
import yaml
from dagster._core.instance import DagsterInstance
from dagster._core.instance.ref import InstanceRef
from dagster._core.test_utils import instance_for_test
from dagster._utils.test.postgres_instance import TestPostgresInstance
from dagster_postgres.utils import get_conn, get_conn_string


def full_pg_config(hostname):
    return f"""
      run_storage:
        module: dagster_postgres.run_storage
        class: PostgresRunStorage
        config:
          postgres_db:
            username: test
            password: test
            hostname: {hostname}
            db_name: test

      event_log_storage:
        module: dagster_postgres.event_log
        class: PostgresEventLogStorage
        config:
            postgres_db:
              username: test
              password: test
              hostname: {hostname}
              db_name: test

      schedule_storage:
        module: dagster_postgres.schedule_storage
        class: PostgresScheduleStorage
        config:
            postgres_db:
              username: test
              password: test
              hostname: {hostname}
              db_name: test
    """


def unified_pg_config(hostname):
    return f"""
      storage:
        postgres:
          postgres_db:
            username: test
            password: test
            hostname: {hostname}
            db_name: test

    """


def skip_autocreate_pg_config(hostname):
    return f"""
      run_storage:
        module: dagster_postgres.run_storage
        class: PostgresRunStorage
        config:
          should_autocreate_tables: false
          postgres_db:
            username: test
            password: test
            hostname: {hostname}
            db_name: test

      event_log_storage:
        module: dagster_postgres.event_log
        class: PostgresEventLogStorage
        config:
            should_autocreate_tables: false
            postgres_db:
              username: test
              password: test
              hostname: {hostname}
              db_name: test

      schedule_storage:
        module: dagster_postgres.schedule_storage
        class: PostgresScheduleStorage
        config:
            should_autocreate_tables: false
            postgres_db:
              username: test
              password: test
              hostname: {hostname}
              db_name: test
    """


def params_specified_pg_config(hostname):
    return f"""
      run_storage:
        module: dagster_postgres.run_storage
        class: PostgresRunStorage
        config:
          should_autocreate_tables: false
          postgres_db:
            username: test
            password: test
            hostname: {hostname}
            db_name: test
            params:
              connect_timeout: 10
              application_name: myapp
              options: -c synchronous_commit=off

      event_log_storage:
        module: dagster_postgres.event_log
        class: PostgresEventLogStorage
        config:
            should_autocreate_tables: false
            postgres_db:
              username: test
              password: test
              hostname: {hostname}
              db_name: test
              params:
                connect_timeout: 10
                application_name: myapp
                options: -c synchronous_commit=off

      schedule_storage:
        module: dagster_postgres.schedule_storage
        class: PostgresScheduleStorage
        config:
            should_autocreate_tables: false
            postgres_db:
              username: test
              password: test
              hostname: {hostname}
              db_name: test
              params:
                connect_timeout: 10
                application_name: myapp
                options: -c synchronous_commit=off
    """


def schema_specified_pg_config(hostname):
    return f"""
      storage:
        postgres:
          postgres_db:
            username: test
            password: test
            hostname: {hostname}
            db_name: test
            params:
              options: -c search_path=other_schema
    """


def test_load_instance(hostname):
    with instance_for_test(overrides=yaml.safe_load(full_pg_config(hostname))):
        pass

    with instance_for_test(overrides=yaml.safe_load(unified_pg_config(hostname))):
        pass


def test_connection_leak(hostname, conn_string):
    num_instances = 20

    tempdir = tempfile.TemporaryDirectory()
    copies = []
    for _ in range(num_instances):
        copies.append(
            DagsterInstance.from_ref(
                InstanceRef.from_dir(
                    tempdir.name, overrides=yaml.safe_load(full_pg_config(hostname))
                )
            )
        )

    with get_conn(conn_string).cursor() as curs:
        # count open connections
        curs.execute("SELECT count(*) from pg_stat_activity")
        res = curs.fetchall()

    # This includes a number of internal connections, so just ensure it did not scale
    # with number of instances
    assert res[0][0] < num_instances

    for copy in copies:
        copy.dispose()

    tempdir.cleanup()


def test_statement_timeouts(hostname):
    with instance_for_test(overrides=yaml.safe_load(full_pg_config(hostname))) as instance:
        instance.optimize_for_webserver(
            statement_timeout=500, pool_recycle=-1, max_overflow=20
        )  # 500ms

        # ensure migration error is not raised by being up to date
        instance.upgrade()

        with pytest.raises(db.exc.OperationalError, match="QueryCanceled"):  # pyright: ignore[reportAttributeAccessIssue]
            with instance._run_storage.connect() as conn:  # noqa: SLF001  # pyright: ignore[reportAttributeAccessIssue]
                conn.execute(db.text("select pg_sleep(1)")).fetchone()

        with pytest.raises(db.exc.OperationalError, match="QueryCanceled"):  # pyright: ignore[reportAttributeAccessIssue]
            with instance._event_storage._connect() as conn:  # noqa: SLF001  # pyright: ignore[reportAttributeAccessIssue]
                conn.execute(db.text("select pg_sleep(1)")).fetchone()

        with pytest.raises(db.exc.OperationalError, match="QueryCanceled"):  # pyright: ignore[reportAttributeAccessIssue]
            with instance._schedule_storage.connect() as conn:  # noqa: SLF001  # pyright: ignore[reportOptionalMemberAccess,reportAttributeAccessIssue]
                conn.execute(db.text("select pg_sleep(1)")).fetchone()


def test_skip_autocreate(hostname, conn_string):
    TestPostgresInstance.clean_run_storage(conn_string, should_autocreate_tables=False)
    TestPostgresInstance.clean_event_log_storage(conn_string, should_autocreate_tables=False)
    TestPostgresInstance.clean_schedule_storage(conn_string, should_autocreate_tables=False)

    with instance_for_test(
        overrides=yaml.safe_load(skip_autocreate_pg_config(hostname))
    ) as instance:
        with pytest.raises(db.exc.ProgrammingError):  # pyright: ignore[reportAttributeAccessIssue]
            instance.get_runs()

        with pytest.raises(db.exc.ProgrammingError):  # pyright: ignore[reportAttributeAccessIssue]
            instance.all_asset_keys()

        with pytest.raises(db.exc.ProgrammingError):  # pyright: ignore[reportAttributeAccessIssue]
            instance.all_instigator_state()

    with instance_for_test(overrides=yaml.safe_load(full_pg_config(hostname))) as instance:
        instance.get_runs()
        instance.all_asset_keys()
        instance.all_instigator_state()

    TestPostgresInstance.clean_run_storage(conn_string, should_autocreate_tables=False)
    TestPostgresInstance.clean_event_log_storage(conn_string, should_autocreate_tables=False)
    TestPostgresInstance.clean_schedule_storage(conn_string, should_autocreate_tables=False)


def test_specify_pg_params(hostname):
    with instance_for_test(
        overrides=yaml.safe_load(params_specified_pg_config(hostname))
    ) as instance:
        postgres_url = f"postgresql://test:test@{hostname}:5432/test?application_name=myapp&connect_timeout=10&options=-c%20synchronous_commit%3Doff"

        assert instance._event_storage.postgres_url == postgres_url  # noqa: SLF001  # pyright: ignore[reportAttributeAccessIssue]
        assert instance._run_storage.postgres_url == postgres_url  # noqa: SLF001  # pyright: ignore[reportAttributeAccessIssue]
        assert instance._schedule_storage.postgres_url == postgres_url  # noqa: SLF001  # pyright: ignore[reportOptionalMemberAccess,reportAttributeAccessIssue]


def test_conn_str():
    username = "has@init"
    password = ":full: of junk!@?"
    db_name = "dagster"
    hostname = "database-city.com"

    url_wo_scheme = r"has%40init:%3Afull%3A%20of%20junk%21%40%3F@database-city.com:5432/dagster"

    conn_str = get_conn_string(
        username=username,
        password=password,
        db_name=db_name,
        hostname=hostname,
    )
    assert conn_str == f"postgresql://{url_wo_scheme}"
    parsed = urlparse(conn_str)
    assert unquote(parsed.username) == username  # pyright: ignore[reportArgumentType]
    assert unquote(parsed.password) == password  # pyright: ignore[reportArgumentType]
    assert parsed.hostname == hostname
    assert parsed.scheme == "postgresql"

    custom_scheme = "postgresql+dialect"
    conn_str = get_conn_string(
        username=username,
        password=password,
        db_name=db_name,
        hostname=hostname,
        scheme=custom_scheme,
    )

    assert conn_str == f"postgresql+dialect://{url_wo_scheme}"
    parsed = urlparse(conn_str)
    assert unquote(parsed.username) == username  # pyright: ignore[reportArgumentType]
    assert unquote(parsed.password) == password  # pyright: ignore[reportArgumentType]
    assert parsed.hostname == hostname
    assert parsed.scheme == custom_scheme


def test_configured_other_schema(hostname):
    with db.create_engine(
        get_conn_string(
            username="test",
            password="test",
            db_name="test",
            hostname=hostname,
        )
    ).connect() as conn:
        with conn.begin():
            conn.execute(db.text("create schema other_schema;"))

    with instance_for_test(
        overrides=yaml.safe_load(schema_specified_pg_config(hostname))
    ) as instance:
        instance.get_runs()
        instance.all_asset_keys()
        instance.all_instigator_state()
        instance.optimize_for_webserver(statement_timeout=100, pool_recycle=100, max_overflow=20)
        instance.get_runs()
        instance.all_asset_keys()
        instance.all_instigator_state()
