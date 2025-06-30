import os
import signal
import subprocess
import time
from collections.abc import Generator
from contextlib import contextmanager
from functools import wraps
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Callable, Optional

import psutil
import pytest
import requests
from dagster._core.test_utils import environ
from dagster._time import get_current_timestamp
from dagster._utils import process_is_alive

from dagster_airlift.constants import AirflowVersion, infer_af_version_from_env
from dagster_airlift.core.airflow_instance import AirflowAuthBackend, AirflowInstance
from dagster_airlift.core.basic_auth import AirflowBasicAuthBackend
from dagster_airlift.core.token_backend import AirflowBearerTokenBackend

# Test constants
AIRFLOW_BASE_URL = "http://localhost:8080"
AIRFLOW_INSTANCE_NAME = "my_airflow_instance"

USERNAME = "admin"
PASSWORD = "admin"

DEFAULT_AIRFLOW_PORT = 8080


def is_airflow_2() -> bool:
    return infer_af_version_from_env() == AirflowVersion.AIRFLOW_2


def get_jwt_token() -> str:
    jwt_token = os.getenv("JWT_TOKEN")
    assert jwt_token, "No JWT Token set at JWT_TOKEN."
    return jwt_token


def timed_operation(timeout: int) -> Callable[[Callable[..., bool]], Callable[..., bool]]:
    """Decorator that repeatedly executes the decorated function until it returns True or timeout is reached.

    Args:
        timeout: Maximum time in seconds to keep trying

    Returns:
        Decorator function that wraps the original function
    """

    def decorator(func: Callable[..., bool]) -> Callable[..., bool]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> bool:
            start_time = get_current_timestamp()

            while get_current_timestamp() - start_time < timeout:
                try:
                    result = func(*args, **kwargs)
                    if result:
                        return True
                except Exception:
                    # Continue trying even if the function raises an exception
                    pass

                # Sleep briefly between attempts to avoid overwhelming the system
                time.sleep(0.5)

            # Timeout reached, return False
            return False

        return wrapper

    return decorator


####################################################################################################
# AIRFLOW SETUP FIXTURES
# Sets up the airflow environment for testing. Running at localhost:8080.
# Callsites are expected to provide implementations for dags_dir fixture.
####################################################################################################


def get_backend(port: int = DEFAULT_AIRFLOW_PORT) -> AirflowAuthBackend:
    if is_airflow_2():
        return AirflowBasicAuthBackend(
            webserver_url=f"http://localhost:{port}",
            username="admin",
            password="admin",
        )
    else:
        return AirflowBearerTokenBackend(
            webserver_url=f"http://localhost:{port}", token=get_jwt_token()
        )


@timed_operation(timeout=60)
def _airflow_is_ready(*, port: int, expected_num_dags: int) -> bool:
    try:
        af_instance = AirflowInstance(
            auth_backend=get_backend(port), name="test", airflow_version=infer_af_version_from_env()
        )
        return len(af_instance.list_dags()) >= expected_num_dags
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
    subprocess.run(
        [path_to_script, dags_dir, airflow_home, infer_af_version_from_env().value],
        check=True,
        env=temp_env,
    )
    with environ(temp_env):
        yield airflow_home


@pytest.fixture(name="reserialize_dags")
def reserialize_fixture(airflow_instance: None) -> Callable[[], None]:
    """Forces airflow to reserialize dags, to ensure that the latest changes are picked up."""

    def _reserialize_dags() -> None:
        subprocess.check_output(["airflow", "dags", "reserialize"])

    return _reserialize_dags


@timed_operation(timeout=5)
def _airflow_is_serving(port: int) -> bool:
    """Check that airflow is serving at the given port."""
    try:
        response = requests.get(f"http://localhost:{port}", timeout=60)
        print(f"Airflow is serving at {port}? {response.status_code == 200}")
        return response.status_code == 200
    except:
        return False


@contextmanager
def optionally_stash_jwt_token(port: int) -> None:
    # In Airflow 2, no need to gen a jwt token.
    if is_airflow_2():
        yield
    else:
        print("Attempting to first check if Airflow is running at all")
        import airflow

        print(f"CONFIRMED AIRFLOW VERSION: {airflow.__version__}")
        print("Can connect to Airflow?")
        try:
            print(requests.get("http://localhost:8080", timeout=10))
        except Exception as e:
            print(f"Error connecting to Airflow: {e}")
        print("Can connect to Airflow API v1?")
        try:
            print(requests.get("http://localhost:8080/api/v1/version", timeout=10))
        except Exception as e:
            print(f"Error connecting to Airflow API v1: {e}")
        print("Can connect to Airflow API v2?")
        try:
            print(requests.get("http://localhost:8080/api/v2/version", timeout=10))
        except Exception as e:
            print(f"Error connecting to Airflow API v2: {e}")
        print("--------------------------------")
        # Make a request to Airflow's auth/token endpoint to get a JWT token
        response = requests.get("http://localhost:8080/auth/token", timeout=10)
        response.raise_for_status()
        token_data = response.json()
        jwt_token = token_data["access_token"]
        with environ({"JWT_TOKEN": jwt_token}):
            yield


@contextmanager
def stand_up_airflow(
    env: Any = {},
    airflow_cmd: list[str] = ["airflow", "standalone"],
    cwd: Optional[Path] = None,
    stdout_channel: Optional[int] = None,
    port: int = 8080,
    expected_num_dags: int = 1,
) -> Generator[subprocess.Popen, None, None]:
    process = subprocess.Popen(
        airflow_cmd,
        cwd=cwd,
        env=env,  # since we have some temp vars in the env right now
        shell=False,
        start_new_session=True,
        stdout=stdout_channel,
    )
    try:
        print("Checking if Airflow is serving")
        is_serving = _airflow_is_serving(port=port)
        print(f"Airflow is serving {is_serving}")
        with optionally_stash_jwt_token(port=port):
            _airflow_is_ready(port=port, expected_num_dags=expected_num_dags)
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
