import time
from pathlib import Path

import pytest
import requests
from dagster import AssetKey, DagsterInstance, DagsterRunStatus
from dagster._core.test_utils import environ
from dagster_airlift.constants import DAG_RUN_ID_TAG_KEY


@pytest.fixture(name="dags_dir")
def dags_dir() -> Path:
    return Path(__file__).parent / "operator_test_project" / "dags"


@pytest.fixture(name="dagster_defs_path")
def dagster_defs_path_fixture() -> str:
    return str(Path(__file__).parent / "operator_test_project" / "dagster_defs.py")


@pytest.mark.timeout(180)
def test_dagster_operator(airflow_instance: None, dagster_dev: None, dagster_home: str) -> None:
    """Tests that dagster operator can correctly map airflow tasks to dagster tasks, and kick off executions."""
    response = requests.post(
        "http://localhost:8080/api/v1/dags/the_dag/dagRuns", auth=("admin", "admin"), json={}
    )
    assert response.status_code == 200, response.json()
    # Poll until the run enters a terminal state. The outer pytest-timeout
    # marker is the safety net for a truly stuck run.
    while True:
        response = requests.get(
            "http://localhost:8080/api/v1/dags/the_dag/dagRuns", auth=("admin", "admin")
        )
        assert response.status_code == 200, response.json()
        dag_runs = response.json()["dag_runs"]
        if dag_runs[0]["state"] in ["success", "failed"]:
            terminal_status = dag_runs[0]["state"]
            dag_run = dag_runs[0]
            break
        time.sleep(1)
    assert terminal_status == "success", f"terminal status was {terminal_status}"
    with environ({"DAGSTER_HOME": dagster_home}):
        instance = DagsterInstance.get()
        runs = instance.get_runs()
        # The graphql endpoint kicks off a run for each of the tasks in the dag
        assert len(runs) == 2
        some_task_run = [  # noqa
            run
            for run in runs
            if set(list(run.asset_selection)) == {AssetKey(["the_dag__other_task"])}  # type: ignore
        ][0]
        other_task_run = [  # noqa
            run
            for run in runs
            if set(list(run.asset_selection)) == {AssetKey(["the_dag__some_task"])}  # type: ignore
        ][0]
        assert some_task_run.status == DagsterRunStatus.SUCCESS
        assert other_task_run.status == DagsterRunStatus.SUCCESS

        assert isinstance(dag_run, dict)
        assert "dag_run_id" in dag_run
        assert some_task_run.tags[DAG_RUN_ID_TAG_KEY] == dag_run["dag_run_id"]
        assert other_task_run.tags[DAG_RUN_ID_TAG_KEY] == dag_run["dag_run_id"]
