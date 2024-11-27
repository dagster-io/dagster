import os
import subprocess
from typing import Generator

import pytest
from azure.identity import ClientSecretCredential
from azure.storage.blob import ContainerClient
from dagster_azure.blob.utils import create_blob_client


@pytest.fixture
def container_client() -> Generator[ContainerClient, None, None]:
    yield create_blob_client(
        storage_account="chriscomplogmngr",
        credential=ClientSecretCredential(
            tenant_id=os.environ["TEST_AZURE_TENANT_ID"],
            client_id=os.environ["TEST_AZURE_CLIENT_ID"],
            client_secret=os.environ["TEST_AZURE_CLIENT_SECRET"],
        ),
    ).get_container_client("mycontainer")


def test_compute_log_manager(
    dagster_dev: subprocess.Popen, container_client: ContainerClient, prefix_env: str
) -> None:
    subprocess.run(
        ["dagster", "asset", "materialize", "--select", "my_asset", "-m", "azure_test_proj.defs"],
        check=True,
    )
    blobs = list(container_client.list_blobs(name_starts_with=f"{prefix_env}/storage"))
    assert len(blobs) == 2
    assert len([blob for blob in blobs if blob.name.endswith(".err")]) == 1
    assert len([blob for blob in blobs if blob.name.endswith(".out")]) == 1
    stdout = container_client.download_blob(blob=blobs[0].name).readall().decode()
    stderr = container_client.download_blob(blob=blobs[1].name).readall().decode()
    assert stdout.count("Logging using context") == 10
    assert stderr.count("Printing without context") == 10
