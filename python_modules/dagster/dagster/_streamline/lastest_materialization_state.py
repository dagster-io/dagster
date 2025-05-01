from typing import Optional

from dagster_shared import record
from dagster_shared.serdes import whitelist_for_serdes

from dagster._core.definitions.asset_key import AssetKey
from dagster._core.loader import LoadingContext
from dagster._core.storage.event_log.base import AssetRecord


@whitelist_for_serdes
@record.record
class AssetLatestMaterializationState:
    """Maintains info about the latest materialization of an asset."""

    timestamp: float
    run_id: str

    @classmethod
    async def compute_for_asset(
        cls, asset_key: AssetKey, loading_context: LoadingContext
    ) -> Optional["AssetLatestMaterializationState"]:
        """Compute the latest materialization state for an asset based on data stored in the DB."""
        asset_record = await AssetRecord.gen(loading_context, asset_key)
        if asset_record is None or asset_record.asset_entry.last_materialization is None:
            # asset has never been materialized
            return None
        return cls(
            timestamp=asset_record.asset_entry.last_materialization.timestamp,
            run_id=asset_record.asset_entry.last_materialization.run_id,
        )
