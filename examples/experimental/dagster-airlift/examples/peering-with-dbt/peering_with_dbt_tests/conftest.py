import os
import signal
import subprocess
from typing import Any, Generator

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


@pytest.fixture(name="airflow_instance")
def airflow_instance_fixture(setup: None) -> Generator[Any, None, None]:
    process = subprocess.Popen(
        ["airflow", "standalone"],
        env=os.environ,  # since we have some temp vars in the env right now
        shell=False,
        stdout=subprocess.PIPE,
        preexec_fn=os.setsid,  # noqa  # fuck it we ball
    )
    assert process.stdout is not None
    for line in process.stdout:
        if "Airflow is ready" in line.decode():
            break
    yield process
    # Kill process group, since process.kill and process.terminate do not work.
    os.killpg(process.pid, signal.SIGKILL)
