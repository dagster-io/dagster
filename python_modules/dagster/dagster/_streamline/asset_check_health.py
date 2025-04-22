from typing import TYPE_CHECKING, Optional

from dagster_shared import record
from dagster_shared.serdes import whitelist_for_serdes

from dagster._core.definitions.asset_check_evaluation import AssetCheckEvaluation
from dagster._core.definitions.asset_check_spec import AssetCheckSeverity

if TYPE_CHECKING:
    from dagster._core.storage.asset_check_execution_record import AssetCheckExecutionResolvedStatus


@whitelist_for_serdes
@record.record
class AssetCheckHealthState:
    # maps check_key -> list of (status, severity, evaluation | None)
    # maintains the latest 5 completed evaluations for each check
    latest_evaluations: dict[
        str,
        list[
            tuple[
                "AssetCheckExecutionResolvedStatus",
                AssetCheckSeverity,
                Optional[AssetCheckEvaluation],
            ]
        ],
    ]
