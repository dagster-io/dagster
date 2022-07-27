import os
import subprocess
from contextlib import contextmanager
from tempfile import TemporaryDirectory

import dagster._check as check
from dagster import file_relative_path
from dagster._core.test_utils import instance_for_test
from dagster._utils import merge_dicts

BUILDKITE = bool(os.getenv("BUILDKITE"))


@contextmanager
def mysql_instance_for_test(dunder_file, container_name, overrides=None):
    with TemporaryDirectory() as temp_dir:
        with TestMySQLInstance.docker_service_up_or_skip(
            file_relative_path(dunder_file, "docker-compose.yml"),
            container_name,
        ) as mysql_conn_string:
            TestMySQLInstance.clean_run_storage(mysql_conn_string)
            TestMySQLInstance.clean_event_log_storage(mysql_conn_string)
            TestMySQLInstance.clean_schedule_storage(mysql_conn_string)
            with instance_for_test(
                temp_dir=temp_dir,
                overrides=merge_dicts(
                    {
                        "run_storage": {
                            "module": "dagster_mysql.run_storage.run_storage",
                            "class": "MySQLRunStorage",
                            "config": {"mysql_url": mysql_conn_string},
                        },
                        "event_log_storage": {
                            "module": "dagster_mysql.event_log.event_log",
                            "class": "MySQLEventLogStorage",
                            "config": {"mysql_url": mysql_conn_string},
                        },
                        "schedule_storage": {
                            "module": "dagster_mysql.schedule_storage.schedule_storage",
                            "class": "MySQLScheduleStorage",
                            "config": {"mysql_url": mysql_conn_string},
                        },
                    },
                    overrides if overrides else {},
                ),
            ) as instance:
                yield instance


class TestMySQLInstance:
    @staticmethod
    def dagster_mysql_installed():
        try:
            import dagster_mysql  # pylint: disable=unused-import
        except ImportError:
            return False
        return True

    @staticmethod
    def get_hostname(env_name="MYSQL_TEST_DB_HOST"):
        # In buildkite we get the ip address from this variable (see buildkite code for commentary)
        # Otherwise assume local development and assume localhost (needs to be 127.0.0.1 for MySQL,
        # "localhost" denotes a socket-based connection)
        return os.environ.get(env_name, "127.0.0.1")

    @staticmethod
    def conn_string(**kwargs):
        check.invariant(
            TestMySQLInstance.dagster_mysql_installed(),
            "dagster_mysql must be installed to test with mysql",
        )
        from dagster_mysql.utils import get_conn_string  # pylint: disable=import-error

        return get_conn_string(
            **dict(
                dict(
                    username="test",
                    password="test",
                    hostname=TestMySQLInstance.get_hostname(),
                    db_name="test",
                ),
                **kwargs,
            )
        )

    @staticmethod
    def clean_run_storage(conn_string):
        check.invariant(
            TestMySQLInstance.dagster_mysql_installed(),
            "dagster_mysql must be installed to test with mysql",
        )
        from dagster_mysql.run_storage import MySQLRunStorage  # pylint: disable=import-error

        storage = MySQLRunStorage.create_clean_storage(conn_string)
        assert storage
        return storage

    @staticmethod
    def clean_event_log_storage(conn_string):
        check.invariant(
            TestMySQLInstance.dagster_mysql_installed(),
            "dagster_mysql must be installed to test with mysql",
        )
        from dagster_mysql.event_log import MySQLEventLogStorage  # pylint: disable=import-error

        storage = MySQLEventLogStorage.create_clean_storage(conn_string)
        assert storage
        return storage

    @staticmethod
    def clean_schedule_storage(conn_string):
        check.invariant(
            TestMySQLInstance.dagster_mysql_installed(),
            "dagster_mysql must be installed to test with mysql",
        )
        from dagster_mysql.schedule_storage.schedule_storage import (  # pylint: disable=import-error
            MySQLScheduleStorage,
        )

        storage = MySQLScheduleStorage.create_clean_storage(conn_string)
        assert storage
        return storage

    @staticmethod
    @contextmanager
    def docker_service_up(docker_compose_file, service_name, conn_args=None):
        check.invariant(
            TestMySQLInstance.dagster_mysql_installed(),
            "dagster_mysql must be installed to test with mysql",
        )
        check.str_param(service_name, "service_name")
        check.str_param(docker_compose_file, "docker_compose_file")
        check.invariant(
            os.path.isfile(docker_compose_file), "docker_compose_file must specify a valid file"
        )
        conn_args = check.opt_dict_param(conn_args, "conn_args") if conn_args else {}

        from dagster_mysql.utils import wait_for_connection  # pylint: disable=import-error

        if BUILDKITE:
            yield TestMySQLInstance.conn_string(
                **conn_args
            )  # buildkite docker is handled in pipeline setup
            return

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
            raise MySQLDockerError(
                "Failed to launch docker container(s) via docker-compose: {}".format(err_text),
                ex,
            ) from ex

        conn_str = TestMySQLInstance.conn_string(**conn_args)
        wait_for_connection(conn_str, retry_limit=10, retry_wait=3)
        yield conn_str

        try:
            subprocess.check_output(
                ["docker-compose", "-f", docker_compose_file, "stop", service_name]
            )
            subprocess.check_output(
                ["docker-compose", "-f", docker_compose_file, "rm", "-f", service_name]
            )
        except subprocess.CalledProcessError:
            pass

    @staticmethod
    @contextmanager
    def docker_service_up_or_skip(docker_compose_file, service_name, conn_args=None):
        with TestMySQLInstance.docker_service_up(
            docker_compose_file, service_name, conn_args
        ) as conn_str:
            yield conn_str


def is_mysql_running(service_name):
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
            raise MySQLDockerError("Cannot connect to the Docker daemon", ex) from ex
        else:
            raise MySQLDockerError(
                "Could not verify mysql container was running as expected", ex
            ) from ex

    decoded = output.decode()
    lines = decoded.split("\n")

    # header, one line for container, trailing \n
    # if container is found, service_name should appear at the end of the second line of output
    return len(lines) == 3 and lines[1].endswith(service_name)


class MySQLDockerError(Exception):
    def __init__(self, message, subprocess_error):
        super(MySQLDockerError, self).__init__(check.opt_str_param(message, "message"))
        self.subprocess_error = check.inst_param(
            subprocess_error, "subprocess_error", subprocess.CalledProcessError
        )
