import json

import pytest
from airflow.operators.python import PythonOperator
from dagster_airlift.in_airflow import mark_as_dagster_migrating
from dagster_airlift.in_airflow.base_proxy_operator import BaseProxyToDagsterOperator
from dagster_airlift.migration_state import AirflowMigrationState

from dagster_airlift_tests.unit_tests.in_airflow_tests.conftest import (
    build_dags_dict_given_structure,
)


def test_mark_as_dagster_migrating() -> None:
    """Test that we can mark a set of dags as migrating to dagster, and as a result, operators are replaced and tags are added."""
    globals_fake = build_dags_dict_given_structure(
        {
            "task_is_migrated": {"task": []},
            "task_isnt_migrated": {"task": []},
            "should_be_ignored": {"task": []},
        }
    )
    mark_as_dagster_migrating(
        global_vars=globals_fake,
        migration_state=AirflowMigrationState.from_dict(
            {
                "task_is_migrated": {"tasks": [{"id": "task", "migrated": True}]},
                "task_isnt_migrated": {"tasks": [{"id": "task", "migrated": False}]},
            }
        ),
    )
    # Only the task marked as migrated should be replaced with a DagsterOperator
    assert isinstance(
        globals_fake["task_is_migrated"].task_dict["task"], BaseProxyToDagsterOperator
    )
    assert isinstance(globals_fake["task_isnt_migrated"].task_dict["task"], PythonOperator)
    assert isinstance(globals_fake["should_be_ignored"].task_dict["task"], PythonOperator)

    # Only task_is_migrated and task_isnt_migrated should have tags added.
    assert len(globals_fake["task_is_migrated"].tags) == 1
    assert len(globals_fake["task_isnt_migrated"].tags) == 1
    assert len(globals_fake["should_be_ignored"].tags) == 0
    assert json.loads(next(iter(globals_fake["task_is_migrated"].tags))) == {
        "DAGSTER_MIGRATION_STATUS": {"tasks": [{"id": "task", "migrated": True}]}
    }
    assert json.loads(next(iter(globals_fake["task_isnt_migrated"].tags))) == {
        "DAGSTER_MIGRATION_STATUS": {"tasks": [{"id": "task", "migrated": False}]}
    }


def test_mark_as_dagster_migrating_no_dags() -> None:
    """Ensure that we error when no dags are found in the current context."""
    with pytest.raises(Exception, match="No dags found in globals dictionary."):
        mark_as_dagster_migrating(
            global_vars={}, migration_state=AirflowMigrationState.from_dict({})
        )


def test_mark_as_dagster_migrating_dags_dont_exist() -> None:
    """Ensure that we error when a dag is referenced that does not exist."""
    globals_fake = build_dags_dict_given_structure({"dag": {"task": []}})
    with pytest.raises(
        Exception, match="Dag with id `doesnt_exist` not found in globals dictionary"
    ):
        mark_as_dagster_migrating(
            global_vars=globals_fake,
            migration_state=AirflowMigrationState.from_dict(
                {
                    "doesnt_exist": {"tasks": [{"id": "task", "migrated": True}]},
                }
            ),
        )


def test_mark_as_dagster_migrating_task_doesnt_exist() -> None:
    """Ensure that we error when a task is referenced that does not exist."""
    globals_fake = build_dags_dict_given_structure({"dag": {"task": []}})
    with pytest.raises(Exception, match="Task with id `doesnt_exist` not found in dag `dag`"):
        mark_as_dagster_migrating(
            global_vars=globals_fake,
            migration_state=AirflowMigrationState.from_dict(
                {
                    "dag": {"tasks": [{"id": "doesnt_exist", "migrated": True}]},
                }
            ),
        )
