import contextlib
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import AbstractSet, Callable, Generator, Iterator

import pytest
import yaml
from dagster._core.test_utils import environ


@pytest.fixture(name="makefile_dir")
def makefile_dir_fixture() -> Path:
    return Path(__file__).parent.parent.parent


@pytest.fixture(name="local_env")
def local_env_fixture(makefile_dir: Path) -> Generator[None, None, None]:
    subprocess.run(["make", "airflow_setup"], cwd=makefile_dir, check=True)
    with environ(
        {
            "MAKEFILE_DIR": str(makefile_dir),
            "TUTORIAL_EXAMPLE_DIR": str(makefile_dir),
            "AIRFLOW_HOME": str(makefile_dir / ".airflow_home"),
            "TUTORIAL_DBT_PROJECT_DIR": str(makefile_dir / "tutorial_example" / "shared" / "dbt"),
            "DBT_PROFILES_DIR": str(makefile_dir / "tutorial_example" / "shared" / "dbt"),
            "DAGSTER_HOME": str(makefile_dir / ".dagster_home"),
            "DAGSTER_URL": "http://localhost:3333",
        }
    ):
        yield
    subprocess.run(["make", "wipe"], cwd=makefile_dir, check=True)


@pytest.fixture(name="dags_dir")
def dags_dir_fixture(makefile_dir: Path) -> Iterator[Path]:
    # Creates a temporary directory and copies the dags into it
    # So we can manipulate the proxied state without affecting the original files
    with tempfile.TemporaryDirectory() as tmpdir:
        shutil.copytree(
            makefile_dir / "tutorial_example" / "airflow_dags",
            tmpdir,
            dirs_exist_ok=True,
        )
        yield Path(tmpdir)


@pytest.fixture(name="airflow_home")
def airflow_home_fixture(local_env) -> Path:
    return Path(os.environ["AIRFLOW_HOME"])


@pytest.fixture(name="mark_tasks_migrated")
def mark_tasks_migrated_fixture(
    dags_dir: Path,
    reserialize_dags: Callable[[], None],
) -> Callable[[AbstractSet[str]], contextlib.AbstractContextManager]:
    """Returns a context manager that marks the specified tasks as proxied in the proxied state file
    for the duration of the context manager's scope.
    """
    proxied_state_file = dags_dir / "proxied_state" / "rebuild_customers_list.yaml"
    all_tasks = {"load_raw_customers", "build_dbt_models", "export_customers"}

    @contextlib.contextmanager
    def mark_tasks_migrated(migrated_tasks: AbstractSet[str]) -> Iterator[None]:
        """Updates the contents of the proxied state file to mark the specified tasks as proxied."""
        with open(proxied_state_file, "r") as f:
            contents = f.read()

        try:
            with open(proxied_state_file, "w") as f:
                f.write(
                    yaml.dump(
                        {
                            "tasks": [
                                {"id": task, "proxied": task in migrated_tasks}
                                for task in all_tasks
                            ]
                        }
                    )
                )

            reserialize_dags()
            yield

        finally:
            with open(proxied_state_file, "w") as f:
                f.write(contents)

    return mark_tasks_migrated
