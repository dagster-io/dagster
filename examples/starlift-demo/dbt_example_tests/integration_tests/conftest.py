import os
import subprocess
from collections.abc import Generator
from pathlib import Path

import pytest
from dagster._core.test_utils import environ


def makefile_dir() -> Path:
    return Path(__file__).parent.parent.parent


@pytest.fixture(name="addtl_setup", scope="session")
def addtl_setup_fixture() -> Generator[None, None, None]:
    subprocess.run(["make", "setup_local_env"], cwd=makefile_dir(), check=True)
    with environ(
        {
            "AIRFLOW_HOME": str(makefile_dir() / ".airflow_home"),
            "DBT_PROJECT_DIR": str(makefile_dir() / "dbt_example" / "shared" / "dbt"),
            "DAGSTER_HOME": str(makefile_dir() / ".dagster_home"),
        }
    ):
        yield
    subprocess.run(["make", "wipe"], cwd=makefile_dir(), check=True)


@pytest.fixture(name="dags_dir", scope="session")
def dags_dir_fixture() -> Path:
    return makefile_dir() / "dbt_example" / "migrating_airflow_dags"


@pytest.fixture(name="airflow_home", scope="session")
def airflow_home_fixture(addtl_setup: None) -> Path:
    return Path(os.environ["AIRFLOW_HOME"])


@pytest.fixture(name="airflow_cmd", scope="session")
def airflow_cmd_fixture() -> list[str]:
    return ["make", "run_migrating_airflow", "-C", str(makefile_dir())]
