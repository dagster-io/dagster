import os
import shutil
import signal
import subprocess
import time
import uuid
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Generator, List

import pytest
import requests
from dagster._core.test_utils import environ
from dagster._time import get_current_timestamp


def integration_test_dir() -> Path:
    return Path(__file__).parent.parent


def _dagster_is_ready(port: int) -> bool:
    try:
        response = requests.get(f"http://localhost:{port}")
        return response.status_code == 200
    except:
        return False


@pytest.fixture(name="dagster_home")
def setup_dagster_home() -> Generator[str, None, None]:
    """Instantiate a temporary directory to serve as the DAGSTER_HOME."""
    with TemporaryDirectory() as tmpdir:
        # Copy over dagster.yaml
        shutil.copy2(integration_test_dir() / "dagster.yaml", tmpdir)
        with environ({"DAGSTER_HOME": tmpdir}):
            yield tmpdir


@pytest.fixture
def prefix_env() -> Generator[str, None, None]:
    prefix = f"prefix_{uuid.uuid4().hex}"
    with environ({"TEST_AZURE_LOG_PREFIX": prefix}):
        yield prefix


@pytest.fixture(name="dagster_dev")
def setup_dagster(dagster_home: str, prefix_env: str) -> Generator[Any, None, None]:
    with stand_up_dagster(["dagster", "dev", "-m", "azure_test_proj.defs"]) as process:
        yield process


@contextmanager
def stand_up_dagster(
    dagster_dev_cmd: List[str], port: int = 3000
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
        os.killpg(process.pid, signal.SIGKILL)
