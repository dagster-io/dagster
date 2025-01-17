import os
import shutil
import signal
import subprocess
import time
import uuid
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from subprocess import CompletedProcess
from tempfile import TemporaryDirectory
from typing import Any, Callable

import pytest
import requests
from azure.identity import ClientSecretCredential
from azure.storage.blob import ContainerClient
from dagster._core.test_utils import environ
from dagster._time import get_current_timestamp
from dagster._utils import process_is_alive
from dagster_azure.blob.utils import create_blob_client

AZURE_CLI_IMAGE = "mcr.microsoft.com/azure-cli:latest"


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
    container_client = get_container_client(get_credentials())
    for blob in container_client.list_blobs(name_starts_with=prefix):
        container_client.delete_blob(blob.name)


REQUIRES_ENV_CREDENTIALS = ["default-credential.yaml", "default-capture-behavior.yaml"]


@pytest.fixture(name="dagster_yaml")
def dagster_yaml_path(request) -> Generator[Path, None, None]:
    additional_env_vars = {}
    if request.param in REQUIRES_ENV_CREDENTIALS:
        additional_env_vars = {
            "AZURE_CLIENT_ID": os.environ["TEST_AZURE_CLIENT_ID"],
            "AZURE_CLIENT_SECRET": os.environ["TEST_AZURE_CLIENT_SECRET"],
            "AZURE_TENANT_ID": os.environ["TEST_AZURE_TENANT_ID"],
        }
    with environ(additional_env_vars):
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
        with environ({"TEST_AZURE_LOG_PREFIX": prefix}):
            yield prefix
    finally:
        delete_blobs_with_prefix(prefix)


@pytest.fixture(name="dagster_dev")
def setup_dagster(dagster_home: str, prefix_env: str) -> Generator[Any, None, None]:
    with stand_up_dagster(["dagster", "dev", "-m", "azure_test_proj.defs"]) as process:
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


def get_credentials() -> ClientSecretCredential:
    return ClientSecretCredential(
        tenant_id=os.environ["TEST_AZURE_TENANT_ID"],
        client_id=os.environ["TEST_AZURE_CLIENT_ID"],
        client_secret=os.environ["TEST_AZURE_CLIENT_SECRET"],
    )


def get_container_client(credentials: ClientSecretCredential) -> ContainerClient:
    return create_blob_client(
        storage_account="chriscomplogmngr",
        credential=credentials,
    ).get_container_client("mycontainer")


@pytest.fixture(name="credentials")
def setup_credentials() -> Generator[ClientSecretCredential, None, None]:
    yield get_credentials()


@pytest.fixture(name="container_client")
def setup_container_client() -> Generator[ContainerClient, None, None]:
    yield get_container_client(get_credentials())


@pytest.fixture(name="azure_tmp_dir")
def setup_azure_tmp_dir() -> Generator[Path, None, None]:
    with TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture(name="call_azure_cli")
def setup_azure_env_file(
    azure_tmp_dir: Path,
) -> Generator[Callable[[list[str]], CompletedProcess[str]], None, None]:
    additional_env_vars = {
        "AZURE_CLIENT_ID": os.environ["TEST_AZURE_CLIENT_ID"],
        "AZURE_CLIENT_SECRET": os.environ["TEST_AZURE_CLIENT_SECRET"],
        "AZURE_TENANT_ID": os.environ["TEST_AZURE_TENANT_ID"],
    }
    # this creates a file and writes the additional env vars to it
    file_path = Path(azure_tmp_dir) / "env_vars"
    with open(file_path, "w") as f:
        for key, value in additional_env_vars.items():
            f.write(f"{key}={value}\n")

    subprocess.run(
        [
            "docker",
            "run",
            "--rm",
            "--env-file",
            file_path,
            "-v",
            f"{azure_tmp_dir}/.azure:/root/.azure",
            AZURE_CLI_IMAGE,
            "/bin/bash",
            "-c",
            "az login --service-principal -u $AZURE_CLIENT_ID -p $AZURE_CLIENT_SECRET --tenant $AZURE_TENANT_ID",
        ],
        check=True,
    )

    def invoke_cli(args: list[str]) -> CompletedProcess[str]:
        assert os.path.exists(f"{azure_tmp_dir}/.azure"), "Azure CLI login information not found."

        docker_args = [
            "docker",
            "run",
            "--rm",
            "-v",
            f"{azure_tmp_dir}/.azure:/root/.azure",
            AZURE_CLI_IMAGE,
        ]
        return subprocess.run(
            [*docker_args, *args],
            capture_output=True,
            text=True,
            check=True,
        )

    yield invoke_cli
