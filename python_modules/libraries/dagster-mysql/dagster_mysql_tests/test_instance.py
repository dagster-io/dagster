from tempfile import TemporaryDirectory

import pytest
import sqlalchemy as db
import yaml
from dagster.core.instance import DagsterInstance, InstanceRef
from dagster.core.test_utils import instance_for_test
from dagster_mysql.utils import get_conn


def full_mysql_config(hostname):
    return """
      run_storage:
        module: dagster_mysql.run_storage
        class: MySQLRunStorage
        config:
          mysql_db:
            username: test
            password: test
            hostname: {hostname}
            db_name: test

      event_log_storage:
        module: dagster_mysql.event_log
        class: MySQLEventLogStorage
        config:
            mysql_db:
              username: test
              password: test
              hostname: {hostname}
              db_name: test

      schedule_storage:
        module: dagster_mysql.schedule_storage
        class: MySQLScheduleStorage
        config:
            mysql_db:
              username: test
              password: test
              hostname: {hostname}
              db_name: test
    """.format(
        hostname=hostname
    )


def test_connection_leak(hostname, conn_string):
    num_instances = 20

    tempdir = TemporaryDirectory()
    copies = []
    for _ in range(num_instances):
        copies.append(
            DagsterInstance.from_ref(
                InstanceRef.from_dir(
                    tempdir.name, overrides=yaml.safe_load(full_mysql_config(hostname))
                )
            )
        )

    with get_conn(conn_string) as conn:
        curs = conn.cursor()
        # count open connections
        curs.execute("SELECT count(*) FROM information_schema.processlist")
        res = curs.fetchall()

    # This includes a number of internal connections, so just ensure it did not scale
    # with number of instances
    assert res[0][0] < num_instances

    for copy in copies:
        copy.dispose()

    tempdir.cleanup()


@pytest.mark.skip("https://github.com/dagster-io/dagster/issues/3719")
def test_statement_timeouts(hostname):
    with instance_for_test(overrides=yaml.safe_load(full_mysql_config(hostname))) as instance:
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
