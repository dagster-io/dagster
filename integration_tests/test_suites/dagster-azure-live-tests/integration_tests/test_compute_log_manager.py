import subprocess
from pathlib import Path
from typing import Callable

import pytest
from azure.identity import ClientSecretCredential
from azure.storage.blob import BlobClient, ContainerClient
from dagster import (
    DagsterEventType,
    DagsterInstance,
    EventRecordsFilter,
    _check as check,
)
from dagster._core.event_api import EventLogRecord
from dagster._core.events import ComputeLogsCaptureData

YAMLS_NOT_CAPTURED = ["default-capture-behavior.yaml"]


@pytest.mark.parametrize(
    "dagster_yaml",
    [
        "secret-credential.yaml",
        "default-credential.yaml",
        "access-key-credential.yaml",
        "default-capture-behavior.yaml",
    ],
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
    logs_captured_record = DagsterInstance.get().get_event_records(
        EventRecordsFilter(
            event_type=DagsterEventType.LOGS_CAPTURED,
        )
    )[0]

    stdout, stderr = (
        get_captured_logs_from_urls(
            logs_captured_record,
            credentials,
        )
        if dagster_yaml.name not in YAMLS_NOT_CAPTURED
        else get_captured_logs_from_run(
            logs_captured_record,
            prefix_env,
            container_client,
        )
    )

    assert stdout.count("Printing without context") == 10
    assert stderr.count("Logging using context") == 10


@pytest.mark.parametrize(
    "dagster_yaml",
    [
        "secret-credential.yaml",
    ],
    indirect=True,
)
def test_compute_log_manager_shell_cmd(
    dagster_dev: subprocess.Popen,
    container_client: ContainerClient,
    prefix_env: str,
    credentials: ClientSecretCredential,
    dagster_yaml: Path,
    call_azure_cli: Callable[[list[str]], subprocess.CompletedProcess[str]],
) -> None:
    subprocess.run(
        ["dagster", "asset", "materialize", "--select", "my_asset", "-m", "azure_test_proj.defs"],
        check=True,
    )
    logs_captured_record = DagsterInstance.get().get_event_records(
        EventRecordsFilter(
            event_type=DagsterEventType.LOGS_CAPTURED,
        )
    )[0]

    logs_captured_data = get_logs_captured_data(logs_captured_record)
    (stdout_filename, stderr_filename) = get_filenames_from_log_data(logs_captured_data)
    assert (
        logs_captured_data.shell_cmd
        and logs_captured_data.shell_cmd.stdout
        and logs_captured_data.shell_cmd.stderr
    )
    assert logs_captured_data.shell_cmd.stdout.endswith(stdout_filename)
    assert logs_captured_data.shell_cmd.stderr.endswith(stderr_filename)

    stdout_result = call_azure_cli(logs_captured_data.shell_cmd.stdout.split())
    assert stdout_result.stdout.count("Printing without context") == 10

    stderr_result = call_azure_cli(logs_captured_data.shell_cmd.stderr.split())
    assert stderr_result.stdout.count("Logging using context") == 10


def get_logs_captured_data(log_record: EventLogRecord) -> ComputeLogsCaptureData:
    return check.not_none(log_record.event_log_entry.dagster_event).logs_captured_data


def get_filenames_from_log_data(logs_captured_data: ComputeLogsCaptureData) -> tuple[str, str]:
    assert logs_captured_data.external_stdout_url is not None
    assert logs_captured_data.external_stderr_url is not None

    return (
        logs_captured_data.external_stdout_url.split("/")[-1],
        logs_captured_data.external_stderr_url.split("/")[-1],
    )


def get_captured_logs_from_urls(
    captured_logs_event: EventLogRecord, credentials: ClientSecretCredential
) -> tuple[str, str]:
    logs_captured_data = get_logs_captured_data(captured_logs_event)

    assert logs_captured_data.external_stderr_url is not None
    assert logs_captured_data.external_stdout_url is not None

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
    return stdout, stderr


def get_captured_logs_from_run(
    captured_logs_event: EventLogRecord, prefix_env: str, container_client: ContainerClient
) -> tuple[str, str]:
    run_id = captured_logs_event.run_id
    expected_log_folder = f"{prefix_env}/storage/{run_id}/compute_logs"
    # list all blobs coming from this log folder
    blob_list = list(container_client.list_blobs(name_starts_with=expected_log_folder))
    assert len(blob_list) == 2
    stdout = next(iter([blob for blob in blob_list if "out" in blob.name]))
    stderr = next(iter([blob for blob in blob_list if "err" in blob.name]))
    # get blob for each log
    stdout_blob = container_client.get_blob_client(stdout.name)
    stderr_blob = container_client.get_blob_client(stderr.name)
    # download content
    stdout_content = stdout_blob.download_blob().readall().decode()
    stderr_content = stderr_blob.download_blob().readall().decode()
    return stdout_content, stderr_content
