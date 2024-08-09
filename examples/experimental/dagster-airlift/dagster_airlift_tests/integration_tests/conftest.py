import os
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Generator

import pytest
from dagster._core.test_utils import environ


@pytest.fixture(name="dags_dir")
def default_dags_dir():
    return Path(__file__).parent / "dags"


@pytest.fixture(name="setup")
def setup_fixture(dags_dir: Path) -> Generator[str, None, None]:
    with TemporaryDirectory() as tmpdir:
        # run chmod +x create_airflow_cfg.sh and then run create_airflow_cfg.sh tmpdir
        temp_env = {**os.environ.copy(), "AIRFLOW_HOME": tmpdir}
        # go up one directory from current
        path_to_script = Path(__file__).parent.parent.parent / "airflow_setup.sh"
        subprocess.run(["chmod", "+x", path_to_script], check=True, env=temp_env)
        subprocess.run([path_to_script, dags_dir], check=True, env=temp_env)
        with environ({"AIRFLOW_HOME": tmpdir}):
            yield tmpdir


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
