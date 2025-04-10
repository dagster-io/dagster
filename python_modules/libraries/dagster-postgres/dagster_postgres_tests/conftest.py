import pytest
from dagster_postgres.test_fixtures import postgres_conn_str, postgres_hostname  # noqa: F401


@pytest.fixture
def hostname(postgres_hostname):  # noqa: F811
    yield postgres_hostname


@pytest.fixture
def conn_string(postgres_conn_str):  # noqa: F811
    yield postgres_conn_str
