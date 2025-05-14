import pytest


@pytest.fixture
def hostname(postgres_hostname):
    yield postgres_hostname


@pytest.fixture
def conn_string(postgres_conn_str):
    yield postgres_conn_str
