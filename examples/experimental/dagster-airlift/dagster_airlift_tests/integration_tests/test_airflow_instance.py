import pytest
from dagster._core.errors import DagsterError
from dagster_airlift.core import AirflowInstance, BasicAuthBackend


def test_airflow_instance(airflow_instance: None):
    """Test AirflowInstance APIs against live-running airflow.

    Airflow is loaded with one dag (print_dag) which contains two tasks (print_task, downstream_print_task).
    """
    instance = AirflowInstance(
        auth_backend=BasicAuthBackend(
            webserver_url="http://localhost:8080", username="admin", password="admin"
        ),
        name="airflow_instance",
    )
    dag_infos = instance.list_dags()
    assert len(dag_infos) == 1
    assert dag_infos[0].dag_id == "print_dag"
    # Required for source code fetching
    assert "file_token" in dag_infos[0].metadata
    source_code = instance.get_dag_source_code(dag_infos[0].metadata["file_token"])
    assert "print_hello()" in source_code
    # Attempt a nonexistent file token
    with pytest.raises(DagsterError, match="Failed to fetch source code."):
        instance.get_dag_source_code("nonexistent")

    task_info = instance.get_task_info(dag_id="print_dag", task_id="print_task")
    assert task_info.dag_id == "print_dag"
    assert task_info.task_id == "print_task"

    task_info = instance.get_task_info(dag_id="print_dag", task_id="downstream_print_task")
    assert task_info.dag_id == "print_dag"
    assert task_info.task_id == "downstream_print_task"

    # Attempt a nonexistent task
    with pytest.raises(
        DagsterError, match="Failed to fetch task info for print_dag/nonexistent_task."
    ):
        instance.get_task_info(dag_id="print_dag", task_id="nonexistent_task")

    assert (
        instance.get_task_url(dag_id="print_dag", task_id="print_task")
        == "http://localhost:8080/dags/print_dag/print_task"
    )
    assert instance.get_dag_url(dag_id="print_dag") == "http://localhost:8080/dags/print_dag"
    assert (
        instance.get_dag_run_url(dag_id="print_dag", run_id="run_id")
        == "http://localhost:8080/dags/print_dag/grid?dag_run_id=run_id&tab=details"
    )
