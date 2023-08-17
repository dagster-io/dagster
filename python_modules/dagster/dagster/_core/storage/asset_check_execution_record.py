from typing import NamedTuple

from dagster._core.definitions.asset_check_execution import AssetCheckExecution


class AssetCheckExecutionRecord(NamedTuple):
    storage_id: int
    asset_check_execution: AssetCheckExecution
