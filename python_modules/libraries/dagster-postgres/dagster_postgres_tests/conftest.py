import pytest
from dagster_postgres.test_fixtures import (  # noqa: F401 #pyright:ignore reportMissingImports
    postgres_conn_str,
    postgres_hostname,
)


@pytest.fixture
def hostname(postgres_hostname):  # noqa: F811
    yield postgres_hostname


@pytest.fixture
def conn_string(postgres_conn_str):  # noqa: F811
    yield postgres_conn_str
