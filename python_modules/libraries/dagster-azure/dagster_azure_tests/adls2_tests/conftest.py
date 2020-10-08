import os

import pytest


@pytest.fixture(scope="session")
def storage_account():
    yield "elementldevstorage"


@pytest.fixture(scope="session")
def file_system():
    yield "dagster-azure-tests"


@pytest.fixture(scope="session")
def credential():
    yield os.environ.get("AZURE_STORAGE_ACCOUNT_KEY")
