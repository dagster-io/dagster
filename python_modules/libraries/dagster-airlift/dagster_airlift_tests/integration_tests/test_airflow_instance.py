import datetime

import pytest
from dagster_airlift.constants import infer_af_version_from_env
from dagster_airlift.core import AirflowInstance
from dagster_airlift.core.filter import AirflowFilter
from dagster_airlift.core.serialization.serialized_data import DagInfo
from dagster_airlift.test.shared_fixtures import (
    AIRFLOW_BASE_URL,
    AIRFLOW_INSTANCE_NAME,
    get_backend,
    is_airflow_2,
)
from dagster_shared.error import DagsterError

from dagster_airlift_tests.integration_tests.conftest import assert_link_exists


def test_airflow_instance(airflow_instance: None) -> None:
    """Test AirflowInstance APIs against live-running airflow. Ensure that links result in 200s.

    Airflow is loaded with one dag (print_dag) which contains two tasks (print_task, downstream_print_task).
    """
    instance = AirflowInstance(
        auth_backend=get_backend(),
        name=AIRFLOW_INSTANCE_NAME,
        airflow_version=infer_af_version_from_env(),
    )
    dag_infos = instance.list_dags(retrieval_filter=AirflowFilter())
    assert len(dag_infos) == 1
    assert dag_infos[0].dag_id == "print_dag"
    # Required for source code fetching
    assert "file_token" in dag_infos[0].metadata
    source_code = instance.get_dag_source_code(dag_infos[0])
    assert "print_hello()" in source_code
    # Attempt a nonexistent file token
    with pytest.raises(DagsterError, match="Failed to fetch source code."):
        instance.get_dag_source_code(
            DagInfo(dag_id="nonexistent", webserver_url=AIRFLOW_BASE_URL, metadata={"file_token": "nonexistent"})
        )

    task_info = instance.get_task_info(dag_id="print_dag", task_id="print_task")
    assert task_info.dag_id == "print_dag"
    assert task_info.task_id == "print_task"
    assert_link_exists("Dag url from task info object", task_info.dag_url)

    task_infos = instance.get_task_infos(dag_id="print_dag")
    assert len(task_infos) == 2

    task_dict = {task_info.task_id: task_info for task_info in task_infos}
    assert set(task_dict.keys()) == {"print_task", "downstream_print_task"}
    assert task_dict["print_task"].dag_id == "print_dag"
    assert task_dict["print_task"].task_id == "print_task"
    assert task_dict["downstream_print_task"].dag_id == "print_dag"
    assert task_dict["downstream_print_task"].task_id == "downstream_print_task"
    assert task_dict["print_task"].downstream_task_ids == ["downstream_print_task"]

    task_info = instance.get_task_info(dag_id="print_dag", task_id="downstream_print_task")
    assert task_info.dag_id == "print_dag"
    assert task_info.task_id == "downstream_print_task"
    assert_link_exists("Dag url from task info object", task_info.dag_url)

    # Attempt a nonexistent task
    with pytest.raises(
        DagsterError, match="Failed to fetch task info for print_dag/nonexistent_task."
    ):
        instance.get_task_info(dag_id="print_dag", task_id="nonexistent_task")

    # Kick off a run of the dag.
    run_id = instance.trigger_dag(dag_id="print_dag")
    instance.wait_for_run_completion(dag_id="print_dag", run_id=run_id)
    run = instance.get_dag_run(dag_id="print_dag", run_id=run_id)

    assert run.run_id == run_id
    assert_link_exists("Dag run", run.url)

    assert run.finished
    assert run.success
    assert isinstance(run.start_date, datetime.datetime)
    assert isinstance(run.end_date, datetime.datetime)
    # On Airflow 2, the logical date is automatically assigned. In Airflow 3, it is not.
    if is_airflow_2():
        assert isinstance(run.logical_date, datetime.datetime)
    else:
        assert run.logical_date is None

    # Fetch task instance
    task_instance = instance.get_task_instance(
        dag_id="print_dag", task_id="print_task", run_id=run_id
    )
    assert_link_exists("Task instance", task_instance.details_url)
    assert_link_exists("Task logs", task_instance.log_url)

    assert isinstance(task_instance.start_date, datetime.datetime)
    assert isinstance(task_instance.end_date, datetime.datetime)
    assert isinstance(task_instance.note, str)
    if is_airflow_2():
        assert isinstance(task_instance.logical_date, datetime.datetime)
        assert run.logical_date == task_instance.logical_date
    else:
        assert task_instance.logical_date is None
