import os
import subprocess
from datetime import timedelta
from typing import Any, Callable, Generator, List, Tuple

import pytest
from dagster import AssetKey, AssetsDefinition, DagsterInstance, materialize
from dagster._core.test_utils import environ
from dagster._time import get_current_datetime
from dagster_airlift.core import AirflowInstance
from dagster_airlift.test.shared_fixtures import stand_up_airflow, stand_up_dagster

from dbt_example_tests.integration_tests.conftest import makefile_dir


def make_unmigrated() -> None:
    subprocess.check_output(["make", "not_proxied", "-C", str(makefile_dir())])


@pytest.fixture(name="local_env")
def local_env_fixture() -> Generator[None, None, None]:
    subprocess.run(["make", "setup_local_env"], cwd=makefile_dir(), check=True)
    with environ(
        {
            "AIRFLOW_HOME": str(makefile_dir() / ".federated_airflow_home"),
            "DBT_PROJECT_DIR": str(makefile_dir() / "dbt_example" / "shared" / "dbt"),
            "DAGSTER_HOME": str(makefile_dir() / ".dagster_home"),
        }
    ):
        yield
    subprocess.run(["make", "wipe"], cwd=makefile_dir(), check=True)


@pytest.fixture(name="dagster_home")
def dagster_home_fixture(local_env: None) -> str:
    return os.environ["DAGSTER_HOME"]


@pytest.fixture(name="stage_and_fn")
def stage_and_fn_fixture(request) -> Tuple[str, Callable[[], AirflowInstance]]:
    return request.param


@pytest.fixture(name="dagster_dev_cmd")
def dagster_dev_cmd_fixture(stage_and_fn: Tuple[str, Callable[[], AirflowInstance]]) -> List[str]:
    dagster_dev_module = stage_and_fn[0]
    if dagster_dev_module.endswith("federated_airflow_defs"):
        cmd = ["make", "run_federated_airflow_defs"]
    else:
        raise ValueError(f"Unknown stage: {dagster_dev_module}")
    return cmd + ["-C", str(makefile_dir())]


@pytest.fixture(name="federated_airflow_instance")
def federated_airflow_instance_fixture(local_env: None) -> Generator[subprocess.Popen, None, None]:
    with stand_up_airflow(
        airflow_cmd=["make", "run_federated_airflow"], env=os.environ, cwd=makefile_dir(), port=8081
    ) as process:
        yield process


@pytest.fixture(name="dagster_dev")
def setup_dagster(
    federated_airflow_instance: None, dagster_home: str, dagster_dev_cmd: List[str]
) -> Generator[Any, None, None]:
    with stand_up_dagster(dagster_dev_cmd) as process:
        yield process


def federated_airflow_instance() -> AirflowInstance:
    from dbt_example.dagster_defs.federated_airflow import airflow_instance as af_instance

    return af_instance


@pytest.mark.parametrize(
    "stage_and_fn",
    [
        ("federated_airflow_defs", federated_airflow_instance),
    ],
    ids=["federated_airflow_defs"],
    indirect=True,
)
def test_dagster_materializes(
    federated_airflow_instance: None,
    dagster_dev: None,
    dagster_home: str,
    stage_and_fn: Tuple[str, Callable[[], AirflowInstance]],
) -> None:
    """Test that assets can load properly, and that materializations register."""
    # Attempt to run all original completed assets.
    from dbt_example.dagster_defs.federated_airflow_defs import defs

    assert defs.assets
    materializable_assets = [
        asset
        for asset in defs.assets
        if isinstance(asset, AssetsDefinition) and asset.is_executable
    ]
    instance = DagsterInstance.get()
    result = materialize(materializable_assets, instance=instance, resources=defs.resources)
    assert result.success
    for asset in materializable_assets:
        for spec in asset.specs:
            assert instance.get_latest_materialization_event(asset_key=spec.key)
    dagster_dev_module, af_instance_fn = stage_and_fn
    af_instance = af_instance_fn()
    for dag_id in ["upload_seeds", "run_scrapers_daily"]:
        run_id = af_instance.trigger_dag(dag_id=dag_id)
        af_instance.wait_for_run_completion(dag_id=dag_id, run_id=run_id, timeout=60)
        dagster_instance = DagsterInstance.get()
        start_time = get_current_datetime()
        while get_current_datetime() - start_time < timedelta(seconds=30):
            asset_materialization = dagster_instance.get_latest_materialization_event(
                asset_key=AssetKey(["my_federated_airflow_instance", "dag", dag_id])
            )
            if asset_materialization:
                break

        assert asset_materialization
