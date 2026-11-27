import os
import tempfile
from urllib.parse import unquote, urlparse

import psycopg2
import psycopg2.extensions
import pytest
import sqlalchemy as db
import sqlalchemy.exc  # ensure db.exc submodule is statically resolvable
from dagster._core.instance import DagsterInstance
from dagster._core.instance.ref import InstanceRef
from dagster._core.test_utils import instance_for_test
from dagster_postgres.utils import get_conn_string
from dagster_shared.yaml_utils import safe_load_yaml


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
    with instance_for_test(overrides=safe_load_yaml(full_pg_config(hostname))):
        pass

    with instance_for_test(overrides=safe_load_yaml(unified_pg_config(hostname))):
        pass


def test_connection_leak(hostname, conn_string):
    num_instances = 20

    tempdir = tempfile.TemporaryDirectory()
    copies = [
        DagsterInstance.from_ref(
            InstanceRef.from_dir(tempdir.name, overrides=safe_load_yaml(full_pg_config(hostname)))
        )
        for _ in range(num_instances)
    ]

    conn = psycopg2.connect(conn_string)
    conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
    with conn.cursor() as curs:
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
    with instance_for_test(overrides=safe_load_yaml(full_pg_config(hostname))) as instance:
        instance.optimize_for_webserver(
            statement_timeout=500, pool_recycle=-1, max_overflow=20
        )  # 500ms

        # ensure migration error is not raised by being up to date
        instance.upgrade()

        with pytest.raises(db.exc.OperationalError, match="QueryCanceled"):
            with instance._run_storage.connect() as conn:  # noqa: SLF001  # ty: ignore[unresolved-attribute]
                conn.execute(db.text("select pg_sleep(1)")).fetchone()

        with pytest.raises(db.exc.OperationalError, match="QueryCanceled"):
            with instance._event_storage._connect() as conn:  # noqa: SLF001  # ty: ignore[unresolved-attribute]
                conn.execute(db.text("select pg_sleep(1)")).fetchone()

        with pytest.raises(db.exc.OperationalError, match="QueryCanceled"):
            with instance._schedule_storage.connect() as conn:  # noqa: SLF001  # ty: ignore[unresolved-attribute]
                conn.execute(db.text("select pg_sleep(1)")).fetchone()


def test_skip_autocreate(hostname, conn_string):
    with instance_for_test(overrides=safe_load_yaml(unified_pg_config(hostname))) as instance:
        instance.run_storage.create_clean_storage(conn_string, should_autocreate_tables=False)  # ty: ignore[unresolved-attribute]
        instance.event_log_storage.create_clean_storage(conn_string, should_autocreate_tables=False)  # ty: ignore[unresolved-attribute]
        instance.schedule_storage.create_clean_storage(conn_string, should_autocreate_tables=False)  # ty: ignore[unresolved-attribute]

    with instance_for_test(
        overrides=safe_load_yaml(skip_autocreate_pg_config(hostname))
    ) as instance:
        with pytest.raises(db.exc.ProgrammingError):
            instance.get_runs()

        with pytest.raises(db.exc.ProgrammingError):
            instance.all_asset_keys()

        with pytest.raises(db.exc.ProgrammingError):
            instance.all_instigator_state()

    with instance_for_test(overrides=safe_load_yaml(full_pg_config(hostname))) as instance:
        instance.get_runs()
        instance.all_asset_keys()
        instance.all_instigator_state()


def test_specify_pg_params(hostname):
    with instance_for_test(
        overrides=safe_load_yaml(params_specified_pg_config(hostname))
    ) as instance:
        postgres_url = f"postgresql://test:test@{hostname}:5432/test?application_name=myapp&connect_timeout=10&options=-c%20synchronous_commit%3Doff"

        assert instance._event_storage.postgres_url == postgres_url  # noqa: SLF001  # ty: ignore[unresolved-attribute]
        assert instance._run_storage.postgres_url == postgres_url  # noqa: SLF001  # ty: ignore[unresolved-attribute]
        assert instance._schedule_storage.postgres_url == postgres_url  # noqa: SLF001  # ty: ignore[unresolved-attribute]


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
    assert unquote(parsed.username) == username  # ty: ignore[invalid-argument-type]
    assert unquote(parsed.password) == password  # ty: ignore[invalid-argument-type]
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
    assert unquote(parsed.username) == username  # ty: ignore[invalid-argument-type]
    assert unquote(parsed.password) == password  # ty: ignore[invalid-argument-type]
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
        overrides=safe_load_yaml(schema_specified_pg_config(hostname))
    ) as instance:
        instance.get_runs()
        instance.all_asset_keys()
        instance.all_instigator_state()
        instance.optimize_for_webserver(statement_timeout=100, pool_recycle=100, max_overflow=20)
        instance.get_runs()
        instance.all_asset_keys()
        instance.all_instigator_state()


def _pg_storages(instance):
    return (instance.run_storage, instance.event_log_storage, instance.schedule_storage)


def test_connection_pool_default(conn_string):
    with instance_for_test(
        overrides={"storage": {"postgres": {"postgres_url": conn_string}}}
    ) as instance:
        for storage in _pg_storages(instance):
            assert isinstance(storage._engine.pool, db.pool.NullPool)  # noqa: SLF001


def test_connection_pool_config(conn_string):
    with instance_for_test(
        overrides={
            "storage": {
                "postgres": {
                    "postgres_url": conn_string,
                    "pool": {"pool_size": 2, "max_overflow": 1, "pool_recycle": 60},
                }
            }
        }
    ) as instance:
        pools = [storage._engine.pool for storage in _pg_storages(instance)]  # noqa: SLF001
        for pool in pools:
            assert isinstance(pool, db.pool.QueuePool)
            assert pool.size() == 2
            assert pool._max_overflow == 1  # noqa: SLF001
            assert pool._recycle == 60  # noqa: SLF001
            assert pool._pre_ping  # noqa: SLF001

        instance.wipe()
        for _ in range(10):
            instance.get_runs(limit=1)
        # every query reused the same pooled connection
        assert pools[0].checkedin() == 1

    # disposing the instance closes the pooled connections
    for pool in pools:
        assert pool.checkedin() == 0


def test_connection_pool_defaults_when_block_empty(conn_string):
    with instance_for_test(
        overrides={"storage": {"postgres": {"postgres_url": conn_string, "pool": {}}}}
    ) as instance:
        pool = instance.run_storage._engine.pool  # noqa: SLF001
        assert isinstance(pool, db.pool.QueuePool)
        assert pool.size() == 5
        assert pool._max_overflow == 10  # noqa: SLF001
        assert pool._recycle == 3600  # noqa: SLF001


def _backend_pid(storage) -> int:
    with storage.connect() as conn:
        return conn.execute(db.text("SELECT pg_backend_pid()")).scalar()


@pytest.mark.skipif(not hasattr(os, "fork"), reason="requires os.fork")
def test_connection_pool_after_fork(conn_string):
    """A forked child gets fresh pools, so disposing them leaves the parent's sessions intact."""
    with instance_for_test(
        overrides={"storage": {"postgres": {"postgres_url": conn_string, "pool": {}}}}
    ) as instance:
        run_storage = instance.run_storage
        parent_pool = run_storage._engine.pool  # noqa: SLF001
        parent_pid = _backend_pid(run_storage)
        assert parent_pool.checkedin() == 1

        child = os.fork()
        if child == 0:  # pragma: no cover - runs in the child
            exit_code = 1
            try:
                child_pool = run_storage._engine.pool  # noqa: SLF001
                if child_pool is not parent_pool and child_pool.checkedin() == 0:
                    instance.dispose()
                    exit_code = 0
            finally:
                os._exit(exit_code)

        _, wait_status = os.waitpid(child, 0)
        assert os.waitstatus_to_exitcode(wait_status) == 0
        # the parent's pooled connection survived the child's dispose
        assert _backend_pid(run_storage) == parent_pid
