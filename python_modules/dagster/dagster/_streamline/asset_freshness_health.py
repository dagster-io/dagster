from collections.abc import Iterable
from typing import Optional

from dagster_shared import record
from dagster_shared.serdes import whitelist_for_serdes

from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.freshness import FreshnessState
from dagster._core.loader import LoadableBy, LoadingContext
from dagster._streamline.asset_health import AssetHealthStatus


@whitelist_for_serdes
@record.record
class AssetFreshnessHealthState(LoadableBy[AssetKey]):
    """Maintains the latest freshness state for the asset."""

    freshness_state: FreshnessState

    @property
    def health_status(self) -> AssetHealthStatus:
        if self.freshness_state == FreshnessState.PASS:
            return AssetHealthStatus.HEALTHY
        elif self.freshness_state == FreshnessState.WARN:
            return AssetHealthStatus.WARNING
        elif self.freshness_state == FreshnessState.FAIL:
            return AssetHealthStatus.DEGRADED
        elif self.freshness_state == FreshnessState.NOT_APPLICABLE:
            return AssetHealthStatus.NOT_APPLICABLE
        else:
            return AssetHealthStatus.UNKNOWN

    @classmethod
    def compute_for_asset(
        cls, asset_key: AssetKey, loading_context: LoadingContext
    ) -> "AssetFreshnessHealthState":
        """Gets the freshness state for the asset from the DB."""
        freshness_state_record = loading_context.instance.get_entity_freshness_state(asset_key)

        if freshness_state_record is None:
            # freshness policy has no evaluations yet
            return cls(
                freshness_state=FreshnessState.UNKNOWN,
            )
        return cls(
            freshness_state=freshness_state_record.freshness_state,
        )

    @classmethod
    def _blocking_batch_load(
        cls, keys: Iterable[AssetKey], context: LoadingContext
    ) -> Iterable[Optional["AssetFreshnessHealthState"]]:
        asset_freshness_health_states = (
            context.instance.get_asset_freshness_health_state_for_assets(list(keys))
        )

        if asset_freshness_health_states is None:
            return [None for _ in keys]
        else:
            return [asset_freshness_health_states.get(key) for key in keys]
