import os
import shutil
import subprocess
from pathlib import Path

import yaml
from dagster_airlift.in_airflow.proxied_state import load_proxied_state_from_yaml
from dagster_airlift.test import configured_airflow_home


def airflow_home_dir() -> Path:
    return Path(__file__).parent / "scaffold_test_airflow_home"


def proxied_state_dir() -> Path:
    return airflow_home_dir() / "dags" / "proxied_state"


def run_scaffold_script() -> None:
    subprocess.run(["dagster-airlift", "proxy", "scaffold"], check=True, env=os.environ.copy())


def expected_xcom_yaml() -> str:
    return """
tasks:
  - id: bash_pull
    proxied: false
  - id: bash_push
    proxied: false
  - id: pull_value_from_bash_push
    proxied: false
  - id: puller
    proxied: false
  - id: push
    proxied: false 
  - id: push_by_returning
    proxied: false
"""


def expected_bash_operator_yaml() -> str:
    return """
tasks:
  - id: also_run_this
    proxied: false
  - id: run_after_loop
    proxied: false
  - id: run_this_last
    proxied: false
  - id: runme_0
    proxied: false
  - id: runme_1
    proxied: false
  - id: runme_2
    proxied: false
  - id: this_will_skip
    proxied: false
"""


def test_scaffold_proxied_state() -> None:
    """Test scaffold proxied state under different scenarios."""
    if airflow_home_dir().exists():
        shutil.rmtree(airflow_home_dir())
    # Airflow home set and no proxied_state directory exists.
    with configured_airflow_home(airflow_home_dir()):
        run_scaffold_script()
        assert proxied_state_dir().exists()
        symbols = list(proxied_state_dir().iterdir())
        # Check that path contents are two files, one for each dag.
        assert len(list(symbols)) > 0  # Cherry pick some example files.
        assert all([symbol.is_file() for symbol in symbols])
        assert all([symbol.suffix == ".yaml" for symbol in symbols])
        assert "example_xcom.yaml" in {symbol.name for symbol in symbols}
        assert "example_bash_operator.yaml" in {symbol.name for symbol in symbols}
        example_xcom_yaml = proxied_state_dir() / "example_xcom.yaml"
        assert yaml.safe_load(example_xcom_yaml.read_text()) == yaml.safe_load(expected_xcom_yaml())
        example_bash_operator_yaml = proxied_state_dir() / "example_bash_operator.yaml"
        assert yaml.safe_load(example_bash_operator_yaml.read_text()) == yaml.safe_load(
            expected_bash_operator_yaml()
        )
        proxied_state = load_proxied_state_from_yaml(proxied_state_dir())
        assert (
            proxied_state.get_task_proxied_state(dag_id="example_xcom", task_id="bash_pull")
            is False
        )
        assert (
            proxied_state.get_task_proxied_state(dag_id="example_xcom", task_id="bash_push")
            is False
        )
        assert (
            proxied_state.get_task_proxied_state(dag_id="example_bash_operator", task_id="runme_0")
            is False
        )
        assert (
            proxied_state.get_task_proxied_state(dag_id="example_bash_operator", task_id="runme_1")
            is False
        )

    shutil.rmtree(airflow_home_dir())
