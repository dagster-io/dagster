import os
import shutil
import subprocess
from collections.abc import Generator
from pathlib import Path

import pytest
from dagster._core.test_utils import environ
from dagster_airlift.test.shared_fixtures import stand_up_airflow


def makefile_dir() -> Path:
    return Path(__file__).parent.parent


@pytest.fixture(name="local_env")
def local_env_fixture() -> Generator[None, None, None]:
    subprocess.run(["make", "setup_local_env"], cwd=makefile_dir(), check=True)
    with environ(
        {
            "AIRFLOW_HOME": str(makefile_dir() / ".airflow_home"),
            "DAGSTER_HOME": str(makefile_dir() / ".dagster_home"),
        }
    ):
        yield
    # Best-effort cleanup. Airflow child processes (gunicorn workers, scheduler, etc.)
    # may still be writing to .airflow_home after the process group is killed, causing
    # `rm -rf` to fail with "Directory not empty". This is safe because setup_local_env
    # starts with `make wipe` anyway.
    shutil.rmtree(makefile_dir() / ".airflow_home", ignore_errors=True)
    shutil.rmtree(makefile_dir() / ".dagster_home", ignore_errors=True)


@pytest.fixture(name="dags_dir")
def dags_dir_fixture() -> Path:
    return Path(__file__).parent.parent / "perf_harness" / "airflow_dags"


@pytest.fixture(name="airflow_home")
def airflow_home_fixture(local_env: None) -> Path:
    return Path(os.environ["AIRFLOW_HOME"])


@pytest.fixture(name="airflow_instance")
def airflow_instance_fixture(local_env: None) -> Generator[subprocess.Popen, None, None]:
    with stand_up_airflow(
        airflow_cmd=["make", "run_airflow"], env=os.environ, cwd=makefile_dir()
    ) as process:
        yield process
