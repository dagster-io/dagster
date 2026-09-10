import os
import subprocess
from contextlib import contextmanager
from tempfile import TemporaryDirectory

import dagster._check as check
from dagster import file_relative_path
from dagster._core.test_utils import instance_for_test
from dagster._utils.merger import merge_dicts

BUILDKITE = bool(os.getenv("BUILDKITE"))

TEST_MSSQL_DB_NAME = "test"
TEST_MSSQL_PASSWORD = "Dagster!Passw0rd"


@contextmanager
def mssql_instance_for_test(dunder_file, container_name, overrides=None):
    with TemporaryDirectory() as temp_dir:
        with TestMSSQLInstance.docker_service_up_or_skip(
            file_relative_path(dunder_file, "docker-compose.yml"),
            container_name,
        ) as mssql_conn_string:
            TestMSSQLInstance.clean_run_storage(mssql_conn_string)
            TestMSSQLInstance.clean_event_log_storage(mssql_conn_string)
            TestMSSQLInstance.clean_schedule_storage(mssql_conn_string)
            with instance_for_test(
                temp_dir=temp_dir,
                overrides=merge_dicts(
                    {
                        "run_storage": {
                            "module": "dagster_mssql.run_storage.run_storage",
                            "class": "MSSQLRunStorage",
                            "config": {"mssql_url": mssql_conn_string},
                        },
                        "event_log_storage": {
                            "module": "dagster_mssql.event_log.event_log",
                            "class": "MSSQLEventLogStorage",
                            "config": {"mssql_url": mssql_conn_string},
                        },
                        "schedule_storage": {
                            "module": "dagster_mssql.schedule_storage.schedule_storage",
                            "class": "MSSQLScheduleStorage",
                            "config": {"mssql_url": mssql_conn_string},
                        },
                    },
                    overrides if overrides else {},
                ),
            ) as instance:
                yield instance


class TestMSSQLInstance:
    @staticmethod
    def dagster_mssql_installed():
        try:
            import dagster_mssql  # noqa: F401
        except ImportError:
            return False
        return True

    @staticmethod
    def get_hostname(env_name="MSSQL_TEST_DB_HOST"):
        # In buildkite we get the ip address from this variable (see buildkite code for commentary)
        # Otherwise assume local development and assume localhost
        return os.environ.get(env_name, "127.0.0.1")

    @staticmethod
    def conn_string(**kwargs):
        check.invariant(
            TestMSSQLInstance.dagster_mssql_installed(),
            "dagster_mssql must be installed to test with mssql",
        )
        from dagster_mssql.utils import get_conn_string

        return get_conn_string(
            **dict(
                dict(
                    username="sa",
                    password=TEST_MSSQL_PASSWORD,
                    hostname=TestMSSQLInstance.get_hostname(),
                    db_name=TEST_MSSQL_DB_NAME,
                    # The test container serves a self-signed certificate, and ODBC Driver
                    # 18 encrypts by default, so the connection is refused without this.
                    params={"TrustServerCertificate": "yes"},
                ),
                **kwargs,
            )
        )

    @staticmethod
    def clean_run_storage(conn_string):
        check.invariant(
            TestMSSQLInstance.dagster_mssql_installed(),
            "dagster_mssql must be installed to test with mssql",
        )
        from dagster_mssql.run_storage import MSSQLRunStorage

        storage = MSSQLRunStorage.create_clean_storage(conn_string)
        assert storage
        return storage

    @staticmethod
    def clean_event_log_storage(conn_string):
        check.invariant(
            TestMSSQLInstance.dagster_mssql_installed(),
            "dagster_mssql must be installed to test with mssql",
        )
        from dagster_mssql.event_log import MSSQLEventLogStorage

        storage = MSSQLEventLogStorage.create_clean_storage(conn_string)
        assert storage
        return storage

    @staticmethod
    def clean_schedule_storage(conn_string):
        check.invariant(
            TestMSSQLInstance.dagster_mssql_installed(),
            "dagster_mssql must be installed to test with mssql",
        )
        from dagster_mssql.schedule_storage.schedule_storage import MSSQLScheduleStorage

        storage = MSSQLScheduleStorage.create_clean_storage(conn_string)
        assert storage
        return storage

    @staticmethod
    def create_test_database(conn_string):
        """Create the test database if it does not exist yet.

        Unlike the MySQL and Postgres images, the SQL Server image has no environment
        variable that creates a database at startup -- a fresh container only has the
        system databases -- so the test database has to be created explicitly.

        Deliberately left on the server's default (non-UTF-8) collation: dagster's text
        columns are NVARCHAR on SQL Server precisely so that storage does not depend on
        the collation, and testing under the default is what keeps that honest.
        """
        import sqlalchemy as db

        master_conn_string = conn_string.replace(f"/{TEST_MSSQL_DB_NAME}?", "/master?")
        engine = db.create_engine(master_conn_string, isolation_level="AUTOCOMMIT")
        try:
            with engine.connect() as conn:
                conn.execute(
                    db.text(
                        f"IF DB_ID('{TEST_MSSQL_DB_NAME}') IS NULL "
                        f"CREATE DATABASE {TEST_MSSQL_DB_NAME}"
                    )
                )
                # READ COMMITTED SNAPSHOT gives the row-versioned reads Postgres has by
                # default. Without it SQL Server takes shared read locks and dagster's
                # daemons block the webserver under any real concurrency.
                conn.execute(
                    db.text(
                        f"ALTER DATABASE {TEST_MSSQL_DB_NAME} SET READ_COMMITTED_SNAPSHOT ON "
                        "WITH ROLLBACK IMMEDIATE"
                    )
                )
        finally:
            engine.dispose()

    @staticmethod
    @contextmanager
    def docker_service_up(docker_compose_file, service_name, conn_args=None):
        check.invariant(
            TestMSSQLInstance.dagster_mssql_installed(),
            "dagster_mssql must be installed to test with mssql",
        )
        check.str_param(service_name, "service_name")
        check.str_param(docker_compose_file, "docker_compose_file")
        check.invariant(
            os.path.isfile(docker_compose_file), "docker_compose_file must specify a valid file"
        )
        conn_args = check.opt_dict_param(conn_args, "conn_args") if conn_args else {}

        from dagster_mssql.utils import wait_for_connection

        if BUILDKITE:
            # buildkite docker is handled in pipeline setup
            conn_str = TestMSSQLInstance.conn_string(**conn_args)
            TestMSSQLInstance.create_test_database(conn_str)
            yield conn_str
            return

        try:
            subprocess.check_output(
                ["docker", "compose", "-f", docker_compose_file, "stop", service_name]
            )
            subprocess.check_output(
                ["docker", "compose", "-f", docker_compose_file, "rm", "-f", service_name]
            )
        except subprocess.CalledProcessError:
            pass

        try:
            subprocess.check_output(
                ["docker", "compose", "-f", docker_compose_file, "up", "-d", service_name],
                stderr=subprocess.STDOUT,  # capture STDERR for error handling
            )
        except subprocess.CalledProcessError as ex:
            err_text = ex.output.decode()
            raise MSSQLDockerError(
                f"Failed to launch docker container(s) via docker compose: {err_text}",
                ex,
            ) from ex

        conn_str = TestMSSQLInstance.conn_string(**conn_args)
        # The server accepts connections to `master` well before the test database exists,
        # so wait on that and only then create the database the tests actually use.
        master_conn_str = conn_str.replace(f"/{TEST_MSSQL_DB_NAME}?", "/master?")
        wait_for_connection(master_conn_str, retry_limit=20, retry_wait=3)
        TestMSSQLInstance.create_test_database(conn_str)
        yield conn_str

        try:
            subprocess.check_output(
                ["docker", "compose", "-f", docker_compose_file, "stop", service_name]
            )
            subprocess.check_output(
                ["docker", "compose", "-f", docker_compose_file, "rm", "-f", service_name]
            )
        except subprocess.CalledProcessError:
            pass

    @staticmethod
    @contextmanager
    def docker_service_up_or_skip(docker_compose_file, service_name, conn_args=None):
        with TestMSSQLInstance.docker_service_up(
            docker_compose_file, service_name, conn_args
        ) as conn_str:
            yield conn_str


def is_mssql_running(service_name):
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
        lines = ex.output.decode().split("\n")
        if len(lines) == 2 and "Cannot connect to the Docker daemon" in lines[0]:
            raise MSSQLDockerError("Cannot connect to the Docker daemon", ex) from ex
        else:
            raise MSSQLDockerError(
                "Could not verify mssql container was running as expected", ex
            ) from ex

    decoded = output.decode()
    lines = decoded.split("\n")

    # header, one line for container, trailing \n
    # if container is found, service_name should appear at the end of the second line of output
    return len(lines) == 3 and lines[1].endswith(service_name)


class MSSQLDockerError(Exception):
    def __init__(self, message, subprocess_error):
        super().__init__(check.opt_str_param(message, "message"))
        self.subprocess_error = check.inst_param(
            subprocess_error, "subprocess_error", subprocess.CalledProcessError
        )
