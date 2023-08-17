import pytest
from dagster import AssetCheckResult, AssetKey
from dagster._check import CheckError
from dagster._core.definitions.asset_check_execution import (
    AssetCheckExecution,
    AssetCheckExecutionStatus,
)
from dagster._core.event_api import EventLogRecord
from dagster._core.events.log import EventLogEntry


def test_status():
    key = AssetKey("foo")

    execution = AssetCheckExecution.planned(asset_key=key, check_name="bar", run_id="baz")
    assert execution.check_status == AssetCheckExecutionStatus.PLANNED

    success_execution = execution.with_result(
        check_result=AssetCheckResult(asset_key=key, check_name="bar", success=True),
        target_materialization_record=EventLogRecord(
            storage_id=1,
            event_log_entry=EventLogEntry(
                user_message="",
                level="WARN",
                timestamp=0.0,
                step_key="",
                dagster_event=None,
                error_info=None,
                run_id="",
            ),
        ),
        start_timestamp=0,
        end_timestamp=0,
    )
    assert success_execution.check_status == AssetCheckExecutionStatus.RESULT_SUCCESS

    fail_execution = execution.with_result(
        check_result=AssetCheckResult(asset_key=key, check_name="bar", success=False),
        target_materialization_record=EventLogRecord(
            storage_id=1,
            event_log_entry=EventLogEntry(
                user_message="",
                level="WARNING",
                timestamp=0.0,
                step_key="",
                dagster_event=None,
                error_info=None,
                run_id="",
            ),
        ),
        start_timestamp=0,
        end_timestamp=0,
    )
    assert fail_execution.check_status == AssetCheckExecutionStatus.RESULT_FAILURE

    with pytest.raises(CheckError):
        AssetCheckExecution(
            asset_key=key,
            check_name="bar",
            check_status=AssetCheckExecutionStatus.RESULT_SUCCESS,
            run_id="baz",
        )
