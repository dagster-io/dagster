from pathlib import Path

import pytest
from dagster import AssetKey, DagsterInstance, DagsterRunStatus
from dagster._core.test_utils import environ
from dagster_airlift.constants import DAG_RUN_ID_TAG_KEY, infer_af_version_from_env
from dagster_airlift.core.airflow_instance import AirflowInstance
from dagster_airlift.test.shared_fixtures import AIRFLOW_INSTANCE_NAME, get_backend


def _test_project_dir() -> Path:
    return Path(__file__).parent / "materialize_assets_operator_test_project"


@pytest.fixture(name="dags_dir")
def dags_dir() -> Path:
    return _test_project_dir() / "dags"


@pytest.fixture(name="dagster_defs_path")
def dagster_defs_path_fixture() -> str:
    return str(_test_project_dir() / "dagster_defs.py")


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
        # The graphql endpoint kicks off a run for each of the assets provided in the asset_key_paths. There are two assets,
        # but they exist within the same job, so there should only be 1 run.
        assert len(runs) == 1
        the_run = [  # noqa
            run
            for run in runs
            if set(list(run.asset_selection))  # type: ignore
            == {
                AssetKey(["some_asset"]),
                AssetKey(["other_asset"]),
                AssetKey(["nested", "asset"]),
                AssetKey(["string", "interpretation"]),
                AssetKey(["backslash/interpretation"]),
            }
        ][0]
        assert the_run.status == DagsterRunStatus.SUCCESS

        assert the_run.tags[DAG_RUN_ID_TAG_KEY] == dag_run.run_id
