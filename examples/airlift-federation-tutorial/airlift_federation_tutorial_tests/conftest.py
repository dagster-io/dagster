import os
import shutil
import subprocess
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

import pytest
from dagster_airlift.test.shared_fixtures import stand_up_airflow, stand_up_dagster


def makefile_dir() -> Path:
    return Path(__file__).parent.parent


@pytest.fixture(name="local_env")
def local_env_fixture() -> Generator[None, None, None]:
    try:
        subprocess.run(["make", "airflow_setup"], cwd=makefile_dir(), check=True)
        yield
    finally:
        subprocess.run(["make", "wipe"], cwd=makefile_dir(), check=True)


@pytest.fixture(name="upstream_airflow")
def upstream_airflow_fixture(local_env: None) -> Generator[subprocess.Popen, None, None]:
    process = None
    try:
        with stand_up_airflow(
            airflow_cmd=["make", "upstream_airflow_run"],
            env=os.environ,
            cwd=makefile_dir(),
            port=8081,
        ) as process:
            yield process
    finally:
        if process:
            process.terminate()


@pytest.fixture(name="downstream_airflow")
def downstream_airflow_fixture(local_env: None) -> Generator[subprocess.Popen, None, None]:
    process = None
    try:
        with stand_up_airflow(
            airflow_cmd=["make", "downstream_airflow_run"],
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
    upstream_airflow: subprocess.Popen, downstream_airflow: subprocess.Popen
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
