import subprocess
from collections.abc import Mapping
from pathlib import Path

import pytest
from dagster import (
    DagsterEventType,
    DagsterInstance,
    EventRecordsFilter,
    _check as check,
)
from google.cloud import storage as gcs

from .conftest import get_bucket_client, get_credentials  # noqa: TID252


@pytest.mark.parametrize(
    "dagster_yaml",
    ["json-credentials.yaml"],
    indirect=True,
)
def test_compute_log_manager(
    dagster_dev: subprocess.Popen,
    bucket_client: gcs.Bucket,
    prefix_env: str,
    credentials: Mapping,
    dagster_yaml: Path,
) -> None:
    subprocess.run(
        ["dagster", "asset", "materialize", "--select", "my_asset", "-m", "gcp_test_proj.defs"],
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
    stderr = get_content_from_url(logs_captured_data.external_stderr_url)
    stdout = get_content_from_url(logs_captured_data.external_stdout_url)
    assert stdout.count("Printing without context") == 10
    assert stderr.count("Logging using context") == 10


def _parse_gcs_url_into_uri(url: str) -> str:
    return url.removeprefix(
        "https://console.cloud.google.com/storage/browser/_details/computelogmanager-tests/"
    )


def get_content_from_url(url: str) -> str:
    uri = _parse_gcs_url_into_uri(url)
    client = get_bucket_client(get_credentials())
    blob = client.blob(uri)
    return blob.download_as_string().decode()
