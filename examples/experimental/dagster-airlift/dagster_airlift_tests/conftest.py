import os
import subprocess
from tempfile import TemporaryDirectory
from typing import Generator

import pytest
from dagster._core.test_utils import environ


@pytest.fixture(name="setup")
def setup_fixture() -> Generator[str, None, None]:
    with TemporaryDirectory() as tmpdir:
        # run chmod +x create_airflow_cfg.sh and then run create_airflow_cfg.sh tmpdir
        temp_env = {**os.environ.copy(), "AIRFLOW_HOME": tmpdir}
        # go up one directory from current
        path_to_script = os.path.join(os.path.dirname(__file__), "..", "airflow_setup.sh")
        path_to_dags = os.path.join(os.path.dirname(__file__), "airflow_project", "dags")
        subprocess.run(["chmod", "+x", path_to_script], check=True, env=temp_env)
        subprocess.run([path_to_script, path_to_dags], check=True, env=temp_env)
        with environ({"AIRFLOW_HOME": tmpdir}):
            yield tmpdir


@pytest.fixture(name="dbt_project_dir")
def dbt_project_fixture() -> str:
    return os.path.join(os.path.dirname(__file__), "dbt_project")


@pytest.fixture
def dbt_project(dbt_project_dir: str) -> None:
    """Builds dbt project."""
    temp_env = {
        **os.environ.copy(),
        "DUCKDB_PATH": os.path.join(dbt_project_dir, "target", "local.duckdb"),
    }
    subprocess.run(
        ["dbt", "build", "--project-dir", dbt_project_dir, "--profiles-dir", dbt_project_dir],
        check=True,
        env=temp_env,
    )
