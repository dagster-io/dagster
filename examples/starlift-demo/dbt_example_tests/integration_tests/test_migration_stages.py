import enum
import os
import subprocess
from datetime import timedelta

import pytest
from dagster import AssetKey, DagsterInstance
from dagster._time import get_current_datetime
from dbt_example.dagster_defs.utils import get_airflow_instance

from dbt_example_tests.integration_tests.conftest import makefile_dir

DAG_ID = "rebuild_iris_models"
REBUILD_IRIS_MODELS_DAG_KEY = AssetKey(["my_airflow_instance", "dag", DAG_ID])


class MigrationStage(enum.Enum):
    PEER = "PEER"
    OBSERVE = "OBSERVE"
    MIGRATE = "MIGRATE"
    OBSERVE_WITH_CHECK = "OBSERVE_WITH_CHECK"

    @property
    def as_cmd(self) -> list[str]:
        if self == MigrationStage.PEER:
            cmd = ["make", "run_peer"]
        elif self == MigrationStage.OBSERVE:
            cmd = ["make", "run_observe"]
        else:
            cmd = ["make", "run_migrate"]
        return cmd + ["-C", str(makefile_dir())]

    @property
    def test_id(self) -> str:
        return self.value.lower()

    @property
    def expected_asset_keys(self) -> list[AssetKey]:
        return [] if self == MigrationStage.PEER else [AssetKey(["lakehouse", "iris"])]


def make_unmigrated() -> None:
    subprocess.check_output(["make", "not_proxied", "-C", str(makefile_dir())])


@pytest.fixture(name="dagster_home")
def dagster_home_fixture(local_env: None) -> str:
    return os.environ["DAGSTER_HOME"]


@pytest.fixture(name="stage")
def stage_fixture(request) -> MigrationStage:
    return request.param


@pytest.fixture(name="dagster_dev_cmd")
def dagster_dev_cmd_fixture(stage: MigrationStage) -> list[str]:
    return stage.as_cmd


@pytest.mark.parametrize(
    "stage",
    [stage for stage in MigrationStage],
    ids=[stage.test_id for stage in MigrationStage],
    indirect=True,
)
def test_dagster_materializes(
    airflow_instance: None,
    dagster_dev: None,
    dagster_home: str,
    stage: MigrationStage,
) -> None:
    """Test that assets can load properly, and that materializations register."""
    af_instance = get_airflow_instance()
    run_id = af_instance.trigger_dag(dag_id=DAG_ID)
    af_instance.wait_for_run_completion(dag_id=DAG_ID, run_id=run_id, timeout=60)
    dagster_instance = DagsterInstance.get()
    start_time = get_current_datetime()
    while get_current_datetime() - start_time < timedelta(seconds=30):
        asset_materialization = dagster_instance.get_latest_materialization_event(
            asset_key=REBUILD_IRIS_MODELS_DAG_KEY
        )
        if asset_materialization:
            break

    assert asset_materialization  # pyright: ignore[reportPossiblyUnboundVariable]

    for expected_asset_key in stage.expected_asset_keys:
        asset_materialization = dagster_instance.get_latest_materialization_event(
            asset_key=expected_asset_key
        )
        assert asset_materialization
