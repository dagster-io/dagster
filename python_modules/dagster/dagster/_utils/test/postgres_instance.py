import os
import subprocess
import warnings
from contextlib import contextmanager

import pytest

import dagster._check as check

BUILDKITE = bool(os.getenv("BUILDKITE"))


class TestPostgresInstance:
    @staticmethod
    def dagster_postgres_installed():
        try:
            import dagster_postgres  # noqa: F401
        except ImportError:
            return False
        return True

    @staticmethod
    def get_hostname(env_name="POSTGRES_TEST_DB_HOST"):
        # In buildkite we get the ip address from this variable (see buildkite code for commentary)
        # Otherwise assume local development and assume localhost
        return os.getenv(env_name, "localhost")

    @staticmethod
    def conn_string(env_name="POSTGRES_TEST_DB_HOST", **kwargs):
        check.invariant(
            TestPostgresInstance.dagster_postgres_installed(),
            "dagster_postgres must be installed to test with postgres",
        )
        from dagster_postgres.utils import get_conn_string

        return get_conn_string(
            **dict(  # pyright: ignore[reportArgumentType]
                dict(
                    username="test",
                    password="test",
                    hostname=TestPostgresInstance.get_hostname(env_name=env_name),
                    db_name="test",
                ),
                **kwargs,
            )
        )

    @staticmethod
    def clean_run_storage(conn_string, should_autocreate_tables=True):
        check.invariant(
            TestPostgresInstance.dagster_postgres_installed(),
            "dagster_postgres must be installed to test with postgres",
        )
        from dagster_postgres.run_storage import PostgresRunStorage

        storage = PostgresRunStorage.create_clean_storage(
            conn_string, should_autocreate_tables=should_autocreate_tables
        )
        assert storage
        return storage

    @staticmethod
    def clean_event_log_storage(conn_string, should_autocreate_tables=True):
        check.invariant(
            TestPostgresInstance.dagster_postgres_installed(),
            "dagster_postgres must be installed to test with postgres",
        )
        from dagster_postgres.event_log import PostgresEventLogStorage

        storage = PostgresEventLogStorage.create_clean_storage(
            conn_string, should_autocreate_tables=should_autocreate_tables
        )
        assert storage
        return storage

    @staticmethod
    def clean_schedule_storage(conn_string, should_autocreate_tables=True):
        check.invariant(
            TestPostgresInstance.dagster_postgres_installed(),
            "dagster_postgres must be installed to test with postgres",
        )
        from dagster_postgres.schedule_storage.schedule_storage import PostgresScheduleStorage

        storage = PostgresScheduleStorage.create_clean_storage(
            conn_string, should_autocreate_tables=should_autocreate_tables
        )
        assert storage
        return storage

    @staticmethod
    @contextmanager
    def docker_service_up(
        docker_compose_file, service_name, conn_args=None, env_name="POSTGRES_TEST_DB_HOST"
    ):
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

        from dagster_postgres.utils import wait_for_connection

        if BUILDKITE:
            yield TestPostgresInstance.conn_string(
                **conn_args,
                env_name=env_name,
            )  # buildkite docker is handled in pipeline setup
            return

        subprocess.run(
            ["docker-compose", "-f", docker_compose_file, "down", service_name],
            check=False,
        )

        try:
            subprocess.check_output(
                ["docker-compose", "-f", docker_compose_file, "up", "-d", service_name],
                stderr=subprocess.STDOUT,  # capture STDERR for error handling
            )
        except subprocess.CalledProcessError as ex:
            err_text = ex.output.decode("utf-8")
            raise PostgresDockerError(
                f"Failed to launch docker container(s) via docker-compose: {err_text}",
                ex,
            ) from ex

        conn_str = TestPostgresInstance.conn_string(**conn_args)
        wait_for_connection(conn_str, retry_limit=10, retry_wait=3)
        try:
            yield conn_str
        finally:
            subprocess.run(
                ["docker-compose", "-f", docker_compose_file, "down", service_name],
                check=False,
            )

    @staticmethod
    @contextmanager
    def docker_service_up_or_skip(
        docker_compose_file, service_name, conn_args=None, env_name="POSTGRES_TEST_DB_HOST"
    ):
        try:
            with TestPostgresInstance.docker_service_up(
                docker_compose_file, service_name, conn_args, env_name
            ) as conn_str:
                yield conn_str
        except PostgresDockerError as ex:
            warnings.warn(
                f"Error launching Dockerized Postgres: {ex}", RuntimeWarning, stacklevel=3
            )
            pytest.skip(f"Skipping due to error launching Dockerized Postgres: {ex}")


def is_postgres_running(service_name):
    check.str_param(service_name, "service_name")
    try:
        output = subprocess.check_output(
            [
                "docker",
                "container",
                "ps",
                "-f",
                f"name={service_name}",
                "-f",
                "status=running",
            ],
            stderr=subprocess.STDOUT,  # capture STDERR for error handling
        )
    except subprocess.CalledProcessError as ex:
        lines = ex.output.decode("utf-8").split("\n")
        if len(lines) == 2 and "Cannot connect to the Docker daemon" in lines[0]:
            raise PostgresDockerError("Cannot connect to the Docker daemon", ex) from ex
        else:
            raise PostgresDockerError(
                "Could not verify postgres container was running as expected", ex
            ) from ex

    decoded = output.decode("utf-8")
    lines = decoded.split("\n")

    # header, one line for container, trailing \n
    # if container is found, service_name should appear at the end of the second line of output
    return len(lines) == 3 and lines[1].endswith(service_name)


class PostgresDockerError(Exception):
    def __init__(self, message, subprocess_error):
        super().__init__(check.opt_str_param(message, "message"))
        self.subprocess_error = check.inst_param(
            subprocess_error, "subprocess_error", subprocess.CalledProcessError
        )
