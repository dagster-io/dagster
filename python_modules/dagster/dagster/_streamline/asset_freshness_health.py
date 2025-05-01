from dagster_shared import record
from dagster_shared.serdes import whitelist_for_serdes

from dagster._core.definitions.freshness import FreshnessState


@whitelist_for_serdes
@record.record
class AssetFreshnessHealthState:
    """Maintains the latest freshness state for the asset."""

    freshness_state: FreshnessState

    @classmethod
    def default(cls) -> "AssetFreshnessHealthState":
        return cls(
            freshness_state=FreshnessState.UNKNOWN,
        )
