import pytest
from dagster_postgres.run_storage import PostgresRunStorage
from dagster_postgres.schedule_storage.schedule_storage import PostgresScheduleStorage

from dagster.utils import file_relative_path
from dagster.utils.test.postgres_instance import TestPostgresInstance


@pytest.fixture(scope="function")
def hostname(conn_string):  # pylint: disable=redefined-outer-name, unused-argument
    return TestPostgresInstance.get_hostname()


@pytest.fixture(scope="function")
def conn_string():  # pylint: disable=redefined-outer-name, unused-argument
    with TestPostgresInstance.docker_service_up_or_skip(
        file_relative_path(__file__, "docker-compose.yml"), "test-postgres-db"
    ) as conn_str:
        yield conn_str


@pytest.fixture(scope="function")
def clean_storage(conn_string):  # pylint: disable=redefined-outer-name
    storage = PostgresRunStorage.create_clean_storage(conn_string)
    assert storage
    return storage


@pytest.fixture(scope="function")
def clean_schedule_storage(conn_string):  # pylint: disable=redefined-outer-name
    storage = PostgresScheduleStorage.create_clean_storage(conn_string)
    assert storage
    return storage


@pytest.fixture(scope="module")
def multi_postgres():  # pylint: disable=redefined-outer-name
    compose_file_path = file_relative_path(__file__, "docker-compose-multi.yml")
    with TestPostgresInstance.docker_service_up_or_skip(
        compose_file_path,
        "test-run-storage-db",
        conn_args={
            "port": 5434,
            "hostname": TestPostgresInstance.get_hostname("POSTGRES_TEST_RUN_STORAGE_DB_HOST"),
        },
    ) as run_storage_conn_string:
        with TestPostgresInstance.docker_service_up_or_skip(
            compose_file_path,
            "test-event-log-storage-db",
            conn_args={
                "port": 5433,
                "hostname": TestPostgresInstance.get_hostname(
                    "POSTGRES_TEST_EVENT_LOG_STORAGE_DB_HOST"
                ),
            },
        ) as event_log_storage_conn_string:
            yield (run_storage_conn_string, event_log_storage_conn_string)
