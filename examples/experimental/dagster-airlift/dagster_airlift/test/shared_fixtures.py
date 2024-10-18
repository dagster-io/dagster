import os
import signal
import subprocess
import time
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Callable, Generator, List, Optional

import pytest
import requests
from dagster._core.test_utils import environ
from dagster._time import get_current_timestamp


####################################################################################################
# AIRFLOW SETUP FIXTURES
# Sets up the airflow environment for testing. Running at localhost:8080.
# Callsites are expected to provide implementations for dags_dir fixture.
####################################################################################################
def _airflow_is_ready() -> bool:
    try:
        response = requests.get("http://localhost:8080")
        return response.status_code == 200
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
    subprocess.run([path_to_script, dags_dir], check=True, env=temp_env)
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
    airflow_cmd: List[str] = ["airflow", "standalone"],
    cwd: Optional[Path] = None,
    stdout_channel: Optional[int] = None,
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
            if _airflow_is_ready():
                airflow_ready = True
                break
            time.sleep(1)

        assert airflow_ready, "Airflow did not start within 30 seconds..."
        yield process
    finally:
        # Kill process group, since process.kill and process.terminate do not work.
        os.killpg(process.pid, signal.SIGKILL)


@pytest.fixture(name="airflow_instance")
def airflow_instance_fixture(setup: None) -> Generator[subprocess.Popen, None, None]:
    with stand_up_airflow(env=os.environ) as process:
        yield process


####################################################################################################
# DAGSTER SETUP FIXTURES
# Sets up the dagster environment for testing. Running at localhost:3333.
# Callsites are expected to provide implementations for dagster_defs_path fixture.
####################################################################################################
def _dagster_is_ready() -> bool:
    try:
        response = requests.get("http://localhost:3333")
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
def dagster_dev_cmd(dagster_defs_path: str) -> List[str]:
    """Return the command used to stand up dagster dev."""
    return ["dagster", "dev", "-f", dagster_defs_path, "-p", "3333"]


@pytest.fixture(name="dagster_dev")
def setup_dagster(dagster_home: str, dagster_dev_cmd: List[str]) -> Generator[Any, None, None]:
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
            if _dagster_is_ready():
                dagster_ready = True
                break
            time.sleep(1)

        assert dagster_ready, "Dagster did not start within 30 seconds..."
        yield process
    finally:
        os.killpg(process.pid, signal.SIGKILL)


####################################################################################################
# MISCELLANEOUS FIXTURES
# Fixtures that are useful across contexts.
####################################################################################################
