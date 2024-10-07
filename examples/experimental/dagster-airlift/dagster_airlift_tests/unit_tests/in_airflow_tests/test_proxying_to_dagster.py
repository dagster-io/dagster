import copy
import json

import pytest
from airflow.operators.python import PythonOperator
from dagster._core.test_utils import environ
from dagster_airlift.in_airflow import proxying_to_dagster
from dagster_airlift.in_airflow.base_asset_operator import BaseDagsterAssetsOperator
from dagster_airlift.in_airflow.proxied_state import AirflowProxiedState
from dagster_airlift.test.shared_fixtures import VAR_DICT
from dagster_airlift.utils import DAGSTER_AIRLIFT_PROXIED_STATE_DIR_ENV_VAR

from dagster_airlift_tests.unit_tests.in_airflow_tests.conftest import (
    build_dags_dict_given_structure,
)


def test_proxying_to_dagster_local_dir_set(mock_airflow_variable: None, caplog) -> None:
    """Test that when a local directory variable is set, we don't use the variable."""
    with environ({DAGSTER_AIRLIFT_PROXIED_STATE_DIR_ENV_VAR: "/tmp"}):
        globals_fake = build_dags_dict_given_structure(
            {
                "dag": {"task": []},
            }
        )

        proxying_to_dagster(
            global_vars=globals_fake,
            proxied_state=AirflowProxiedState.from_dict(
                {
                    "dag": {"tasks": [{"id": "task", "proxied": True}]},
                }
            ),
        )
        assert any(
            "Executing in local mode" in record.message and record.levelname == "INFO"
            for record in caplog.records
        )

        assert VAR_DICT == {}


def test_proxying_to_dagster(mock_airflow_variable: None) -> None:
    """Test that we can proxy a set of dags, and as a result, operators are replaced and tags are added."""
    globals_fake = build_dags_dict_given_structure(
        {
            "task_is_proxied": {"task": []},
            "initially_not_proxied": {"task": []},
            "should_be_ignored": {"task": []},
        }
    )
    original_globals = copy.deepcopy(globals_fake)
    proxying_to_dagster(
        global_vars=globals_fake,
        proxied_state=AirflowProxiedState.from_dict(
            {
                "task_is_proxied": {"tasks": [{"id": "task", "proxied": True}]},
                "initially_not_proxied": {"tasks": [{"id": "task", "proxied": False}]},
            }
        ),
    )
    # Both dags should have the tag "Proxied to Dagster"
    assert len(globals_fake["task_is_proxied"].tags) == 1
    assert len(globals_fake["initially_not_proxied"].tags) == 1

    assert "1 Task Marked as Proxied to Dagster" in globals_fake["task_is_proxied"].tags
    assert "0 Tasks Marked as Proxied to Dagster" in globals_fake["initially_not_proxied"].tags

    # Only the task marked as proxied should be replaced with a DagsterOperator
    assert isinstance(globals_fake["task_is_proxied"].task_dict["task"], BaseDagsterAssetsOperator)
    assert isinstance(globals_fake["initially_not_proxied"].task_dict["task"], PythonOperator)
    assert isinstance(globals_fake["should_be_ignored"].task_dict["task"], PythonOperator)

    # Check the variable store
    assert VAR_DICT == {
        "task_is_proxied_dagster_proxied_state": json.dumps(
            {"tasks": [{"id": "task", "proxied": True}]}
        ),
        "initially_not_proxied_dagster_proxied_state": json.dumps(
            {"tasks": [{"id": "task", "proxied": False}]}
        ),
    }

    # Change initially_not_proxied to be proxied
    proxying_to_dagster(
        global_vars=original_globals,
        proxied_state=AirflowProxiedState.from_dict(
            {
                "task_is_proxied": {"tasks": [{"id": "task", "proxied": True}]},
                "initially_not_proxied": {"tasks": [{"id": "task", "proxied": True}]},
            }
        ),
    )
    # Both dags should have the tag "Proxied to Dagster"
    assert len(original_globals["task_is_proxied"].tags) == 1
    assert len(original_globals["initially_not_proxied"].tags) == 1

    assert "1 Task Marked as Proxied to Dagster" in original_globals["task_is_proxied"].tags
    assert "1 Task Marked as Proxied to Dagster" in original_globals["initially_not_proxied"].tags

    # Both tasks should be replaced with a DagsterOperator
    assert isinstance(
        original_globals["task_is_proxied"].task_dict["task"], BaseDagsterAssetsOperator
    )
    assert isinstance(
        original_globals["initially_not_proxied"].task_dict["task"],
        BaseDagsterAssetsOperator,
    )
    assert isinstance(original_globals["should_be_ignored"].task_dict["task"], PythonOperator)

    # Check the variable store
    assert VAR_DICT == {
        "task_is_proxied_dagster_proxied_state": json.dumps(
            {"tasks": [{"id": "task", "proxied": True}]}
        ),
        "initially_not_proxied_dagster_proxied_state": json.dumps(
            {"tasks": [{"id": "task", "proxied": True}]}
        ),
    }


def test_proxying_to_dagster_no_dags() -> None:
    """Ensure that we error when no dags are found in the current context."""
    with pytest.raises(Exception, match="No dags found in globals dictionary."):
        proxying_to_dagster(global_vars={}, proxied_state=AirflowProxiedState.from_dict({}))


def test_proxying_to_dagster_dags_dont_exist() -> None:
    """Ensure that we dont error when a dag is referenced that does not exist."""
    globals_fake = build_dags_dict_given_structure({"dag": {"task": []}})
    proxying_to_dagster(
        global_vars=globals_fake,
        proxied_state=AirflowProxiedState.from_dict(
            {
                "doesnt_exist": {"tasks": [{"id": "task", "proxied": True}]},
            }
        ),
    )
    dag = globals_fake["dag"]
    assert len(dag.tags) == 0


def test_proxying_to_dagster_task_doesnt_exist() -> None:
    """Ensure that we error when a task is referenced that does not exist."""
    globals_fake = build_dags_dict_given_structure({"dag": {"task": []}})
    with pytest.raises(Exception, match="Task with id `doesnt_exist` not found in dag `dag`"):
        proxying_to_dagster(
            global_vars=globals_fake,
            proxied_state=AirflowProxiedState.from_dict(
                {
                    "dag": {"tasks": [{"id": "doesnt_exist", "proxied": True}]},
                }
            ),
        )
