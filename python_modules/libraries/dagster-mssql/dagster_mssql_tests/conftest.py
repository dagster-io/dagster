from urllib.parse import urlparse

import pytest
from dagster._utils import file_relative_path
from dagster._utils.test.mssql_instance import TestMSSQLInstance


@pytest.fixture(scope="session")
def hostname(conn_string):
    parse_result = urlparse(conn_string)
    return parse_result.hostname


@pytest.fixture(scope="session")
def conn_string():
    with TestMSSQLInstance.docker_service_up_or_skip(
        file_relative_path(__file__, "docker-compose.yml"), "test-mssql-db"
    ) as conn_str:
        yield conn_str
