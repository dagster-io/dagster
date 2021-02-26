import pytest
from dagster.utils import file_relative_path
from dagster.utils.test.postgres_instance import TestPostgresInstance


@pytest.fixture(scope="session")
def hostname(conn_string):  # pylint: disable=redefined-outer-name, unused-argument
    return TestPostgresInstance.get_hostname()


@pytest.fixture(scope="session")
def conn_string():  # pylint: disable=redefined-outer-name, unused-argument
    with TestPostgresInstance.docker_service_up_or_skip(
        file_relative_path(__file__, "docker-compose.yml"), "test-postgres-db"
    ) as conn_str:
        yield conn_str
