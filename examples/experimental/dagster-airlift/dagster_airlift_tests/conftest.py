import os
import signal
import subprocess
from tempfile import TemporaryDirectory
from typing import Any, Generator

import pytest


@pytest.fixture(name="airflow_home_dir")
def airflow_home_dir_fixture() -> Generator[str, None, None]:
    with TemporaryDirectory() as tmpdir:
        # run chmod +x create_airflow_cfg.sh and then run create_airflow_cfg.sh tmpdir
        temp_env = {**os.environ.copy(), "AIRFLOW_HOME": tmpdir}
        path_to_script = os.path.join(os.path.dirname(__file__), "create_airflow_cfg.sh")
        path_to_dags = os.path.join(os.path.dirname(__file__), "airflow_project", "dags")
        subprocess.run(["chmod", "+x", path_to_script], check=True, env=temp_env)
        subprocess.run([path_to_script, path_to_dags], check=True, env=temp_env)
        yield tmpdir


@pytest.fixture(name="airflow_instance")
def airflow_instance_fixture(airflow_home_dir: str) -> Generator[Any, None, None]:
    temp_env = {**os.environ.copy(), "AIRFLOW_HOME": airflow_home_dir}
    subprocess.run(["airflow", "db", "migrate"], check=True, env=temp_env)
    subprocess.run(
        [
            "airflow",
            "users",
            "create",
            "--username",
            "admin",
            "--firstname",
            "admin",
            "--lastname",
            "admin",
            "--role",
            "Admin",
            "--email",
            "foo@bar.com",
            "--password",
            "admin",
        ],
        check=True,
        env=temp_env,
    )
    process = subprocess.Popen(
        ["airflow", "standalone"],
        env=temp_env,
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
    process.wait()


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
