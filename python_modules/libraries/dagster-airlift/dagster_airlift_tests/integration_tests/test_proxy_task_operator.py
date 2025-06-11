from pathlib import Path

import pytest
from dagster import AssetKey, DagsterInstance, DagsterRunStatus
from dagster._core.test_utils import environ
from dagster_airlift.constants import DAG_RUN_ID_TAG_KEY
from dagster_airlift.core import AirflowInstance
from dagster_airlift.test.shared_fixtures import (
    AIRFLOW_INSTANCE_NAME,
    get_backend,
    infer_af_version_from_env,
)


@pytest.fixture(name="dags_dir")
def dags_dir() -> Path:
    return Path(__file__).parent / "operator_test_project" / "dags"


@pytest.fixture(name="dagster_defs_path")
def dagster_defs_path_fixture() -> str:
    return str(Path(__file__).parent / "operator_test_project" / "dagster_defs.py")


def test_dagster_operator(airflow_instance: None, dagster_dev: None, dagster_home: str) -> None:
    """Tests that dagster operator can correctly map airflow tasks to dagster tasks, and kick off executions."""
    af_instance = AirflowInstance(
        auth_backend=get_backend(),
        name=AIRFLOW_INSTANCE_NAME,
        airflow_version=infer_af_version_from_env(),
    )
    dag_run_id = af_instance.trigger_dag(dag_id="the_dag")
    af_instance.wait_for_run_completion(dag_id="the_dag", run_id=dag_run_id)
    dag_run = af_instance.get_dag_run(dag_id="the_dag", run_id=dag_run_id)
    assert dag_run.success

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

        assert some_task_run.tags[DAG_RUN_ID_TAG_KEY] == dag_run.run_id
        assert other_task_run.tags[DAG_RUN_ID_TAG_KEY] == dag_run.run_id
