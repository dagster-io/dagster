import os
from datetime import timedelta
from typing import List

import pytest
from dagster import AssetKey, DagsterInstance
from dagster._time import get_current_datetime
from perf_harness.dagster_defs.peer import airflow_instance as af_instance


@pytest.fixture(name="dagster_home")
def dagster_home_fixture(local_env: None) -> str:
    return os.environ["DAGSTER_HOME"]


@pytest.fixture(name="dagster_dev_module")
def dagster_dev_module_fixture(request) -> str:
    return request.param


@pytest.fixture(name="dagster_dev_cmd")
def dagster_dev_cmd_fixture(dagster_dev_module: str) -> List[str]:
    return ["dagster", "dev", "-m", dagster_dev_module, "-p", "3333"]


@pytest.mark.parametrize(
    "dagster_dev_module",
    [
        "perf_harness.dagster_defs.peer",
        "perf_harness.dagster_defs.observe",
        "perf_harness.dagster_defs.migrate",
    ],
    ids=["peer", "observe", "migrate"],
    indirect=True,
)
def test_dagster_materializes(
    airflow_instance: None, dagster_dev: None, dagster_home: str, dagster_dev_module: str
) -> None:
    """Test that assets can load properly, and that materializations register."""
    run_id = af_instance.trigger_dag("dag_0")
    af_instance.wait_for_run_completion(dag_id="dag_0", run_id=run_id)
    dagster_instance = DagsterInstance.get()
    start_time = get_current_datetime()
    while get_current_datetime() - start_time < timedelta(seconds=30):
        asset_materialization = dagster_instance.get_latest_materialization_event(
            asset_key=AssetKey(["airflow_instance", "dag", "dag_0"])
        )
        if asset_materialization:
            break

    assert asset_materialization

    if dagster_dev_module.endswith("observe") or dagster_dev_module.endswith("migrate"):
        asset_materialization = dagster_instance.get_latest_materialization_event(
            asset_key=AssetKey(["asset_0_0"])
        )
        assert asset_materialization
