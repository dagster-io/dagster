import os
import signal
import subprocess
import time
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Generator

import pytest
import requests
from dagster._core.test_utils import environ
from dagster._time import get_current_timestamp


def assert_link_exists(link_name: str, link_url: Any):
    assert isinstance(link_url, str)
    assert requests.get(link_url).status_code == 200, f"{link_name} is broken"


@pytest.fixture(name="dags_dir")
def default_dags_dir():
    return Path(__file__).parent / "dags"


@pytest.fixture(name="airflow_home")
def default_airflow_home() -> Generator[str, None, None]:
    with TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture(name="setup")
def setup_fixture(airflow_home: Path, dags_dir: Path) -> Generator[str, None, None]:
    # run chmod +x create_airflow_cfg.sh and then run create_airflow_cfg.sh tmpdir
    temp_env = {
        **os.environ.copy(),
        "AIRFLOW_HOME": str(airflow_home),
        "DAGSTER_URL": "http://localhost:3333",
    }
    # go up one directory from current
    path_to_script = Path(__file__).parent.parent.parent / "airflow_setup.sh"
    subprocess.run(["chmod", "+x", path_to_script], check=True, env=temp_env)
    subprocess.run([path_to_script, dags_dir], check=True, env=temp_env)
    with environ({"AIRFLOW_HOME": str(airflow_home), "DAGSTER_URL": "http://localhost:3333"}):
        yield str(airflow_home)


@pytest.fixture(name="dbt_project_dir")
def dbt_project_fixture() -> Generator[Path, None, None]:
    path = Path(__file__).parent / "dbt_project"
    with environ(
        {"DBT_PROJECT_DIR": str(path), "DUCKDB_PATH": str(path / "target" / "local.duckdb")}
    ):
        yield path


@pytest.fixture
def dbt_project(dbt_project_dir: Path) -> None:
    """Builds dbt project."""
    subprocess.run(
        ["dbt", "build", "--project-dir", dbt_project_dir, "--profiles-dir", dbt_project_dir],
        check=True,
        env=os.environ.copy(),
    )


def dagster_is_ready() -> bool:
    try:
        response = requests.get("http://localhost:3333")
        return response.status_code == 200
    except:
        return False


@pytest.fixture(name="dagster_home")
def setup_dagster_home() -> Generator[str, None, None]:
    """Instantiate a temporary directory to serve as the DAGSTER_HOME."""
    with TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture(name="dagster_dev")
def setup_dagster(dagster_home: str, dagster_defs_path: str) -> Generator[Any, None, None]:
    """Stands up a dagster instance using the dagster dev CLI. dagster_defs_path must be provided
    by a fixture included in the callsite.
    """
    temp_env = {**os.environ.copy(), "DAGSTER_HOME": dagster_home}
    process = subprocess.Popen(
        ["dagster", "dev", "-f", dagster_defs_path, "-p", "3333"],
        env=temp_env,
        shell=False,
        preexec_fn=os.setsid,  # noqa
    )
    # Give dagster a second to stand up
    time.sleep(5)

    dagster_ready = False
    initial_time = get_current_timestamp()
    while get_current_timestamp() - initial_time < 60:
        if dagster_is_ready():
            dagster_ready = True
            break
        time.sleep(1)

    assert dagster_ready, "Dagster did not start within 30 seconds..."
    yield process
    os.killpg(process.pid, signal.SIGKILL)
