import os
import subprocess
from contextlib import contextmanager

from dagster import check

BUILDKITE = bool(os.getenv('BUILDKITE'))


class TestPostgresInstance:
    @staticmethod
    def dagster_postgres_installed():
        try:
            import dagster_postgres  # pylint: disable=unused-import
        except ImportError:
            return False
        return True

    @staticmethod
    def get_hostname(env_name='POSTGRES_TEST_DB_HOST'):
        # In buildkite we get the ip address from this variable (see buildkite code for commentary)
        # Otherwise assume local development and assume localhost
        return os.environ.get(env_name, 'localhost')

    @staticmethod
    def conn_string(**kwargs):
        check.invariant(
            TestPostgresInstance.dagster_postgres_installed(),
            'dagster_postgres must be installed to test with postgres',
        )
        from dagster_postgres.utils import get_conn_string  # pylint: disable=import-error

        return get_conn_string(
            **dict(
                dict(
                    username='test',
                    password='test',
                    hostname=TestPostgresInstance.get_hostname(),
                    db_name='test',
                ),
                **kwargs
            )
        )

    @staticmethod
    def clean_run_storage():
        check.invariant(
            TestPostgresInstance.dagster_postgres_installed(),
            'dagster_postgres must be installed to test with postgres',
        )
        from dagster_postgres.run_storage import PostgresRunStorage  # pylint: disable=import-error

        storage = PostgresRunStorage.create_clean_storage(TestPostgresInstance.conn_string())
        assert storage
        return storage

    @staticmethod
    def clean_event_log_storage():
        check.invariant(
            TestPostgresInstance.dagster_postgres_installed(),
            'dagster_postgres must be installed to test with postgres',
        )
        from dagster_postgres.event_log import (  # pylint: disable=import-error
            PostgresEventLogStorage,
        )

        storage = PostgresEventLogStorage.create_clean_storage(TestPostgresInstance.conn_string())
        assert storage
        return storage

    @staticmethod
    def clean_schedule_storage():
        check.invariant(
            TestPostgresInstance.dagster_postgres_installed(),
            'dagster_postgres must be installed to test with postgres',
        )
        from dagster_postgres.schedule_storage.schedule_storage import (  # pylint: disable=import-error
            PostgresScheduleStorage,
        )

        storage = PostgresScheduleStorage.create_clean_storage(TestPostgresInstance.conn_string())
        assert storage
        return storage

    @staticmethod
    @contextmanager
    def docker_service_up(docker_compose_file, service_name):
        check.invariant(
            TestPostgresInstance.dagster_postgres_installed(),
            'dagster_postgres must be installed to test with postgres',
        )
        check.str_param(service_name, 'service_name')
        check.str_param(docker_compose_file, 'docker_compose_file')
        check.invariant(
            os.path.isfile(docker_compose_file), 'docker_compose_file must specify a valid file'
        )

        from dagster_postgres.utils import wait_for_connection  # pylint: disable=import-error

        if BUILDKITE:
            yield TestPostgresInstance.conn_string()  # buildkite docker is handled in pipeline setup
            return

        if not is_postgres_running(service_name):
            try:
                subprocess.check_output(
                    ['docker-compose', '-f', docker_compose_file, 'stop', service_name]
                )
                subprocess.check_output(
                    ['docker-compose', '-f', docker_compose_file, 'rm', '-f', service_name]
                )
            except Exception:  # pylint: disable=broad-except
                pass
            subprocess.check_output(
                ['docker-compose', '-f', docker_compose_file, 'up', '-d', service_name]
            )

        conn_str = TestPostgresInstance.conn_string()
        wait_for_connection(conn_str)
        yield conn_str


def is_postgres_running(service_name):
    check.str_param(service_name, 'service_name')
    output = subprocess.check_output(
        ['docker', 'container', 'ps', '-f', 'name={}'.format(service_name), '-f', 'status=running',]
    )
    decoded = output.decode()

    lines = decoded.split('\n')

    # header, one line for container, trailing \n
    # if container is found, service_name should appear in the second line of output
    return (len(lines) == 3) and (service_name in lines[1])
