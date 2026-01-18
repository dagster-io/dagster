import enum
import os
import subprocess

import pytest
from dagster import AssetKey, DagsterInstance
from dagster._core.storage.dagster_run import RunsFilter
from dagster._time import get_current_timestamp
from dagster_airlift.constants import DAG_RUN_ID_TAG_KEY
from dbt_example.dagster_defs.utils import get_airflow_instance

from dbt_example_tests.integration_tests.conftest import makefile_dir

DAG_ID = "rebuild_iris_models"
REBUILD_IRIS_MODELS_DAG_KEY = AssetKey(["my_airflow_instance", "dag", DAG_ID])


class MigrationStage(enum.Enum):
    PEER = "PEER"
    OBSERVE = "OBSERVE"
    MIGRATE = "MIGRATE"
    OBSERVE_WITH_CHECK = "OBSERVE_WITH_CHECK"
    PEER_COMPONENT = "PEER_COMPONENT"
    OBSERVE_COMPONENT = "OBSERVE_COMPONENT"
    MIGRATE_COMPONENT = "MIGRATE_COMPONENT"

    @property
    def as_cmd(self) -> list[str]:
        if self == MigrationStage.PEER:
            cmd = ["make", "run_peer"]
        elif self == MigrationStage.OBSERVE:
            cmd = ["make", "run_observe"]
        elif self == MigrationStage.MIGRATE:
            cmd = ["make", "run_migrate"]
        elif self == MigrationStage.OBSERVE_WITH_CHECK:
            cmd = ["make", "run_observe_with_check"]
        elif self == MigrationStage.PEER_COMPONENT:
            cmd = ["make", "run_peer_component"]
        elif self == MigrationStage.OBSERVE_COMPONENT:
            cmd = ["make", "run_observe_component"]
        elif self == MigrationStage.MIGRATE_COMPONENT:
            cmd = ["make", "run_migrate_component"]
        else:
            raise ValueError(f"Unknown migration stage: {self}")
        return cmd + ["-C", str(makefile_dir())]

    @property
    def test_id(self) -> str:
        return self.value.lower()

    @property
    def is_component_stage(self) -> bool:
        return self in [
            MigrationStage.PEER_COMPONENT,
            MigrationStage.OBSERVE_COMPONENT,
            MigrationStage.MIGRATE_COMPONENT,
        ]

    def is_run_propagated(self, instance: DagsterInstance, dag_run_id: str) -> bool:
        if self.is_component_stage:
            return (
                instance.get_latest_materialization_event(asset_key=REBUILD_IRIS_MODELS_DAG_KEY)
                is not None
            )
        else:
            return (
                len(
                    instance.get_run_records(
                        filters=RunsFilter(tags={DAG_RUN_ID_TAG_KEY: dag_run_id})
                    )
                )
                > 0
            )

    def wait_for_run_propagation(
        self, instance: DagsterInstance, dag_run_id: str, timeout: int = 30
    ) -> None:
        start_timestamp = get_current_timestamp()
        while get_current_timestamp() - start_timestamp < timeout:
            if self.is_run_propagated(instance, dag_run_id):
                break

    @property
    def expected_asset_keys(self) -> list[AssetKey]:
        return (
            []
            if self == MigrationStage.PEER or self.is_component_stage
            else [AssetKey(["lakehouse", "iris"])]
        )


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
    stage.wait_for_run_propagation(instance=dagster_instance, dag_run_id=run_id)
