import copy

import pytest
from airflow.operators.python import PythonOperator
from dagster_airlift.in_airflow import proxying_to_dagster
from dagster_airlift.in_airflow.base_asset_operator import BaseDagsterAssetsOperator
from dagster_airlift.in_airflow.proxied_state import AirflowProxiedState

from dagster_airlift_tests.unit_tests.in_airflow_tests.conftest import (
    build_dags_dict_given_structure,
)


def test_proxying_to_dagster() -> None:
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
