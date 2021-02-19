import pytest
from dagster.utils import file_relative_path
from dagster.utils.test.mysql_instance import TestMySQLInstance


@pytest.fixture(scope="function")
def hostname(conn_string):  # pylint: disable=redefined-outer-name, unused-argument
    return TestMySQLInstance.get_hostname()


@pytest.fixture(scope="function")
def conn_string():  # pylint: disable=redefined-outer-name, unused-argument
    with TestMySQLInstance.docker_service_up_or_skip(
        file_relative_path(__file__, "docker-compose.yml"), "test-mysql-db"
    ) as conn_str:
        yield conn_str
