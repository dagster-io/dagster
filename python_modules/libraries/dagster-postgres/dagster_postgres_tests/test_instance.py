import pytest
import sqlalchemy as db
import yaml
from dagster_postgres.utils import get_conn

from dagster.core.instance import DagsterInstance


def full_pg_config(hostname):
    return """
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
    """.format(
        hostname=hostname
    )


def test_connection_leak(hostname, conn_string):
    num_instances = 20

    copies = []
    for _ in range(num_instances):
        copies.append(
            DagsterInstance.local_temp(overrides=yaml.safe_load(full_pg_config(hostname)))
        )

    with get_conn(conn_string).cursor() as curs:
        # count open connections
        curs.execute("SELECT count(*) from pg_stat_activity")
        res = curs.fetchall()

    # This includes a number of internal connections, so just ensure it did not scale
    # with number of instances
    assert res[0][0] < num_instances


def test_statement_timeouts(hostname):
    with DagsterInstance.local_temp(overrides=yaml.safe_load(full_pg_config(hostname))) as instance:
        instance.optimize_for_dagit(statement_timeout=500)  # 500ms

        # ensure migration error is not raised by being up to date
        instance.upgrade()

        with pytest.raises(db.exc.OperationalError, match="QueryCanceled"):
            with instance._run_storage.connect() as conn:  # pylint: disable=protected-access
                conn.execute("select pg_sleep(1)").fetchone()

        with pytest.raises(db.exc.OperationalError, match="QueryCanceled"):
            with instance._event_storage.connect() as conn:  # pylint: disable=protected-access
                conn.execute("select pg_sleep(1)").fetchone()

        with pytest.raises(db.exc.OperationalError, match="QueryCanceled"):
            with instance._schedule_storage.connect() as conn:  # pylint: disable=protected-access
                conn.execute("select pg_sleep(1)").fetchone()
