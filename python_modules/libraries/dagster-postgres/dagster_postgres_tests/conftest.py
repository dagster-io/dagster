import pytest

pytest_plugins = ["dagster_test.fixtures"]


@pytest.fixture
def hostname(postgres_hostname):
    yield postgres_hostname


@pytest.fixture
def conn_string(postgres_conn_str):
    yield postgres_conn_str
