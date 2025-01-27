import json
import os
import shutil
import signal
import subprocess
import time
import uuid
from collections.abc import Generator, Mapping
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

import pytest
import requests
from dagster._core.test_utils import environ
from dagster._time import get_current_timestamp
from dagster._utils import process_is_alive
from google.cloud import storage as gcs


def integration_test_dir() -> Path:
    return Path(__file__).parent.parent


def _dagster_is_ready(port: int) -> bool:
    try:
        response = requests.get(f"http://localhost:{port}")
        return response.status_code == 200
    except:
        return False


def path_to_dagster_yamls() -> Path:
    return Path(__file__).parent / "dagster-yamls"


def delete_blobs_with_prefix(prefix: str) -> None:
    bucket_client = get_bucket_client(get_credentials())
    for blob in bucket_client.list_blobs(prefix=prefix):
        bucket_client.delete_blob(blob.name)


@pytest.fixture(name="dagster_yaml")
def dagster_yaml_path(request) -> Generator[Path, None, None]:
    yield path_to_dagster_yamls() / request.param


@pytest.fixture(name="dagster_home")
def setup_dagster_home(dagster_yaml: Path) -> Generator[str, None, None]:
    """Instantiate a temporary directory to serve as the DAGSTER_HOME."""
    with TemporaryDirectory() as tmpdir:
        # Copy over dagster.yaml
        shutil.copy2(dagster_yaml, Path(tmpdir) / "dagster.yaml")
        with environ({"DAGSTER_HOME": tmpdir}):
            yield tmpdir


@pytest.fixture
def prefix_env() -> Generator[str, None, None]:
    prefix = f"prefix_{uuid.uuid4().hex}"
    try:
        with environ({"TEST_GCP_LOG_PREFIX": prefix}):
            yield prefix
    finally:
        delete_blobs_with_prefix(prefix)


@pytest.fixture(name="dagster_dev")
def setup_dagster(dagster_home: str, prefix_env: str) -> Generator[Any, None, None]:
    with stand_up_dagster(["dagster", "dev", "-m", "gcp_test_proj.defs"]) as process:
        yield process


@contextmanager
def stand_up_dagster(
    dagster_dev_cmd: list[str], port: int = 3000
) -> Generator[subprocess.Popen, None, None]:
    """Stands up a dagster instance using the dagster dev CLI. dagster_defs_path must be provided
    by a fixture included in the callsite.
    """
    process = subprocess.Popen(
        dagster_dev_cmd,
        env=os.environ.copy(),
        shell=False,
        preexec_fn=os.setsid,  # noqa
    )
    try:
        dagster_ready = False
        initial_time = get_current_timestamp()
        while get_current_timestamp() - initial_time < 60:
            if _dagster_is_ready(port):
                dagster_ready = True
                break
            time.sleep(1)

        assert dagster_ready, "Dagster did not start within 30 seconds..."
        yield process
    finally:
        if process_is_alive(process.pid):
            os.killpg(process.pid, signal.SIGKILL)


def get_credentials() -> Mapping:
    return json.loads(os.environ["GCP_LIVE_TEST_CREDENTIALS"])


def get_bucket_client(credentials: Mapping) -> gcs.Bucket:
    return gcs.Client.from_service_account_info(credentials).get_bucket("computelogmanager-tests")


@pytest.fixture(name="credentials")
def setup_credentials() -> Generator[Mapping, None, None]:
    yield get_credentials()


@pytest.fixture(name="bucket_client")
def setup_container_client() -> Generator[gcs.Bucket, None, None]:
    yield get_bucket_client(get_credentials())
