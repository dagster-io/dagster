import enum
from typing import TYPE_CHECKING, NamedTuple, Optional

import dagster._check as check
from dagster._serdes.serdes import whitelist_for_serdes

from .asset_check_result import AssetCheckResult
from .events import AssetKey

if TYPE_CHECKING:
    from dagster._core.event_api import EventLogRecord


@whitelist_for_serdes
class AssetCheckExecutionStatus(enum.Enum):
    PLANNED = "PLANNED"  # No result yet
    RESULT_SUCCESS = "RESULT_SUCCESS"
    RESULT_FAILURE = "RESULT_FAILURE"


@whitelist_for_serdes
class AssetCheckExecution(
    NamedTuple(
        "_AssetCheckExecution",
        [
            ("asset_key", AssetKey),
            ("check_name", str),
            ("check_status", AssetCheckExecutionStatus),
            ("run_id", str),
            ("check_result", Optional[AssetCheckResult]),
            ("target_materialization_record", Optional["EventLogRecord"]),
            ("start_timestamp", Optional[float]),
            ("end_timestamp", Optional[float]),
        ],
    )
):
    """Wrapper around AssetCheckResult that includes metadata about the execution of the check.

    Normal use is to instantiate this class with AssetCheckExecution.planned(), then call
    with_result() when the check is complete.
    """

    def __new__(
        cls,
        asset_key: AssetKey,
        check_name: str,
        check_status: AssetCheckExecutionStatus,
        run_id: str,
        check_result: Optional[AssetCheckResult] = None,
        target_materialization_record: Optional["EventLogRecord"] = None,
        start_timestamp: Optional[float] = None,
        end_timestamp: Optional[float] = None,
    ):
        if check_status == AssetCheckExecutionStatus.PLANNED:
            check.invariant(
                check_result is None, "check_result must be None when check_status is PLANNED"
            )
        else:
            check_result = check.not_none(
                check_result,
                "check_result must be provided when check_status is not PLANNED",
            )
            check.invariant(
                asset_key == check_result.asset_key,
                "asset_key and check_result.asset_key must match",
            )
            check.invariant(
                check_name == check_result.check_name,
                "check_name and check_result.check_name must match",
            )
            check.invariant(
                (
                    check_status == AssetCheckExecutionStatus.RESULT_SUCCESS
                    if check_result.success
                    else AssetCheckExecutionStatus.RESULT_FAILURE
                ),
                "check_status and check_result.success must match",
            )

        return super().__new__(
            cls,
            asset_key=asset_key,
            check_name=check_name,
            check_status=check_status,
            check_result=check_result,
            target_materialization_record=target_materialization_record,
            run_id=run_id,
            start_timestamp=start_timestamp,
            end_timestamp=end_timestamp,
        )

    @classmethod
    def planned(cls, asset_key: AssetKey, check_name: str, run_id: str):
        return cls(asset_key, check_name, AssetCheckExecutionStatus.PLANNED, run_id)

    def with_result(
        self,
        check_result: AssetCheckResult,
        start_timestamp: float,
        end_timestamp: float,
        target_materialization_record: Optional["EventLogRecord"] = None,
    ):
        return AssetCheckExecution(
            asset_key=self.asset_key,
            check_name=self.check_name,
            check_status=(
                AssetCheckExecutionStatus.RESULT_SUCCESS
                if check_result.success
                else AssetCheckExecutionStatus.RESULT_FAILURE
            ),
            run_id=self.run_id,
            check_result=check_result,
            target_materialization_record=target_materialization_record,
            start_timestamp=start_timestamp,
            end_timestamp=end_timestamp,
        )
