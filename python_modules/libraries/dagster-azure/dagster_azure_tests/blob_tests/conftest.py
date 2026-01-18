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
    yield {
        "client_id": "11111111-1111-1111-1111-111111111111",
        "client_secret": "fake_client_secret",
        "tenant_id": "22222222-2222-2222-2222-222222222222",
    }


@pytest.fixture(scope="session")
def blob_client(storage_account):
    yield FakeBlobServiceClient(storage_account)
