import time
from typing import Dict, List, Union, cast

import dagster._check as check
import requests
from dagster._core.definitions.asset_key import AssetCheckKey, AssetKey
from dagster._core.events.log import EventLogEntry
from dagster._core.instance import DagsterInstance
from dagster._core.storage.asset_check_execution_record import (
    AssetCheckExecutionRecord,
    AssetCheckExecutionRecordStatus,
)
from dagster._core.storage.dagster_run import DagsterRunStatus
from dagster._time import get_current_timestamp


def start_run_and_wait_for_completion(dag_id: str) -> None:
    response = requests.post(
        f"http://localhost:8080/api/v1/dags/{dag_id}/dagRuns",
        auth=("admin", "admin"),
        json={},
    )
    assert response.status_code == 200, response.json()
    # Wait until the run enters a terminal state
    terminal_status = None
    start_time = get_current_timestamp()
    while get_current_timestamp() - start_time < 30:
        response = requests.get(
            f"http://localhost:8080/api/v1/dags/{dag_id}/dagRuns",
            auth=("admin", "admin"),
        )
        assert response.status_code == 200, response.json()
        dag_runs = response.json()["dag_runs"]
        if dag_runs[0]["state"] in ["success", "failed"]:
            terminal_status = dag_runs[0]["state"]
            break
        time.sleep(1)
    assert terminal_status == "success", (
        "Never reached terminal status"
        if terminal_status is None
        else f"terminal status was {terminal_status}"
    )


def poll_for_materialization(
    instance: DagsterInstance,
    target: Union[AssetKey, List[AssetKey]],
    timeout: int = 60,
    poll_interval: int = 3,
) -> Dict[AssetKey, EventLogEntry]:
    """Polls the instance for materialization events for the given target(s) until all targets have been materialized or the timeout is reached."""
    target_list = [target] if isinstance(target, AssetKey) else target

    mat_events = instance.get_latest_materialization_events(asset_keys=target_list)

    total_time_elapsed = 0
    while not all(event is not None for event in mat_events.values()):
        time.sleep(poll_interval)
        total_time_elapsed += poll_interval
        if total_time_elapsed >= timeout:
            raise TimeoutError("Timed out waiting for materialization events")

        mat_events = instance.get_latest_materialization_events(asset_keys=target_list)

    return cast(Dict[AssetKey, EventLogEntry], mat_events)


def poll_for_asset_check(
    instance: DagsterInstance, target: AssetCheckKey, timeout: int = 60, poll_interval: int = 3
) -> AssetCheckExecutionRecord:
    """Polls the instance for asset check evaluation records for the given target until the target check has run or the timeout is reached."""
    evaluation = instance.get_latest_asset_check_evaluation_record(asset_check_key=target)

    total_time_elapsed = 0
    while (
        evaluation is None
        or evaluation.status
        not in (
            AssetCheckExecutionRecordStatus.SUCCEEDED,
            AssetCheckExecutionRecordStatus.FAILED,
        )
        or check.not_none(instance.get_run_by_id(evaluation.run_id)).status
        not in (
            DagsterRunStatus.SUCCESS,
            DagsterRunStatus.FAILURE,
        )
    ):
        time.sleep(poll_interval)
        total_time_elapsed += poll_interval
        if total_time_elapsed >= timeout:
            raise TimeoutError("Timed out waiting for asset check evaluation")

        evaluation = instance.get_latest_asset_check_evaluation_record(asset_check_key=target)

    return evaluation


def wait_for_all_runs_to_complete(
    instance: DagsterInstance, timeout: int = 60, poll_interval: int = 3
) -> None:
    runs = instance.get_runs()

    total_time_elapsed = 0
    while not all(
        run.status in (DagsterRunStatus.SUCCESS, DagsterRunStatus.FAILURE) for run in runs
    ):
        time.sleep(poll_interval)
        total_time_elapsed += poll_interval
        if total_time_elapsed >= timeout:
            raise TimeoutError("Timed out waiting for runs to complete")

        runs = instance.get_runs()
