import pytest
from dagster import AssetCheckKey, AssetKey, Definitions, asset, asset_check
from dagster._core.errors import DagsterError
from dagster_airlift.core import AirflowInstance, BasicAuthBackend, build_defs_from_airflow_instance

from .conftest import assert_link_exists


def test_airflow_instance(airflow_instance: None) -> None:
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
    assert_link_exists("Dag url from task info object", task_info.dag_url)

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

    # Fetch task instance
    task_instance = instance.get_task_instance(
        dag_id="print_dag", task_id="print_task", run_id=run_id
    )
    assert_link_exists("Task instance", task_instance.details_url)
    assert_link_exists("Task logs", task_instance.log_url)

    assert isinstance(task_instance.start_date, float)
    assert isinstance(task_instance.end_date, float)
    assert isinstance(task_instance.note, str)


def test_orchestrated_defs(airflow_instance: None) -> None:
    """Test allowing assets and asset checks to be passed through orchestrated defs without airflow mapping,
    and that they will be present in the ultimately created defs.
    """

    @asset
    def print_dag__print_task():
        pass

    @asset
    def not_orchestrated_in_airflow():
        pass

    @asset_check(asset=print_dag__print_task.key)
    def check_print_task():
        pass

    instance = AirflowInstance(
        auth_backend=BasicAuthBackend(
            webserver_url="http://localhost:8080", username="admin", password="admin"
        ),
        name="airflow_instance",
    )

    defs = build_defs_from_airflow_instance(
        airflow_instance=instance,
        orchestrated_defs=Definitions(
            assets=[print_dag__print_task, not_orchestrated_in_airflow],
            asset_checks=[check_print_task],
        ),
    ).get_repository_def()
    assert len(defs.assets_defs_by_key) == 3
    assert set(defs.assets_defs_by_key.keys()) == {
        AssetKey(["airflow_instance", "dag", "print_dag"]),
        AssetKey(["print_dag__print_task"]),
        AssetKey(["not_orchestrated_in_airflow"]),
    }
    assert len(defs.asset_checks_defs_by_key) == 1
    assert set(defs.asset_checks_defs_by_key.keys()) == {
        AssetCheckKey(name="check_print_task", asset_key=AssetKey(["print_dag__print_task"]))
    }
