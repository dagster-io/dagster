import os
import subprocess
from pathlib import Path
from typing import Generator

import pytest
from azure.identity import ClientSecretCredential
from azure.storage.blob import BlobClient, ContainerClient
from dagster import (
    DagsterEventType,
    DagsterInstance,
    EventRecordsFilter,
    _check as check,
)
from dagster_azure.blob.utils import create_blob_client


@pytest.fixture
def credentials() -> ClientSecretCredential:
    return ClientSecretCredential(
        tenant_id=os.environ["TEST_AZURE_TENANT_ID"],
        client_id=os.environ["TEST_AZURE_CLIENT_ID"],
        client_secret=os.environ["TEST_AZURE_CLIENT_SECRET"],
    )


@pytest.fixture
def container_client(credentials: ClientSecretCredential) -> Generator[ContainerClient, None, None]:
    yield create_blob_client(
        storage_account="chriscomplogmngr",
        credential=credentials,
    ).get_container_client("mycontainer")


@pytest.mark.parametrize(
    "dagster_yaml",
    ["secret-credential.yaml", "default-credential.yaml", "access-key-credential.yaml"],
    indirect=True,
)
def test_compute_log_manager(
    dagster_dev: subprocess.Popen,
    container_client: ContainerClient,
    prefix_env: str,
    credentials: ClientSecretCredential,
    dagster_yaml: Path,
) -> None:
    subprocess.run(
        ["dagster", "asset", "materialize", "--select", "my_asset", "-m", "azure_test_proj.defs"],
        check=True,
    )
    logs_captured_data = check.not_none(
        DagsterInstance.get()
        .get_event_records(
            EventRecordsFilter(
                event_type=DagsterEventType.LOGS_CAPTURED,
            )
        )[0]
        .event_log_entry.dagster_event
    ).logs_captured_data

    assert logs_captured_data.external_stderr_url
    assert logs_captured_data.external_stdout_url

    stderr = (
        BlobClient.from_blob_url(logs_captured_data.external_stderr_url, credential=credentials)
        .download_blob()
        .readall()
        .decode()
    )

    stdout = (
        BlobClient.from_blob_url(logs_captured_data.external_stdout_url, credential=credentials)
        .download_blob()
        .readall()
        .decode()
    )

    assert stdout.count("Printing without context") == 10
    assert stderr.count("Logging using context") == 10
