import pytest


@pytest.fixture(scope="session")
def storage_account():
    yield "dagsterdatabrickstests"


@pytest.fixture(scope="session")
def container():
    yield "dagster-databricks-tests"


@pytest.fixture(scope="session")
def credential():
    yield "super-secret-creds"
