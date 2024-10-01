from pathlib import Path

import pytest
from dagster import AssetKey, DagsterInstance
from dagster._core.definitions.asset_key import AssetCheckKey
from dagster._core.storage.asset_check_execution_record import AssetCheckExecutionRecordStatus
from dagster._core.storage.dagster_run import DagsterRunStatus

from .utils import poll_for_asset_check, poll_for_materialization, start_run_and_wait_for_completion


@pytest.fixture(name="dagster_defs_path")
def setup_dagster_defs_path(
    makefile_dir: Path,
    local_env,
) -> str:
    return str(makefile_dir / "tutorial_example" / "dagster_defs" / "stages" / "peer_with_check.py")


@pytest.mark.skip(reason="Flakiness, @benpankow to investigate")
def test_peer_reflects_dag_completion_status_and_runs_check(
    airflow_instance: None, dagster_dev: None
) -> None:
    instance = DagsterInstance.get()

    mat_event = instance.get_latest_materialization_event(
        AssetKey(["airflow_instance_one", "dag", "rebuild_customers_list"])
    )
    assert mat_event is None

    start_run_and_wait_for_completion("rebuild_customers_list")

    poll_for_materialization(
        instance, target=AssetKey(["airflow_instance_one", "dag", "rebuild_customers_list"])
    )

    check_key = AssetCheckKey(
        asset_key=AssetKey(["airflow_instance_one", "dag", "rebuild_customers_list"]),
        name="validate_exported_csv",
    )
    check_result = poll_for_asset_check(instance, target=check_key)

    # Ensure check runs on the peered DAG
    runs = instance.get_runs()
    assert len(runs) == 1

    check_run = runs[0]
    assert check_run.status == DagsterRunStatus.SUCCESS

    assert check_result.status == AssetCheckExecutionRecordStatus.SUCCEEDED
