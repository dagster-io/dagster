import os
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Generator

import pytest
import requests
from dagster._core.test_utils import environ


@pytest.fixture(name="setup")
def setup_fixture() -> Generator[str, None, None]:
    with TemporaryDirectory() as tmpdir:
        # run chmod +x create_airflow_cfg.sh and then run create_airflow_cfg.sh tmpdir
        temp_env = {**os.environ.copy(), "AIRFLOW_HOME": tmpdir}
        # go up one directory from current
        path_to_script = Path(__file__).parent.parent.parent / "airflow_setup.sh"
        path_to_dags = Path(__file__).parent / "incorrectly_marked_dag" / "dags"
        subprocess.run(["chmod", "+x", path_to_script], check=True, env=temp_env)
        subprocess.run([path_to_script, path_to_dags], check=True, env=temp_env)
        with environ({"AIRFLOW_HOME": tmpdir}):
            yield tmpdir


def test_migrating_dag(airflow_instance: None) -> None:
    """Tests that an incorrectly marked dag throws an exception, and is not loaded."""
    response = requests.get("http://localhost:8080/api/v1/dags/marked_dag", auth=("admin", "admin"))
    assert response.status_code == 200
    tags = response.json()["tags"]
    assert len(tags) == 0
