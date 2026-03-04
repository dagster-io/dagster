import os

import pytest
from dagster._core.test_utils import environ


@pytest.fixture(scope="session")
def storage_account():
    yield "dagsterdev"


@pytest.fixture(scope="session")
def file_system():
    yield "dagster-azure-tests"


@pytest.fixture(scope="session")
def credential():
    key = os.environ.get("AZURE_STORAGE_ACCOUNT_KEY")
    if key is None:
        with environ({"AZURE_STORAGE_ACCOUNT_KEY": "dummy-key-for-testing"}):
            yield os.environ["AZURE_STORAGE_ACCOUNT_KEY"]
    else:
        yield key
