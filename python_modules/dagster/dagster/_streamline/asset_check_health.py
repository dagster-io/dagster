from dagster_shared import record
from dagster_shared.serdes import whitelist_for_serdes

from dagster._core.definitions.asset_key import AssetCheckKey


@whitelist_for_serdes
@record.record
class AssetCheckHealthState:
    """Maintains a list of asset checks for the asset in each terminal state. If a check is in progress,
    it will not move to a new list until the execution is complete.
    """

    passing_checks: set[AssetCheckKey]
    failing_checks: set[AssetCheckKey]
    warning_checks: set[AssetCheckKey]
    all_checks: set[AssetCheckKey]

    @classmethod
    def default(cls) -> "AssetCheckHealthState":
        return cls(
            passing_checks=set(),
            failing_checks=set(),
            warning_checks=set(),
            all_checks=set(),
        )
