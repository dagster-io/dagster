import os
import subprocess
from datetime import timedelta
from typing import Callable, List, Tuple

import pytest
from dagster import AssetKey, DagsterInstance
from dagster._time import get_current_datetime
from dagster_airlift.core import AirflowInstance

from dbt_example_tests.integration_tests.conftest import makefile_dir


def make_unmigrated() -> None:
    subprocess.check_output(["make", "not_proxied", "-C", str(makefile_dir())])


@pytest.fixture(name="dagster_home")
def dagster_home_fixture(local_env: None) -> str:
    return os.environ["DAGSTER_HOME"]


@pytest.fixture(name="stage_and_fn")
def stage_and_fn_fixture(request) -> Tuple[str, Callable[[], AirflowInstance]]:
    return request.param


@pytest.fixture(name="dagster_dev_cmd")
def dagster_dev_cmd_fixture(stage_and_fn: Tuple[str, Callable[[], AirflowInstance]]) -> List[str]:
    dagster_dev_module = stage_and_fn[0]
    if dagster_dev_module.endswith("peer"):
        cmd = ["make", "run_peer"]
    elif dagster_dev_module.endswith("observe"):
        cmd = ["make", "run_observe"]
    else:
        cmd = ["make", "run_migrate"]
    return cmd + ["-C", str(makefile_dir())]


def peer_instance() -> AirflowInstance:
    from dbt_example.dagster_defs.peer import airflow_instance as af_instance_peer

    return af_instance_peer


def observe_instance() -> AirflowInstance:
    from dbt_example.dagster_defs.observe import airflow_instance as af_instance_observe

    return af_instance_observe


def observe_with_check_instance() -> AirflowInstance:
    from dbt_example.dagster_defs.observe_with_check import (
        airflow_instance as af_instance_observe_with_check,
    )

    return af_instance_observe_with_check


def migrate_instance() -> AirflowInstance:
    from dbt_example.dagster_defs.migrate import airflow_instance as af_instance_migrate

    return af_instance_migrate


@pytest.mark.parametrize(
    "stage_and_fn",
    [
        ("peer", peer_instance),
        ("observe", observe_instance),
        ("observe_with_check", observe_with_check_instance),
        ("migrate", migrate_instance),
    ],
    ids=["peer", "observe", "observe_with_check", "migrate"],
    indirect=True,
)
def test_dagster_materializes(
    airflow_instance: None,
    dagster_dev: None,
    dagster_home: str,
    stage_and_fn: Tuple[str, Callable[[], AirflowInstance]],
) -> None:
    """Test that assets can load properly, and that materializations register."""
    dagster_dev_module, af_instance_fn = stage_and_fn
    if dagster_dev_module.endswith("peer"):
        make_unmigrated()
    af_instance = af_instance_fn()
    for dag_id, expected_asset_key in [("rebuild_iris_models", AssetKey(["lakehouse", "iris"]))]:
        run_id = af_instance.trigger_dag(dag_id=dag_id)
        af_instance.wait_for_run_completion(dag_id=dag_id, run_id=run_id, timeout=60)
        dagster_instance = DagsterInstance.get()
        start_time = get_current_datetime()
        while get_current_datetime() - start_time < timedelta(seconds=30):
            asset_materialization = dagster_instance.get_latest_materialization_event(
                asset_key=AssetKey(["my_airflow_instance", "dag", dag_id])
            )
            if asset_materialization:
                break

        assert asset_materialization

        if dagster_dev_module.endswith("observe") or dagster_dev_module.endswith("migrate"):
            asset_materialization = dagster_instance.get_latest_materialization_event(
                asset_key=expected_asset_key
            )
            assert asset_materialization
