import signal
import subprocess
import time

import boto3
import pytest
from azure.core.exceptions import ResourceExistsError
from azure.storage import blob
from obstore.store import AzureStore


# Make sure unit tests never connect to real AWS
@pytest.fixture(autouse=True)
def fake_aws_credentials(monkeypatch):
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "test")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "test")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")
    monkeypatch.setenv("AWS_ENDPOINT", "http://127.0.0.1:3000")


@pytest.fixture(autouse=True)
def azurite_credentials(monkeypatch):
    account_name = "devstoreaccount1"
    azure_storage_account_key = (
        "Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw=="
    )
    monkeypatch.setenv("AZURE_STORAGE_USE_EMULATOR", "true")
    monkeypatch.setenv("AZURE_STORAGE_CONTAINER_NAME", "dagster")
    monkeypatch.setenv("AZURE_STORAGE_ACCOUNT_KEY", azure_storage_account_key)
    monkeypatch.setenv("AZURITE_BLOB_STORAGE_URL", "http://localhost:10000")
    monkeypatch.setenv("AZURE_STORAGE_ENDPOINT", "http://localhost:10000")
    monkeypatch.setenv("AZURE_STORAGE_ACCOUNT_NAME", account_name)
    monkeypatch.setenv(
        "AZURE_STORAGE_CONNECTION_STRING",
        f"DefaultEndpointsProtocol=http;AccountName={account_name};AccountKey={azure_storage_account_key};BlobEndpoint=http://localhost:10000/{account_name};QueueEndpoint=http://localhost:10001/{account_name};",
    )


@pytest.fixture(scope="module")
def start_azurite_server():
    account_name = "devstoreaccount1"
    azure_storage_account_key = (
        "Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw=="
    )

    docker_process = subprocess.Popen(
        ["docker-compose", "up"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    time.sleep(5)

    container_name = "dagster"
    try:
        blob_client = blob.BlobServiceClient.from_connection_string(
            conn_str=f"DefaultEndpointsProtocol=http;AccountName={account_name};AccountKey={azure_storage_account_key};BlobEndpoint=http://localhost:10000/{account_name};QueueEndpoint=http://localhost:10001/{account_name};"
        )
        blob_client.create_container(name=container_name)
    except ResourceExistsError:
        pass

    yield container_name

    docker_process.send_signal(signal.SIGINT)
    docker_process.wait()


@pytest.fixture
def container() -> str:
    return "dagster"


@pytest.fixture
def storage_account() -> str:
    return "devstoreaccount1"


@pytest.fixture
def azure_store(container) -> AzureStore:
    return AzureStore.from_env(container=container, client_options={"allow_http": True})


@pytest.fixture(scope="module")
def start_moto_server():
    moto_process = subprocess.Popen(
        ["moto_server", "-p3000"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    time.sleep(5)

    yield moto_process

    moto_process.send_signal(signal.SIGINT)
    moto_process.wait()


@pytest.fixture
def mock_s3_resource(start_moto_server):
    return boto3.resource("s3", region_name="us-east-1", endpoint_url="http://127.0.0.1:3000")


@pytest.fixture
def mock_s3_bucket(mock_s3_resource):
    yield mock_s3_resource.create_bucket(Bucket="test-bucket")
