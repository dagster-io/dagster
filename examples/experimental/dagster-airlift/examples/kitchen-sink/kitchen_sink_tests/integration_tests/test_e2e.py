import os
from datetime import timedelta
from typing import List

import pytest
from dagster import AssetKey, DagsterInstance
from dagster._time import get_current_datetime

from kitchen_sink_tests.integration_tests.conftest import makefile_dir


@pytest.fixture(name="dagster_home")
def dagster_home_fixture(local_env: None) -> str:
    return os.environ["DAGSTER_HOME"]


@pytest.fixture(name="dagster_dev_cmd")
def dagster_dev_cmd_fixture() -> List[str]:
    return ["make", "run_dagster", "-C", str(makefile_dir())]


expected_mats_per_dag = {
    "print_dag": [AssetKey("print_asset")],
}


def test_dagster_materializes(
    airflow_instance: None,
    dagster_dev: None,
    dagster_home: str,
) -> None:
    """Test that assets can load properly, and that materializations register."""
    from kitchen_sink.dagster_defs import airflow_instance as af_instance

    for dag_id, expected_asset_keys in expected_mats_per_dag.items():
        run_id = af_instance.trigger_dag(dag_id=dag_id)
        af_instance.wait_for_run_completion(dag_id=dag_id, run_id=run_id, timeout=60)
        dagster_instance = DagsterInstance.get()
        start_time = get_current_datetime()
        while get_current_datetime() - start_time < timedelta(seconds=30):
            asset_materialization = dagster_instance.get_latest_materialization_event(
                asset_key=AssetKey(["airflow_instance", "dag", dag_id])
            )
            if asset_materialization:
                break

        assert asset_materialization

        for expected_asset_key in expected_asset_keys:
            asset_materialization = dagster_instance.get_latest_materialization_event(
                asset_key=expected_asset_key
            )
            assert asset_materialization
