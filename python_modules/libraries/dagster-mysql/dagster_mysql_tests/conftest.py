from urllib.parse import urlparse

import pytest
from dagster._utils import file_relative_path
from dagster._utils.test.mysql_instance import TestMySQLInstance


@pytest.fixture(scope="session")
def hostname(conn_string):
    parse_result = urlparse(conn_string)
    return parse_result.hostname


@pytest.fixture(
    scope="session", params=[("test-mysql-db", {}), ("test-mysql-db-pinned", {"port": 3307})]
)
def conn_string(request):
    service, conn_args = request.param
    with TestMySQLInstance.docker_service_up_or_skip(
        file_relative_path(__file__, "docker-compose.yml"), service, conn_args
    ) as conn_str:
        yield conn_str


@pytest.fixture(
    scope="session",
    params=[("test-mysql-db", {}), ("test-mysql-db-pinned-backcompat", {"port": 3308})],
)
def backcompat_conn_string(request):
    service, conn_args = request.param
    with TestMySQLInstance.docker_service_up_or_skip(
        file_relative_path(__file__, "docker-compose.yml"), service, conn_args
    ) as conn_str:
        yield conn_str
