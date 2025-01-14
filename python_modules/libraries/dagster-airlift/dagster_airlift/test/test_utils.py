import subprocess
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

from dagster._core.test_utils import environ


def airlift_root() -> Path:
    return Path(__file__).parent.parent.parent


def remove_airflow_home_remnants(airflow_home: Path) -> None:
    logs_path = airflow_home / "logs"
    cfg_path = airflow_home / "airflow.cfg"
    db_path = airflow_home / "airflow.db"
    proxied_state_path = airflow_home / "airflow_dags" / "proxied_state"

    subprocess.check_output(
        ["rm", "-rf", str(logs_path), str(cfg_path), str(db_path), str(proxied_state_path)]
    )


def airflow_cfg_script_path() -> Path:
    return airlift_root() / "scripts" / "airflow_setup.sh"


def chmod_script(script_path: Path) -> None:
    subprocess.check_output(["chmod", "+x", str(script_path)])


@contextmanager
def configured_airflow_home(airflow_home: Path) -> Generator[None, None, None]:
    path_to_dags = airflow_home / "airflow_dags"
    with environ({"AIRFLOW_HOME": str(airflow_home)}):
        try:
            # Start by removing old cruft if it exists
            remove_airflow_home_remnants(airflow_home)
            # Scaffold the airflow configuration file.
            chmod_script(airflow_cfg_script_path())
            subprocess.run(
                [str(airflow_cfg_script_path()), str(path_to_dags), str(airflow_home)], check=False
            )
            yield
        finally:
            # Clean up after ourselves.
            remove_airflow_home_remnants(airflow_home)
