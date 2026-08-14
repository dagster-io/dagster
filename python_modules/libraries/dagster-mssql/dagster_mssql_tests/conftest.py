import os
from urllib.parse import urlparse

import pytest
from dagster._utils import file_relative_path
from dagster._utils.test.mssql_instance import TestMSSQLInstance

# Which SQL Server the suite runs against, selected by MSSQL_TEST_VERSION. Each entry is
# the compose service, the port it publishes on the host, and the environment variable
# buildkite uses to hand over the container's address. Keep in step with
# docker-compose.yml and the mssql section of .buildkite steps/packages.py.
_SERVICES = {
    "2022": ("test-mssql-db", 1433, "MSSQL_TEST_DB_HOST"),
    "2019": ("test-mssql-db-2019", 1435, "MSSQL_TEST_2019_DB_HOST"),
    "2017": ("test-mssql-db-pinned", 1434, "MSSQL_TEST_PINNED_DB_HOST"),
}

BUILDKITE = bool(os.getenv("BUILDKITE"))


@pytest.fixture(scope="session")
def mssql_version():
    version = os.environ.get("MSSQL_TEST_VERSION", "2022")
    if version not in _SERVICES:
        raise ValueError(f"MSSQL_TEST_VERSION={version!r} is not one of {sorted(_SERVICES)}")
    return version


@pytest.fixture(scope="session")
def hostname(conn_string):
    parse_result = urlparse(conn_string)
    return parse_result.hostname


@pytest.fixture(scope="session")
def conn_string(mssql_version):
    service, host_port, host_env = _SERVICES[mssql_version]

    # In buildkite each container is reachable by address on its own network, so the port
    # is the one SQL Server actually listens on rather than the published one.
    conn_args = (
        {"hostname": os.environ[host_env]}
        if BUILDKITE and host_env in os.environ
        else {"port": host_port}
    )

    with TestMSSQLInstance.docker_service_up_or_skip(
        file_relative_path(__file__, "docker-compose.yml"), service, conn_args=conn_args
    ) as conn_str:
        yield conn_str
