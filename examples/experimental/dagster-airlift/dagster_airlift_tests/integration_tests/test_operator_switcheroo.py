import time
from pathlib import Path

import pytest
import requests
from dagster import AssetKey, DagsterInstance, DagsterRunStatus
from dagster._time import get_current_timestamp


# Two different test targets
# The first uses convention-based binding of assets to tasks, e.g.
# op named the_dag__some_task
# The second uses `dag_defs` and `task_defs` to attach tags to assets, which
# in turn are used to bind assets to tasks.
@pytest.fixture(
    name="test_dir",
    params=[
        "airflow_op_switcheroo_convention",
        "airflow_op_switcheroo_tags",
    ],
)
def test_dir_fixture(request: pytest.FixtureRequest) -> Path:
    return Path(__file__).parent / request.param


@pytest.fixture(name="dags_dir")
def setup_dags_dir(test_dir: Path) -> Path:
    return test_dir / "dags"


@pytest.fixture(name="dagster_defs_path")
def setup_dagster_defs_path(test_dir: Path) -> str:
    return str(test_dir / "dagster_defs.py")


def test_migrated_operator(airflow_instance: None, dagster_dev: None) -> None:
    """Tests that dagster migrated operator can correctly map airflow tasks to dagster tasks, and kick off executions."""
    response = requests.post(
        "http://localhost:8080/api/v1/dags/the_dag/dagRuns", auth=("admin", "admin"), json={}
    )
    assert response.status_code == 200, response.json()
    # Wait until the run enters a terminal state
    terminal_status = None
    start_time = get_current_timestamp()
    while get_current_timestamp() - start_time < 30:
        response = requests.get(
            "http://localhost:8080/api/v1/dags/the_dag/dagRuns", auth=("admin", "admin")
        )
        assert response.status_code == 200, response.json()
        dag_runs = response.json()["dag_runs"]
        if dag_runs[0]["state"] in ["success", "failed"]:
            terminal_status = dag_runs[0]["state"]
            break
        time.sleep(1)
    assert terminal_status == "success", (
        "Never reached terminal status"
        if terminal_status is None
        else f"terminal status was {terminal_status}"
    )
    # DAGSTER_HOME already set in environment, so instance should be retrievable.
    instance = DagsterInstance.get()
    runs = instance.get_runs()
    # The graphql endpoint kicks off a run for each of the tasks in the dag
    assert len(runs) == 1
    some_task_run = [  # noqa
        run
        for run in runs
        if set(list(run.asset_selection)) == {AssetKey(["the_dag__some_task"])}  # type: ignore
        or set(list(run.asset_selection)) == {AssetKey(["my_asset_for_some_task"])}  # type: ignore
    ][0]
    assert some_task_run.status == DagsterRunStatus.SUCCESS
