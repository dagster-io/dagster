from datetime import datetime

import pytest
from dagster_airlift.test import (
    AirflowInstanceFake,
    make_dag_info,
    make_dag_run,
    make_task_info,
    make_task_instance,
)


def test_test_instance() -> None:
    """Test the AirflowInstanceFake class."""
    dag_info = make_dag_info(dag_id="test_dag", file_token="test_file_token")
    task_info = make_task_info(dag_id="test_dag", task_id="test_task")
    task_instance = make_task_instance(
        dag_id="test_dag",
        task_id="test_task",
        run_id="test_run_id",
        start_date=datetime(2022, 1, 1),
        end_date=datetime(2022, 1, 2),
    )
    assert task_instance.logical_date == datetime(2022, 1, 1)
    dag_run = make_dag_run(
        dag_id="test_dag",
        run_id="test_run_id",
        start_date=datetime(2022, 1, 1),
        end_date=datetime(2022, 1, 2),
    )
    assert dag_run.logical_date == datetime(2022, 1, 1)
    test_instance = AirflowInstanceFake(
        dag_infos=[dag_info],
        task_infos=[task_info],
        task_instances=[task_instance],
        dag_runs=[dag_run],
    )

    # Dag doesn't exist in instance
    with pytest.raises(ValueError):
        test_instance.get_dag_runs(
            dag_id="nonexistent_dag", start_date=datetime(2022, 1, 1), end_date=datetime(2022, 1, 2)
        )

    # Task doesn't exist in instance
    with pytest.raises(ValueError):
        test_instance.get_task_info(dag_id="test_dag", task_id="nonexistent_task")

    # Dag not in instance
    with pytest.raises(ValueError):
        test_instance.get_task_infos(dag_id="nonexistent_dag")

    # Task instance doesn't exist in instance (task id is wrong)
    with pytest.raises(ValueError):
        test_instance.get_task_instance(
            dag_id="test_dag", task_id="nonexistent_task", run_id="test_run_id"
        )

    # Task instance doesn't exist in instance (dag id is wrong)
    with pytest.raises(ValueError):
        test_instance.get_task_instance(
            dag_id="nonexistent_dag", task_id="test_task", run_id="test_run_id"
        )

    # Task instance doesn't exist in instance (run id is wrong)
    with pytest.raises(ValueError):
        test_instance.get_task_instance(
            dag_id="test_dag", task_id="test_task", run_id="nonexistent_run_id"
        )

    with pytest.raises(ValueError):
        test_instance.get_dag_runs(
            dag_id="nonexistent_dag", start_date=datetime(2022, 1, 1), end_date=datetime(2022, 1, 2)
        )

    assert test_instance.list_dags() == [dag_info]
    assert test_instance.get_dag_info(dag_id="test_dag") == dag_info
    # Matching range
    assert test_instance.get_dag_runs(
        dag_id="test_dag", start_date=datetime(2022, 1, 1), end_date=datetime(2022, 1, 2)
    ) == [dag_run]
    # Range is too late
    assert (
        test_instance.get_dag_runs(
            dag_id="test_dag", start_date=datetime(2022, 1, 2), end_date=datetime(2022, 1, 3)
        )
        == []
    )
    # Range is too early
    assert (
        test_instance.get_dag_runs(
            dag_id="test_dag", start_date=datetime(2021, 12, 31), end_date=datetime(2022, 1, 1)
        )
        == []
    )

    # Can retrieve task info
    assert test_instance.get_task_info(dag_id="test_dag", task_id="test_task") == task_info

    # Can retrieve task infos
    assert test_instance.get_task_infos(dag_id="test_dag") == [task_info]

    # Can retrieve task instance
    assert (
        test_instance.get_task_instance(
            dag_id="test_dag", task_id="test_task", run_id="test_run_id"
        )
        == task_instance
    )

    assert (
        test_instance.get_dag_source_code(file_token="test_file_token")
        == "indicates found source code"
    )
    with pytest.raises(ValueError):
        test_instance.get_dag_source_code(file_token="nonexistent_file_token")
