from typing import Optional

from dagster_shared import record
from dagster_shared.serdes import whitelist_for_serdes

from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.freshness import FreshnessState
from dagster._core.loader import LoadingContext
from dagster._core.storage.event_log.base import AssetRecord
from dagster._streamline.asset_health import AssetHealthStatus


@whitelist_for_serdes
@record.record
class AssetFreshnessHealthState:
    """Maintains the latest freshness state for the asset."""

    freshness_state: FreshnessState
    last_materialization_timestamp: Optional[float] = None

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
    async def compute_for_asset(
        cls, asset_key: AssetKey, loading_context: LoadingContext
    ) -> "AssetFreshnessHealthState":
        """Using the latest terminal state for each check as stored in the DB, returns a set of
        asset checks in each terminal state. If a check is in progress, it remains in the terminal
        state it was in prior to the in progress execution.
        """
        freshness_state_record = loading_context.instance.get_entity_freshness_state(asset_key)
        asset_record = await AssetRecord.gen(loading_context, asset_key)
        last_materialization_ts = (
            asset_record.asset_entry.last_materialization.timestamp
            if asset_record and asset_record.asset_entry.last_materialization
            else None
        )
        if freshness_state_record is None:
            # asset has a freshness policy, but it has not been evaluated yet
            return cls(
                freshness_state=FreshnessState.UNKNOWN,
                last_materialization_timestamp=last_materialization_ts,
            )
        return cls(
            freshness_state=freshness_state_record.freshness_state,
            last_materialization_timestamp=last_materialization_ts,
        )
