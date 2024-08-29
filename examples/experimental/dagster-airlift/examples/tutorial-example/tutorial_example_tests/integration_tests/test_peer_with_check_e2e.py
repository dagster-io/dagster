import time
from pathlib import Path

import pytest
from dagster import AssetKey, DagsterInstance
from dagster._core.definitions.asset_key import AssetCheckKey
from dagster._core.storage.asset_check_execution_record import AssetCheckExecutionRecordStatus
from dagster._core.storage.dagster_run import DagsterRunStatus

from .utils import start_run_and_wait_for_completion


@pytest.fixture(name="dagster_defs_path")
def setup_dagster_defs_path(makefile_dir: Path) -> str:
    return str(makefile_dir / "tutorial_example" / "dagster_defs" / "stages" / "peer_with_check.py")


def test_peer_reflects_dag_completion_status_and_runs_check(
    airflow_instance: None, dagster_dev: None
) -> None:
    instance = DagsterInstance.get()

    mat_event = instance.get_latest_materialization_event(
        AssetKey(["airflow_instance", "dag", "rebuild_customers_list"])
    )
    assert mat_event is None

    start_run_and_wait_for_completion("rebuild_customers_list")

    time.sleep(10)

    mat_event = instance.get_latest_materialization_event(
        AssetKey(["airflow_instance", "dag", "rebuild_customers_list"])
    )
    assert mat_event is not None

    # Ensure check runs on the peered DAG
    runs = instance.get_runs()
    assert len(runs) == 1

    check_run = runs[0]
    assert check_run.status == DagsterRunStatus.SUCCESS

    assert (
        instance.get_latest_asset_check_evaluation_record(
            AssetCheckKey(
                asset_key=AssetKey(["airflow_instance", "dag", "rebuild_customers_list"]),
                name="validate_exported_csv",
            )
        ).status  # type: ignore
        == AssetCheckExecutionRecordStatus.SUCCEEDED
    )
