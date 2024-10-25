import subprocess
from pathlib import Path

import yaml
from dagster_airlift.in_airflow.proxied_state import load_proxied_state_from_yaml
from dagster_airlift.test import configured_airflow_home


def path_to_test_proj() -> Path:
    return Path(__file__).parent / "scaffold_test_airflow_home"


def run_scaffold_script() -> None:
    subprocess.run(["dagster-airlift", "proxy", "scaffold"], check=False)


def expected_yaml() -> str:
    return """
tasks:
  - id: downstream_print_task
    proxied: false
  - id: print_task 
    proxied: false 
"""


def test_scaffold_proxied_state() -> None:
    """Test scaffold proxied state under different scenarios."""
    # No AIRFLOW_HOME set.

    # Airflow home set but a proxied_state directory already exists.

    # Airflow home set and no proxied_state directory exists.
    with configured_airflow_home(path_to_test_proj()):
        run_scaffold_script()
        path_to_proxied_state = path_to_test_proj() / "airflow_dags" / "proxied_state"
        assert path_to_proxied_state.exists()
        symbols = list(path_to_proxied_state.iterdir())
        # Check that path contents are two files, one for each dag.
        assert len(list(symbols)) == 2
        assert all([symbol.is_file() for symbol in symbols])
        assert all([symbol.suffix == ".yaml" for symbol in symbols])
        assert {symbol.name for symbol in symbols} == {"print_dag.yaml", "other_print_dag.yaml"}
        print_dag_yaml = path_to_proxied_state / "print_dag.yaml"
        assert yaml.safe_load(print_dag_yaml.read_text()) == yaml.safe_load(expected_yaml())
        other_print_dag_yaml = path_to_proxied_state / "other_print_dag.yaml"
        assert yaml.safe_load(other_print_dag_yaml.read_text()) == yaml.safe_load(expected_yaml())
        proxied_state = load_proxied_state_from_yaml(path_to_proxied_state)
        assert (
            proxied_state.get_task_proxied_state(dag_id="print_dag", task_id="print_task") is False
        )
        assert (
            proxied_state.get_task_proxied_state(
                dag_id="print_dag", task_id="downstream_print_task"
            )
            is False
        )
        assert (
            proxied_state.get_task_proxied_state(dag_id="other_print_dag", task_id="print_task")
            is False
        )
        assert (
            proxied_state.get_task_proxied_state(
                dag_id="other_print_dag", task_id="downstream_print_task"
            )
            is False
        )
