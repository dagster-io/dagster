import os
import subprocess
import warnings
from contextlib import contextmanager

import pytest

from dagster import check

BUILDKITE = bool(os.getenv("BUILDKITE"))


class TestPostgresInstance:
    @staticmethod
    def dagster_postgres_installed():
        try:
            import dagster_postgres  # pylint: disable=unused-import
        except ImportError:
            return False
        return True

    @staticmethod
    def get_hostname(env_name="POSTGRES_TEST_DB_HOST"):
        # In buildkite we get the ip address from this variable (see buildkite code for commentary)
        # Otherwise assume local development and assume localhost
        return os.environ.get(env_name, "localhost")

    @staticmethod
    def conn_string(**kwargs):
        check.invariant(
            TestPostgresInstance.dagster_postgres_installed(),
            "dagster_postgres must be installed to test with postgres",
        )
        from dagster_postgres.utils import get_conn_string  # pylint: disable=import-error

        return get_conn_string(
            **dict(
                dict(
                    username="test",
                    password="test",
                    hostname=TestPostgresInstance.get_hostname(),
                    db_name="test",
                ),
                **kwargs
            )
        )

    @staticmethod
    def clean_run_storage(conn_string):
        check.invariant(
            TestPostgresInstance.dagster_postgres_installed(),
            "dagster_postgres must be installed to test with postgres",
        )
        from dagster_postgres.run_storage import PostgresRunStorage  # pylint: disable=import-error

        storage = PostgresRunStorage.create_clean_storage(conn_string)
        assert storage
        return storage

    @staticmethod
    def clean_event_log_storage(conn_string):
        check.invariant(
            TestPostgresInstance.dagster_postgres_installed(),
            "dagster_postgres must be installed to test with postgres",
        )
        from dagster_postgres.event_log import (  # pylint: disable=import-error
            PostgresEventLogStorage,
        )

        storage = PostgresEventLogStorage.create_clean_storage(conn_string)
        assert storage
        return storage

    @staticmethod
    def clean_schedule_storage(conn_string):
        check.invariant(
            TestPostgresInstance.dagster_postgres_installed(),
            "dagster_postgres must be installed to test with postgres",
        )
        from dagster_postgres.schedule_storage.schedule_storage import (  # pylint: disable=import-error
            PostgresScheduleStorage,
        )

        storage = PostgresScheduleStorage.create_clean_storage(conn_string)
        assert storage
        return storage

    @staticmethod
    @contextmanager
    def docker_service_up(docker_compose_file, service_name, conn_args=None):
        check.invariant(
            TestPostgresInstance.dagster_postgres_installed(),
            "dagster_postgres must be installed to test with postgres",
        )
        check.str_param(service_name, "service_name")
        check.str_param(docker_compose_file, "docker_compose_file")
        check.invariant(
            os.path.isfile(docker_compose_file), "docker_compose_file must specify a valid file"
        )
        conn_args = check.opt_dict_param(conn_args, "conn_args") if conn_args else {}

        from dagster_postgres.utils import wait_for_connection  # pylint: disable=import-error

        if BUILDKITE:
            yield TestPostgresInstance.conn_string(
                **conn_args
            )  # buildkite docker is handled in pipeline setup
            return

        if not is_postgres_running(service_name):
            try:
                subprocess.check_output(
                    ["docker-compose", "-f", docker_compose_file, "stop", service_name]
                )
                subprocess.check_output(
                    ["docker-compose", "-f", docker_compose_file, "rm", "-f", service_name]
                )
            except subprocess.CalledProcessError:
                pass

            try:
                subprocess.check_output(
                    ["docker-compose", "-f", docker_compose_file, "up", "-d", service_name],
                    stderr=subprocess.STDOUT,  # capture STDERR for error handling
                )
            except subprocess.CalledProcessError as ex:
                err_text = ex.output.decode()
                raise PostgresDockerError(
                    "Failed to launch docker container(s) via docker-compose: {}".format(err_text),
                    ex,
                )

        conn_str = TestPostgresInstance.conn_string(**conn_args)
        wait_for_connection(conn_str)
        yield conn_str

    @staticmethod
    @contextmanager
    def docker_service_up_or_skip(docker_compose_file, service_name, conn_args=None):
        try:
            with TestPostgresInstance.docker_service_up(
                docker_compose_file, service_name, conn_args
            ) as conn_str:
                yield conn_str
        except PostgresDockerError as ex:
            warnings.warn(
                "Error launching Dockerized Postgres: {}".format(ex), RuntimeWarning, stacklevel=3
            )
            pytest.skip("Skipping due to error launching Dockerized Postgres: {}".format(ex))


def is_postgres_running(service_name):
    check.str_param(service_name, "service_name")
    try:
        output = subprocess.check_output(
            [
                "docker",
                "container",
                "ps",
                "-f",
                "name={}".format(service_name),
                "-f",
                "status=running",
            ],
            stderr=subprocess.STDOUT,  # capture STDERR for error handling
        )
    except subprocess.CalledProcessError as ex:
        lines = ex.output.decode().split("\n")
        if len(lines) == 2 and "Cannot connect to the Docker daemon" in lines[0]:
            raise PostgresDockerError("Cannot connect to the Docker daemon", ex)
        else:
            raise PostgresDockerError(
                "Could not verify postgres container was running as expected", ex
            )

    decoded = output.decode()
    lines = decoded.split("\n")

    # header, one line for container, trailing \n
    # if container is found, service_name should appear at the end of the second line of output
    return len(lines) == 3 and lines[1].endswith(service_name)


class PostgresDockerError(Exception):
    def __init__(self, message, subprocess_error):
        super(PostgresDockerError, self).__init__(check.opt_str_param(message, "message"))
        self.subprocess_error = check.inst_param(
            subprocess_error, "subprocess_error", subprocess.CalledProcessError
        )
