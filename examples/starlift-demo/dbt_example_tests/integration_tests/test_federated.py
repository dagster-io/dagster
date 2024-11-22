import os
import subprocess
from datetime import timedelta
from typing import Any, Callable, Generator, List, Mapping, Tuple

import pytest
from dagster import AssetKey, AssetsDefinition, DagsterInstance, materialize
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.test_utils import environ
from dagster._time import get_current_datetime
from dagster_airlift.core import AirflowInstance
from dagster_airlift.test.shared_fixtures import stand_up_airflow, stand_up_dagster
from dbt_example.dagster_defs.constants import (
    LEGACY_FEDERATED_INSTANCE_NAME,
    OTHER_TEAM_FEDERATED_INSTANCE_NAME,
)

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
def stage_and_fn_fixture(request) -> tuple[str, Callable[[], AirflowInstance]]:
    return request.param


@pytest.fixture(name="dagster_dev_cmd")
def dagster_dev_cmd_fixture(stage_and_fn: tuple[str, Callable[[], AirflowInstance]]) -> list[str]:
    dagster_dev_module = stage_and_fn[0]
    if dagster_dev_module.endswith("federated_airflow_defs_1"):
        cmd = ["make", "run_federated_airflow_defs_1"]
    elif dagster_dev_module.endswith("federated_airflow_defs_2"):
        cmd = ["make", "run_federated_airflow_defs_2"]
    elif dagster_dev_module.endswith("dbt_cloud_airflow"):
        cmd = ["make", "run_dbt_cloud_defs"]
    else:
        raise ValueError(f"Unknown stage: {dagster_dev_module}")
    return cmd + ["-C", str(makefile_dir())]


@pytest.fixture(name="federated_airflow_instance_1")
def federated_airflow_instance_1_fixture(
    local_env: None,
) -> Generator[subprocess.Popen, None, None]:
    with stand_up_airflow(
        airflow_cmd=["make", "run_federated_airflow_1"],
        env=os.environ,
        cwd=makefile_dir(),
        port=8081,
    ) as process:
        yield process


@pytest.fixture(name="federated_airflow_instance_2")
def federated_airflow_instance_2_fixture(
    local_env: None,
) -> Generator[subprocess.Popen, None, None]:
    with stand_up_airflow(
        airflow_cmd=["make", "run_federated_airflow_2"],
        env=os.environ,
        cwd=makefile_dir(),
        port=8081,
    ) as process:
        yield process


@pytest.fixture(name="dagster_dev")
def setup_dagster(
    federated_airflow_instance_1: None,
    federated_airflow_instance_2: None,
    dagster_home: str,
    dagster_dev_cmd: list[str],
) -> Generator[Any, None, None]:
    with stand_up_dagster(dagster_dev_cmd) as process:
        yield process


def federated_airflow_instances_1() -> Mapping[str, AirflowInstance]:
    from dbt_example.dagster_defs.federated_airflow_1 import airflow_instance as af_instance

    return {af_instance.name: af_instance}


def federated_airflow_instances_2() -> Mapping[str, AirflowInstance]:
    from dbt_example.dagster_defs.federated_airflow_1 import airflow_instance as af_instance_1
    from dbt_example.dagster_defs.federated_airflow_2 import airflow_instance as af_instance_2

    return {af_instance_1.name: af_instance_1, af_instance_2.name: af_instance_2}


def get_federated_1_defs() -> Definitions:
    from dbt_example.dagster_defs.federated_airflow_defs_1 import defs

    return defs


def get_federated_2_defs() -> Definitions:
    from dbt_example.dagster_defs.federated_airflow_defs_2 import defs

    return defs


def get_dbt_cloud_defs() -> Definitions:
    from dbt_example.dagster_defs.dbt_cloud_airflow import defs

    return defs


@pytest.mark.parametrize(
    "stage_and_fn",
    [
        ("federated_airflow_defs_1", federated_airflow_instances_1),
        ("federated_airflow_defs_2", federated_airflow_instances_2),
        ("dbt_cloud_airflow", federated_airflow_instances_2),
    ],
    ids=["federated_airflow_defs_1", "federated_airflow_defs_2", "dbt_cloud_airflow"],
    indirect=True,
)
def test_dagster_materializes(
    federated_airflow_instance_1: None,
    federated_airflow_instance_2: None,
    dagster_dev: None,
    dagster_home: str,
    stage_and_fn: tuple[str, Callable[[], Mapping[str, AirflowInstance]]],
) -> None:
    """Test that assets can load properly, and that materializations register."""
    # Attempt to run all original completed assets.
    if stage_and_fn[0] == "federated_airflow_defs_1":
        defs = get_federated_1_defs()
    elif stage_and_fn[0] == "federated_airflow_defs_2":
        defs = get_federated_2_defs()
    elif stage_and_fn[0] == "dbt_cloud_airflow":
        defs = get_dbt_cloud_defs()
    else:
        raise ValueError(f"Unknown stage: {stage_and_fn[0]}")

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
    af_instances = af_instance_fn()
    dags_per_instance = {
        OTHER_TEAM_FEDERATED_INSTANCE_NAME: ["upload_source_data", "run_scrapers_daily"],
        LEGACY_FEDERATED_INSTANCE_NAME: ["upload_raw_iris", "run_telemetry_job"],
    }
    for af_instance in af_instances.values():
        for dag_id in dags_per_instance[af_instance.name]:
            run_id = af_instance.trigger_dag(dag_id=dag_id)
            af_instance.wait_for_run_completion(dag_id=dag_id, run_id=run_id, timeout=60)
            dagster_instance = DagsterInstance.get()
            start_time = get_current_datetime()
            while get_current_datetime() - start_time < timedelta(seconds=30):
                asset_materialization = dagster_instance.get_latest_materialization_event(
                    asset_key=AssetKey([af_instance.name, "dag", dag_id])
                )
                if asset_materialization:
                    break

        assert asset_materialization
