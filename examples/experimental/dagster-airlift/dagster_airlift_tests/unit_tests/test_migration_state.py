from pathlib import Path

import pytest
import yaml
from dagster_airlift.in_airflow.proxied_state import (
    AirflowProxiedState,
    DagProxiedState,
    ProxiedStateParsingError,
    TaskProxiedState,
    load_proxied_state_from_yaml,
)


def test_proxied_state() -> None:
    """Test that we can load proxied state from a yaml file, and that errors are handled in a reasonable way."""
    # First test a valid proxied directory with two files.
    valid_proxied_state_file = Path(__file__).parent / "proxied_state_yamls" / "valid"
    proxied_state = load_proxied_state_from_yaml(valid_proxied_state_file)
    assert isinstance(proxied_state, AirflowProxiedState)
    assert proxied_state == AirflowProxiedState(
        dags={
            "first": DagProxiedState(
                tasks={
                    "first_task": TaskProxiedState(task_id="first_task", proxied=True),
                    "second_task": TaskProxiedState(task_id="second_task", proxied=False),
                    "third_task": TaskProxiedState(task_id="third_task", proxied=True),
                }
            ),
            "second": DagProxiedState(
                tasks={
                    "some_task": TaskProxiedState("some_task", proxied=True),
                    "other_task": TaskProxiedState("other_task", proxied=False),
                }
            ),
        }
    )

    # Test various incorrect yaml dirs.
    incorrect_dirs = ["empty_file", "nonexistent_dir", "extra_key", "nonsense"]
    for incorrect_dir in incorrect_dirs:
        incorrect_proxied_state_file = Path(__file__).parent / "proxied_state_yamls" / incorrect_dir
        with pytest.raises(ProxiedStateParsingError, match="Error parsing proxied state yaml"):
            load_proxied_state_from_yaml(incorrect_proxied_state_file)


def test_proxied_state_from_yaml() -> None:
    proxied_state_dict = yaml.safe_load("""
tasks:
  - id: load_raw_customers
    proxied: False
  - id: build_dbt_models
    proxied: False
  - id: export_customers
    proxied: True 
 """)

    dag_proxied_state = DagProxiedState.from_dict(proxied_state_dict)
    assert dag_proxied_state.is_task_proxied("load_raw_customers") is False
    assert dag_proxied_state.is_task_proxied("build_dbt_models") is False
    assert dag_proxied_state.is_task_proxied("export_customers") is True
