import os
import subprocess
from typing import Generator

import pytest
from dagster._core.test_utils import environ


@pytest.fixture(name="setup")
def setup_fixture() -> Generator[None, None, None]:
    makefile_dir = os.path.join(os.path.dirname(__file__), "..")
    subprocess.run(["make", "setup_local_env"], cwd=makefile_dir, check=True)
    with environ(
        {
            "AIRFLOW_HOME": os.path.join(makefile_dir, ".airflow_home"),
            "DBT_PROJECT_DIR": os.path.join(makefile_dir, "peering_with_dbt", "dbt"),
        }
    ):
        yield
    subprocess.run(["make", "wipe"], check=True)
