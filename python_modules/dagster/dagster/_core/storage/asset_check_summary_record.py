from typing import NamedTuple, Optional

from dagster._annotations import experimental
from dagster._core.definitions.asset_check_spec import AssetCheckKey
from dagster._core.storage.asset_check_execution_record import AssetCheckExecutionRecord


@experimental
class AssetCheckSummaryRecord(NamedTuple):
    """A representation of the current state of an asset check. Contains the most recent execution record,
    and the most recent run id that the check was executed in.

    Users should not instantiate this class directly.
    """

    asset_check_key: AssetCheckKey
    last_check_execution_record: Optional[AssetCheckExecutionRecord]
    last_run_id: Optional[str]
