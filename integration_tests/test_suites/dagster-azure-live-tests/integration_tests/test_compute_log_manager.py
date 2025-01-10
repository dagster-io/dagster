import os
import subprocess
from pathlib import Path

import pytest
from azure.identity import ClientSecretCredential
from azure.storage.blob import BlobClient, ContainerClient
from dagster import (
    DagsterEventType,
    DagsterInstance,
    EventRecordsFilter,
    _check as check,
)


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

    assert logs_captured_data.stdout_uri_or_path
    assert logs_captured_data.stderr_uri_or_path
    assert logs_captured_data.external_stdout_url.endswith(logs_captured_data.stdout_uri_or_path)
    assert logs_captured_data.external_stderr_url.endswith(logs_captured_data.stderr_uri_or_path)

    assert logs_captured_data.log_manager_metadata
    metadata = logs_captured_data.log_manager_metadata
    assert metadata.log_manager_class == "AzureBlobComputeLogManager"
    assert metadata.container == os.getenv("TEST_AZURE_CONTAINER_ID")
    assert metadata.storage_account == os.getenv("TEST_AZURE_STORAGE_ACCOUNT_ID")
