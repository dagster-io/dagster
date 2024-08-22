import os
import subprocess
from pathlib import Path
from typing import Generator

import pytest
from dagster._core.test_utils import environ


@pytest.fixture(name="local_env")
def local_env_fixture() -> Generator[None, None, None]:
    makefile_dir = Path(__file__).parent.parent
    subprocess.run(["make", "setup_local_env"], cwd=makefile_dir, check=True)
    with environ(
        {
            "AIRFLOW_HOME": str(makefile_dir / ".airflow_home"),
            "DBT_PROJECT_DIR": str(makefile_dir / "tutorial_example" / "shared" / "dbt"),
            "DAGSTER_HOME": str(makefile_dir / ".dagster_home"),
        }
    ):
        yield
    subprocess.run(["make", "wipe"], cwd=makefile_dir, check=True)


@pytest.fixture(name="dags_dir")
def dags_dir_fixture() -> Path:
    return Path(__file__).parent.parent / "tutorial_example" / "airflow_dags"


@pytest.fixture(name="airflow_home")
def airflow_home_fixture(local_env) -> Path:
    return Path(os.environ["AIRFLOW_HOME"])
