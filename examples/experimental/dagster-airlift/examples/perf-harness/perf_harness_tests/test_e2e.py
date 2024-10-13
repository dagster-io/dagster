import os
from datetime import timedelta
from typing import Callable, List, Tuple

import pytest
from dagster import AssetKey, DagsterInstance
from dagster._time import get_current_datetime
from dagster_airlift.core.airflow_instance import AirflowInstance


@pytest.fixture(name="dagster_home")
def dagster_home_fixture(local_env: None) -> str:
    return os.environ["DAGSTER_HOME"]


@pytest.fixture(name="module_and_instance")
def module_and_instance_fixture(request) -> str:
    return request.param


@pytest.fixture(name="dagster_dev_cmd")
def dagster_dev_cmd_fixture(module_and_instance: Tuple) -> List[str]:
    module, instance = module_and_instance
    return ["dagster", "dev", "-m", module, "-p", "3333"]


def peer_instance() -> AirflowInstance:
    from perf_harness.dagster_defs.peer import airflow_instance as af_instance_peer

    return af_instance_peer


def observe_instance() -> AirflowInstance:
    from perf_harness.dagster_defs.observe import airflow_instance as af_instance_observe

    return af_instance_observe


def migrate_instance() -> AirflowInstance:
    from perf_harness.dagster_defs.migrate import airflow_instance as af_instance_migrate

    return af_instance_migrate


@pytest.mark.parametrize(
    "module_and_instance",
    [
        ("perf_harness.dagster_defs.peer", peer_instance),
        ("perf_harness.dagster_defs.observe", observe_instance),
        ("perf_harness.dagster_defs.migrate", migrate_instance),
    ],
    ids=["peer", "observe", "migrate"],
    indirect=True,
)
def test_dagster_materializes(
    airflow_instance: None,
    dagster_dev: None,
    dagster_home: str,
    module_and_instance: Tuple[str, Callable[[], AirflowInstance]],
) -> None:
    """Test that assets can load properly, and that materializations register."""
    module, instance_fn = module_and_instance
    af_instance = instance_fn()
    run_id = af_instance.trigger_dag("dag_0")
    af_instance.wait_for_run_completion(dag_id="dag_0", run_id=run_id, timeout=60)
    dagster_instance = DagsterInstance.get()
    start_time = get_current_datetime()
    while get_current_datetime() - start_time < timedelta(seconds=60):
        asset_materialization = dagster_instance.get_latest_materialization_event(
            asset_key=AssetKey(["my_airflow_instance", "dag", "dag_0"])
        )
        if asset_materialization:
            break

    assert asset_materialization, "Could not find asset materialization for asset dag key"

    if module.endswith("observe") or module.endswith("migrate"):
        asset_materialization = dagster_instance.get_latest_materialization_event(
            asset_key=AssetKey(["task_0_0_asset_0"])
        )
        assert asset_materialization
