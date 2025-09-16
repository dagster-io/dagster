from collections.abc import Iterable
from typing import TYPE_CHECKING, Optional

from dagster_shared import record
from dagster_shared.serdes import whitelist_for_serdes

import dagster._check as check
from dagster._core.definitions.asset_health.asset_health import AssetHealthStatus
from dagster._core.definitions.asset_health.asset_materialization_health import (
    MinimalAssetMaterializationHealthState,
)
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.freshness import FreshnessState, FreshnessStateRecord
from dagster._core.loader import LoadableBy, LoadingContext
from dagster._core.storage.event_log.base import AssetRecord

if TYPE_CHECKING:
    from dagster._core.workspace.context import BaseWorkspaceRequestContext


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
    async def compute_for_asset(
        cls, asset_key: AssetKey, loading_context: LoadingContext
    ) -> "AssetFreshnessHealthState":
        """Gets the freshness state for the asset from the DB."""
        freshness_state_record = await FreshnessStateRecord.gen(loading_context, asset_key)

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
        return [asset_freshness_health_states.get(key) for key in keys]


@whitelist_for_serdes
@record.record
class AssetHealthFreshnessMetadata:
    last_materialized_timestamp: Optional[float]


async def get_freshness_status_and_metadata(
    context: "BaseWorkspaceRequestContext", asset_key: AssetKey
) -> tuple[AssetHealthStatus, Optional["AssetHealthFreshnessMetadata"]]:
    """Gets an AssetFreshnessHealthState object for an asset, either via streamline or by computing
    it based on the state of the DB. Then converts it to a AssetHealthStatus and the metadata
    needed to power the UIs. Metadata is computed based on the state of the DB.
    """
    asset_freshness_health_state = await AssetFreshnessHealthState.gen(context, asset_key)
    if (
        asset_freshness_health_state is None
    ):  # if streamline reads are off or no streamline state exists for the asset compute it from the DB
        if context.instance.streamline_read_asset_health_required("asset-freshness-health"):
            return AssetHealthStatus.UNKNOWN, None

        if (
            not context.asset_graph.has(asset_key)
            or context.asset_graph.get(asset_key).freshness_policy is None
        ):
            return AssetHealthStatus.NOT_APPLICABLE, None
        asset_freshness_health_state = await AssetFreshnessHealthState.compute_for_asset(
            asset_key,
            context,
        )

    asset_materialization_health_state = await MinimalAssetMaterializationHealthState.gen(
        context, asset_key
    )
    if asset_materialization_health_state is None:
        asset_record = await AssetRecord.gen(context, asset_key)
        materialization_timestamp = (
            asset_record.asset_entry.last_materialization.timestamp
            if asset_record
            and asset_record.asset_entry
            and asset_record.asset_entry.last_materialization
            else None
        )
    else:
        materialization_timestamp = (
            asset_materialization_health_state.latest_materialization_timestamp
        )

    if asset_freshness_health_state.freshness_state == FreshnessState.PASS:
        return AssetHealthStatus.HEALTHY, AssetHealthFreshnessMetadata(
            last_materialized_timestamp=materialization_timestamp,
        )
    if asset_freshness_health_state.freshness_state == FreshnessState.WARN:
        return AssetHealthStatus.WARNING, AssetHealthFreshnessMetadata(
            last_materialized_timestamp=materialization_timestamp,
        )
    if asset_freshness_health_state.freshness_state == FreshnessState.FAIL:
        return AssetHealthStatus.DEGRADED, AssetHealthFreshnessMetadata(
            last_materialized_timestamp=materialization_timestamp,
        )
    elif asset_freshness_health_state.freshness_state == FreshnessState.UNKNOWN:
        return AssetHealthStatus.UNKNOWN, None
    elif asset_freshness_health_state.freshness_state == FreshnessState.NOT_APPLICABLE:
        return AssetHealthStatus.NOT_APPLICABLE, None

    else:
        check.failed(f"Unexpected freshness state: {asset_freshness_health_state.freshness_state}")
