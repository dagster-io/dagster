import os
import shutil
import subprocess
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

import pytest
from dagster_airlift.core import AirflowBasicAuthBackend, AirflowInstance
from dagster_airlift.test.shared_fixtures import stand_up_airflow, stand_up_dagster


def makefile_dir() -> Path:
    return Path(__file__).parent.parent


def airflow_test_instance(port: int) -> AirflowInstance:
    return AirflowInstance(
        auth_backend=AirflowBasicAuthBackend(
            webserver_url=f"http://localhost:{port}",
            username="admin",
            password="admin",
        ),
        name="test",
    )


def warehouse_instance() -> AirflowInstance:
    return airflow_test_instance(8081)


def metrics_instance() -> AirflowInstance:
    return airflow_test_instance(8082)


@pytest.fixture(name="local_env")
def local_env_fixture() -> Generator[None, None, None]:
    try:
        subprocess.run(["make", "airflow_setup"], cwd=makefile_dir(), check=True)
        yield
    finally:
        subprocess.run(["make", "wipe"], cwd=makefile_dir(), check=True)


@pytest.fixture(name="warehouse_airflow")
def warehouse_airflow_fixture(local_env: None) -> Generator[subprocess.Popen, None, None]:
    process = None
    try:
        with stand_up_airflow(
            airflow_cmd=["make", "warehouse_airflow_run"],
            env=os.environ,
            cwd=makefile_dir(),
            port=8081,
        ) as process:
            yield process
    finally:
        if process:
            process.terminate()


@pytest.fixture(name="metrics_airflow")
def metrics_airflow_fixture(local_env: None) -> Generator[subprocess.Popen, None, None]:
    process = None
    try:
        with stand_up_airflow(
            airflow_cmd=["make", "metrics_airflow_run"],
            env=os.environ,
            cwd=makefile_dir(),
            port=8082,
        ) as process:
            yield process
    finally:
        if process:
            process.terminate()


@pytest.fixture(name="dagster_dev")
def dagster_fixture(
    warehouse_airflow: subprocess.Popen, metrics_airflow: subprocess.Popen
) -> Generator[subprocess.Popen, None, None]:
    process = None
    try:
        with stand_up_dagster(
            dagster_dev_cmd=["make", "-C", str(makefile_dir()), "dagster_run"],
            port=3000,
        ) as process:
            yield process
    finally:
        if process:
            process.terminate()


@contextmanager
def replace_file(old_file: Path, new_file: Path) -> Generator[None, None, None]:
    backup_file = old_file.with_suffix(old_file.suffix + ".bak")
    try:
        if old_file.exists():
            shutil.copy2(old_file, backup_file)
        if new_file.exists():
            shutil.copy2(new_file, old_file)
        else:
            raise FileNotFoundError(f"New file {new_file} not found")
        yield
    finally:
        if backup_file.exists():
            shutil.copy2(backup_file, old_file)
            backup_file.unlink()


ORIG_DEFS_FILE = makefile_dir() / "airlift_federation_tutorial" / "dagster_defs" / "definitions.py"
SNIPPETS_DIR = makefile_dir() / "snippets"


def assert_successful_dag_run(af_instance: AirflowInstance, dag_id: str) -> None:
    run_id = af_instance.trigger_dag(dag_id)
    assert run_id is not None
    af_instance.wait_for_run_completion(dag_id=dag_id, run_id=run_id)
    assert af_instance.get_run_state(dag_id=dag_id, run_id=run_id) == "success"
