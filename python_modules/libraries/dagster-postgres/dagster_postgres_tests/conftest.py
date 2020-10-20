import pytest
from dagster.utils import file_relative_path
from dagster.utils.test.postgres_instance import TestPostgresInstance
from dagster_postgres.run_storage import PostgresRunStorage
from dagster_postgres.schedule_storage.schedule_storage import PostgresScheduleStorage


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
