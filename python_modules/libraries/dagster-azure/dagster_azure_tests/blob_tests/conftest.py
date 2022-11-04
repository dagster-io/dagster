import pytest
from dagster_azure.blob.fake_blob_client import FakeBlobServiceClient


@pytest.fixture(scope="session")
def storage_account():
    yield "dagsterdatabrickstests"


@pytest.fixture(scope="session")
def container():
    yield "dagster-databricks-tests"


@pytest.fixture(scope="session")
def credential():
    yield "super-secret-creds"


@pytest.fixture(scope="session")
def blob_client(storage_account):
    yield FakeBlobServiceClient(storage_account)
