import copy
import json

import pytest
from airflow.operators.python import PythonOperator
from dagster._core.test_utils import environ
from dagster_airlift.in_airflow import mark_as_dagster_migrating
from dagster_airlift.in_airflow.base_proxy_operator import BaseProxyToDagsterOperator
from dagster_airlift.migration_state import AirflowProxiedState
from dagster_airlift.test.shared_fixtures import VAR_DICT
from dagster_airlift.utils import DAGSTER_AIRLIFT_MIGRATION_STATE_DIR_ENV_VAR

from dagster_airlift_tests.unit_tests.in_airflow_tests.conftest import (
    build_dags_dict_given_structure,
)


def test_mark_as_dagster_migrating_local_dir_set(mock_airflow_variable: None, caplog) -> None:
    """Test that when a local directory variable is set, we don't use the variable."""
    with environ({DAGSTER_AIRLIFT_MIGRATION_STATE_DIR_ENV_VAR: "/tmp"}):
        globals_fake = build_dags_dict_given_structure(
            {
                "dag": {"task": []},
            }
        )

        mark_as_dagster_migrating(
            global_vars=globals_fake,
            migration_state=AirflowProxiedState.from_dict(
                {
                    "dag": {"tasks": [{"id": "task", "migrated": True}]},
                }
            ),
        )
        assert any(
            "Executing in local mode" in record.message and record.levelname == "INFO"
            for record in caplog.records
        )

        assert VAR_DICT == {}


def test_mark_as_dagster_migrating(mock_airflow_variable: None) -> None:
    """Test that we can mark a set of dags as migrating to dagster, and as a result, operators are replaced and tags are added."""
    globals_fake = build_dags_dict_given_structure(
        {
            "task_is_migrated": {"task": []},
            "initially_not_migrated": {"task": []},
            "should_be_ignored": {"task": []},
        }
    )
    original_globals = copy.deepcopy(globals_fake)
    mark_as_dagster_migrating(
        global_vars=globals_fake,
        migration_state=AirflowProxiedState.from_dict(
            {
                "task_is_migrated": {"tasks": [{"id": "task", "migrated": True}]},
                "initially_not_migrated": {"tasks": [{"id": "task", "migrated": False}]},
            }
        ),
    )
    # Both dags should have the tag "Migrating to Dagster"
    assert len(globals_fake["task_is_migrated"].tags) == 1
    assert len(globals_fake["initially_not_migrated"].tags) == 1

    assert "1 Task Marked as Migrating to Dagster" in globals_fake["task_is_migrated"].tags
    assert "0 Tasks Marked as Migrating to Dagster" in globals_fake["initially_not_migrated"].tags

    # Only the task marked as migrated should be replaced with a DagsterOperator
    assert isinstance(
        globals_fake["task_is_migrated"].task_dict["task"], BaseProxyToDagsterOperator
    )
    assert isinstance(globals_fake["initially_not_migrated"].task_dict["task"], PythonOperator)
    assert isinstance(globals_fake["should_be_ignored"].task_dict["task"], PythonOperator)

    # Check the variable store
    assert VAR_DICT == {
        "task_is_migrated_dagster_migration_state": json.dumps(
            {"tasks": [{"id": "task", "migrated": True}]}
        ),
        "initially_not_migrated_dagster_migration_state": json.dumps(
            {"tasks": [{"id": "task", "migrated": False}]}
        ),
    }

    # Change initially_not_migrated to be migrated
    mark_as_dagster_migrating(
        global_vars=original_globals,
        migration_state=AirflowProxiedState.from_dict(
            {
                "task_is_migrated": {"tasks": [{"id": "task", "migrated": True}]},
                "initially_not_migrated": {"tasks": [{"id": "task", "migrated": True}]},
            }
        ),
    )
    # Both dags should have the tag "Migrating to Dagster"
    assert len(original_globals["task_is_migrated"].tags) == 1
    assert len(original_globals["initially_not_migrated"].tags) == 1

    assert "1 Task Marked as Migrating to Dagster" in original_globals["task_is_migrated"].tags
    assert (
        "1 Task Marked as Migrating to Dagster" in original_globals["initially_not_migrated"].tags
    )

    # Both tasks should be replaced with a DagsterOperator
    assert isinstance(
        original_globals["task_is_migrated"].task_dict["task"], BaseProxyToDagsterOperator
    )
    assert isinstance(
        original_globals["initially_not_migrated"].task_dict["task"], BaseProxyToDagsterOperator
    )
    assert isinstance(original_globals["should_be_ignored"].task_dict["task"], PythonOperator)

    # Check the variable store
    assert VAR_DICT == {
        "task_is_migrated_dagster_migration_state": json.dumps(
            {"tasks": [{"id": "task", "migrated": True}]}
        ),
        "initially_not_migrated_dagster_migration_state": json.dumps(
            {"tasks": [{"id": "task", "migrated": True}]}
        ),
    }


def test_mark_as_dagster_migrating_no_dags() -> None:
    """Ensure that we error when no dags are found in the current context."""
    with pytest.raises(Exception, match="No dags found in globals dictionary."):
        mark_as_dagster_migrating(global_vars={}, migration_state=AirflowProxiedState.from_dict({}))


def test_mark_as_dagster_migrating_dags_dont_exist() -> None:
    """Ensure that we dont error when a dag is referenced that does not exist."""
    globals_fake = build_dags_dict_given_structure({"dag": {"task": []}})
    mark_as_dagster_migrating(
        global_vars=globals_fake,
        migration_state=AirflowProxiedState.from_dict(
            {
                "doesnt_exist": {"tasks": [{"id": "task", "migrated": True}]},
            }
        ),
    )
    dag = globals_fake["dag"]
    assert len(dag.tags) == 0


def test_mark_as_dagster_migrating_task_doesnt_exist() -> None:
    """Ensure that we error when a task is referenced that does not exist."""
    globals_fake = build_dags_dict_given_structure({"dag": {"task": []}})
    with pytest.raises(Exception, match="Task with id `doesnt_exist` not found in dag `dag`"):
        mark_as_dagster_migrating(
            global_vars=globals_fake,
            migration_state=AirflowProxiedState.from_dict(
                {
                    "dag": {"tasks": [{"id": "doesnt_exist", "migrated": True}]},
                }
            ),
        )
