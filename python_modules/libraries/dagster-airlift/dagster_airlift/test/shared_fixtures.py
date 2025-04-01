import os
import signal
import subprocess
import sys
import time
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Callable, Optional

import psutil
import pytest
import requests
from dagster._core.test_utils import environ
from dagster._time import get_current_timestamp
from dagster._utils import process_is_alive

from dagster_airlift.core.airflow_instance import AirflowInstance
from dagster_airlift.core.basic_auth import AirflowBasicAuthBackend


####################################################################################################
# AIRFLOW SETUP FIXTURES
# Sets up the airflow environment for testing. Running at localhost:8080.
# Callsites are expected to provide implementations for dags_dir fixture.
####################################################################################################
def _airflow_is_ready(port) -> bool:
    try:
        af_instance = AirflowInstance(
            auth_backend=AirflowBasicAuthBackend(
                webserver_url=f"http://localhost:{port}",
                username="admin",
                password="admin",
            ),
            name="test",
        )
        return len(af_instance.list_dags()) > 0
    except:
        return False


@pytest.fixture(name="airflow_home")
def default_airflow_home() -> Generator[str, None, None]:
    with TemporaryDirectory() as tmpdir:
        with environ({"AIRFLOW_HOME": tmpdir}):
            yield tmpdir


@pytest.fixture(name="setup")
def setup_fixture(airflow_home: Path, dags_dir: Path) -> Generator[Path, None, None]:
    assert os.environ["AIRFLOW_HOME"] == str(airflow_home), "AIRFLOW_HOME is not set correctly"
    temp_env = {
        **os.environ.copy(),
        # Provide link to local dagster installation.
        "DAGSTER_URL": "http://localhost:3333",
    }
    path_to_script = Path(__file__).parent.parent.parent / "scripts" / "airflow_setup.sh"
    subprocess.run(["chmod", "+x", path_to_script], check=True, env=temp_env)
    subprocess.run([path_to_script, dags_dir, airflow_home], check=True, env=temp_env)
    with environ(temp_env):
        yield airflow_home


@pytest.fixture(name="reserialize_dags")
def reserialize_fixture(airflow_instance: None) -> Callable[[], None]:
    """Forces airflow to reserialize dags, to ensure that the latest changes are picked up."""

    def _reserialize_dags() -> None:
        subprocess.check_output(["airflow", "dags", "reserialize"])

    return _reserialize_dags


@contextmanager
def stand_up_airflow(
    env: Any = {},
    airflow_cmd: list[str] = ["airflow", "standalone"],
    cwd: Optional[Path] = None,
    stdout_channel: Optional[int] = None,
    port: int = 8080,
) -> Generator[subprocess.Popen, None, None]:
    process = subprocess.Popen(
        airflow_cmd,
        cwd=cwd,
        env=env,  # since we have some temp vars in the env right now
        shell=False,
        preexec_fn=os.setsid,  # noqa  # fuck it we ball
        stdout=stdout_channel,
    )
    try:
        # Give airflow a second to stand up
        time.sleep(5)
        initial_time = get_current_timestamp()

        airflow_ready = False
        while get_current_timestamp() - initial_time < 60:
            if _airflow_is_ready(port):
                airflow_ready = True
                break
            time.sleep(1)

        assert airflow_ready, "Airflow did not start within 30 seconds..."
        yield process
    finally:
        if process_is_alive(process.pid):
            # Kill process group, since process.kill and process.terminate do not work.
            os.killpg(process.pid, signal.SIGKILL)
            process.wait(5)


@pytest.fixture(name="airflow_instance")
def airflow_instance_fixture(setup: None) -> Generator[subprocess.Popen, None, None]:
    with stand_up_airflow(env=os.environ) as process:
        yield process


####################################################################################################
# DAGSTER SETUP FIXTURES
# Sets up the dagster environment for testing. Running at localhost:3333.
# Callsites are expected to provide implementations for dagster_defs_path fixture.
####################################################################################################
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
        with environ({"DAGSTER_HOME": tmpdir}):
            yield tmpdir


@pytest.fixture(name="dagster_dev_cmd")
def dagster_dev_cmd(dagster_defs_path: str) -> list[str]:
    """Return the command used to stand up dagster dev."""
    return ["dagster", "dev", "-f", dagster_defs_path, "-p", "3333"]


@pytest.fixture(name="dagster_dev")
def setup_dagster(
    airflow_instance: None, dagster_home: str, dagster_dev_cmd: list[str]
) -> Generator[Any, None, None]:
    # The version of airflow we use on 3.12 or greater (2.10.2) takes longer to reconcile the dags, and sometimes does it partially.
    # We need to wait for all the dags to be loaded before we can start dagster.
    # A better solution would be to poll the airflow instance for the existence of all expected dags, but this is a stopgap.
    if sys.version_info >= (3, 12):
        time.sleep(20)
    with stand_up_dagster(dagster_dev_cmd) as process:
        yield process
    time.sleep(5)


@contextmanager
def stand_up_dagster(
    dagster_dev_cmd: list[str], port: int = 3333
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
        # Give dagster a second to stand up
        time.sleep(5)

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
        if psutil.Process(pid=process.pid).is_running():
            # Kill process group, since process.kill and process.terminate do not work.
            os.killpg(process.pid, signal.SIGKILL)


####################################################################################################
# MISCELLANEOUS FIXTURES
# Fixtures that are useful across contexts.
####################################################################################################
